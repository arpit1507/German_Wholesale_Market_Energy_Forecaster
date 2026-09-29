import yaml
from pathlib import Path

def read_yaml(path_to_yaml: Path) -> dict:
    with open(path_to_yaml) as yaml_file:
        return yaml.safe_load(yaml_file)