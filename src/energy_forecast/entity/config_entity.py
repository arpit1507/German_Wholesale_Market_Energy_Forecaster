from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple

@dataclass(frozen=True)
class SmardSeriesConfig:
    filter_id: int
    column_name: str
    region: str = "DE"
    resolution: str = "hour"

@dataclass(frozen=True)
class DataIngestionConfig:
    raw_data_dir: Path
    output_file_name: str
    base_url: str
    max_weeks_back: int = 52
    timeout_sec: float = 30.0
    max_concurrency: int = 8
    series_registry: Tuple[SmardSeriesConfig, ...] = field(
        default_factory=lambda: (
            SmardSeriesConfig(filter_id=4169, column_name="day_ahead_price_eur_mwh", region="DE"),
            SmardSeriesConfig(filter_id=410,  column_name="total_grid_load_mwh",     region="DE"),
            SmardSeriesConfig(filter_id=4068, column_name="solar_generation_mwh",    region="DE"),
            SmardSeriesConfig(filter_id=4067, column_name="wind_onshore_mwh",        region="DE"),
            SmardSeriesConfig(filter_id=1225, column_name="wind_offshore_mwh",       region="DE"),
            SmardSeriesConfig(filter_id=4359, column_name="residual_load_actual_mwh",region="DE"),
        )
    )

    @property
    def output_filepath(self) -> Path:
        return self.raw_data_dir / self.output_file_name