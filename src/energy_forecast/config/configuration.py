from pathlib import Path
import yaml
from energy_forecast.entity.config_entity import DataIngestionConfig

class ConfigurationManager:
    def __init__(self, config_filepath: Path = Path("config/config.yaml")):
        with open(config_filepath, "r") as f:
            self.config = yaml.safe_load(f)

    def get_data_ingestion_config(self) -> DataIngestionConfig:
        cfg = self.config["data_ingestion"]
        return DataIngestionConfig(
            raw_data_dir=Path(cfg["raw_data_dir"]),
            output_file_name=cfg["output_file_name"],
            base_url=str(cfg["base_url"]),
            max_weeks_back=int(cfg.get("max_weeks_back", 52)),
            timeout_sec=float(cfg.get("timeout_sec", 30.0)),
            max_concurrency=int(cfg.get("max_concurrency", 8)),
        )