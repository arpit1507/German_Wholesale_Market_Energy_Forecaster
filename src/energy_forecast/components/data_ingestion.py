import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx
import polars as pl
from tqdm.asyncio import tqdm_asyncio

from energy_forecast.config.configuration import ConfigurationManager
from energy_forecast.entity.config_entity import DataIngestionConfig, SmardSeriesConfig

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class DataIngestion:
    def __init__(self, config: DataIngestionConfig):
        self.config = config
        self.config.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.semaphore = asyncio.Semaphore(self.config.max_concurrency)

    async def _fetch_json_with_retry(
        self, client: httpx.AsyncClient, url: str, retries: int = 3, backoff: float = 1.5
    ) -> Optional[Dict[str, Any]]:
        for attempt in range(1, retries + 1):
            try:
                async with self.semaphore:
                    resp = await client.get(url, timeout=self.config.timeout_sec)
                    if resp.status_code == 200:
                        return resp.json()
                    elif resp.status_code == 404:
                        logger.warning(f"Resource not found (404): {url}")
                        return None
                    else:
                        logger.warning(f"HTTP {resp.status_code} for {url}. Attempt {attempt}/{retries}")
            except (httpx.RequestError, httpx.TimeoutException) as exc:
                if attempt == retries:
                    logger.error(f"Failed to fetch {url} after {retries} attempts: {exc}")
                    return None
                await asyncio.sleep(backoff * attempt)
        return None

    async def _fetch_series_timestamps(
        self, client: httpx.AsyncClient, series: SmardSeriesConfig
    ) -> List[int]:
        index_url = f"{self.config.base_url}/{series.filter_id}/{series.region}/index_{series.resolution}.json"
        data = await self._fetch_json_with_retry(client, index_url)
        if not data or "timestamps" not in data:
            raise ValueError(f"Could not retrieve timestamp index for filter {series.filter_id} from {index_url}")

        timestamps: List[int] = data["timestamps"]
        # Slice to the configured lookback window (e.g., 52 weeks)
        return timestamps[-self.config.max_weeks_back:]

    async def _fetch_single_chunk(
        self, client: httpx.AsyncClient, series: SmardSeriesConfig, timestamp: int
    ) -> List[Dict[str, Any]]:
        chunk_url = (
            f"{self.config.base_url}/{series.filter_id}/{series.region}/"
            f"{series.filter_id}_{series.region}_{series.resolution}_{timestamp}.json"
        )
        payload = await self._fetch_json_with_retry(client, chunk_url)
        if not payload or "series" not in payload:
            return []

        # Return list of valid hourly readings
        return [
            {"timestamp_ms": item[0], series.column_name: item[1]}
            for item in payload["series"]
            if item[0] is not None
        ]

    async def fetch_series_dataframe(
        self, client: httpx.AsyncClient, series: SmardSeriesConfig
    ) -> pl.DataFrame:
        logger.info(f"Extracting series: '{series.column_name}' (Filter ID: {series.filter_id})...")
        target_timestamps = await self._fetch_series_timestamps(client, series)

        tasks = [self._fetch_single_chunk(client, series, ts) for ts in target_timestamps]
        chunk_results = await tqdm_asyncio.gather(*tasks, desc=f"Ingesting {series.column_name}")

        flat_records = [record for chunk in chunk_results for record in chunk]
        if not flat_records:
            raise RuntimeError(f"Zero records extracted for {series.column_name}")

        return (
            pl.DataFrame(flat_records)
            .with_columns(
                pl.from_epoch("timestamp_ms", time_unit="ms").dt.replace_time_zone("UTC").alias("timestamp_utc"),
                pl.col(series.column_name).cast(pl.Float64),
            )
            .drop("timestamp_ms")
            .sort("timestamp_utc")
            .unique(subset=["timestamp_utc"])
        )

    async def initiate_data_ingestion(self) -> pl.DataFrame:
        limits = httpx.Limits(max_keepalive_connections=15, max_connections=25)
        headers = {"User-Agent": "Mozilla/5.0 (EnergyDataPipeline/1.0; SMARD-Client)"}

        async with httpx.AsyncClient(limits=limits, headers=headers) as client:
            series_dfs: List[pl.DataFrame] = []
            for series in self.config.series_registry:
                df = await self.fetch_series_dataframe(client, series)
                series_dfs.append(df)

            logger.info("Merging series into an aligned UTC time series...")
            final_df = series_dfs[0]
            for df in series_dfs[1:]:
                final_df = final_df.join(df, on="timestamp_utc", how="inner")

            output_path = self.config.output_filepath
            final_df.write_parquet(output_path, compression="zstd")
            logger.info(f"Successfully ingested {final_df.shape[0]} rows and {final_df.shape[1]} columns.")
            logger.info(f"Parquet artifact written to: {output_path.resolve()}")

            return final_df


if __name__ == "__main__":
    config_manager = ConfigurationManager()
    ingestion_config = config_manager.get_data_ingestion_config()
    ingestion = DataIngestion(config=ingestion_config)
    asyncio.run(ingestion.initiate_data_ingestion())