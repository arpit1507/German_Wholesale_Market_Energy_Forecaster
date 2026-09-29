# template.py
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="[%(asctime)s]: %(message)s")

project_name = "energy_forecast"

list_of_files = [
    ".github/workflows/ci.yml",
    f"src/{project_name}/__init__.py",
    f"src/{project_name}/components/__init__.py",
    f"src/{project_name}/components/data_ingestion.py",
    f"src/{project_name}/components/data_transformation.py",
    f"src/{project_name}/components/model_trainer.py",
    f"src/{project_name}/components/model_evaluation.py",
    f"src/{project_name}/pipelines/__init__.py",
    f"src/{project_name}/pipelines/training_pipeline.py",
    f"src/{project_name}/entity/__init__.py",
    f"src/{project_name}/entity/config_entity.py",
    f"src/{project_name}/constants/__init__.py",
    f"src/{project_name}/utils/__init__.py",
    f"src/{project_name}/utils/common.py",
    "config/config.yaml",
    "params.yaml",
    "tests/__init__.py",
    "tests/unit/__init__.py",
    "tests/integration/__init__.py",
    ".gitignore",
    "pyproject.toml",
    "setup.py",
    "README.md",
]

for filepath in list_of_files:
    path = Path(filepath)
    filedir, filename = path.parent, path.name

    if filedir != Path(""):
        filedir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created directory: {filedir} for file: {filename}")

    if not path.exists() or path.stat().st_size == 0:
        path.touch()
        logging.info(f"Created empty file: {path}")
    else:
        logging.info(f"File already exists: {path}")