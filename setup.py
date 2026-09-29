# setup.py
from setuptools import setup, find_packages
from pathlib import Path

def get_requirements() -> list[str]:
    requirements_path = Path("requirements.txt")
    if requirements_path.exists():
        with open(requirements_path) as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("-e")]
    return []

setup(
    name="energy_forecast",
    version="0.1.0",
    author="Arpit Agrawal",
    description="End-to-End Wholesale Day-Ahead Spot Price & Negative Spike Forecaster for Germany (SMARD)",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=get_requirements(),
    python_requires=">=3.10",
)