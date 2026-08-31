from pathlib import Path
from dataclasses import dataclass, field
from omegaconf import OmegaConf

REPO_ROOT = Path(__file__).resolve().parents[1]

@dataclass(slots=True, kw_only=True)
class Rawdataset:
    """Configuration class for raw/unprocessed dataset"""
    aoi_geojson: str = field(
        metadata={
            "description": "File path to .geojson file containing the geometry of the selected area of interest"
        }
    )
    aoi_lulc: str = field(
        metadata={
            "descriptiopn": "File path to the folder containing Google Earth Engine Dynamic World .geotif file of the area of interest"
        }
    )
    base_data: str = field(
        metadata={
            "descriptiopn": "File path to shapefile of the 8,809 wards in Nigeria from Grid3"
        }
    )

@dataclass(slots=True, kw_only=True)
class Processeddataset:
    """Configuration class for processed dataset"""
    aoi_shapefile: str = field(
         metadata={
            "descriptiopn": "File path to shapefile of the area of interest"
        }
    )

@dataclass(slots=True, kw_only=True)
class Dataset:
    "Configuration class for all datasets"
    raw_dataset: Rawdataset = field(
        metadata={
            "descriptiopn": "File path to all raw datasets in this repository"
        }
    )
    processed_dataset: Processeddataset = field(
        metadata={
            "descriptiopn": "File path to all preprocessed datasets in this repository"
        }
    )

@dataclass(slots=True, kw_only=True)
class AppConfig:
    """Configuration for the Application"""
    name: str = field(metadata={"description": "The name of the App."})
    description: str = field(metadata={"description": "The description of the App."})

@dataclass(slots=True, kw_only=True)
class DynamicWorldClass:
    """Name and display colour for a Dynamic World class."""

    name: str = field(
        metadata={
            "description": "The human-readable Dynamic World class name"
        }
    )
    colour: str = field(
        metadata={
            "description": "The hexadecimal display colour for the class"
        }
    )


@dataclass(slots=True, kw_only=True)
class DynamicWorldConfig:
    """Configuration for the Dynamic World class registry."""

    classes: dict[int, DynamicWorldClass] = field(
        metadata={
            "description": (
                "Dynamic World class definitions keyed by raster class value"
            )
        }
    )


@dataclass(slots=True, kw_only=True)
class Config:
    """Top level Configuration class of the application"""
    app_config: AppConfig = field(metadata={"description": "The app configuration"})
    dynamic_world: DynamicWorldConfig = field(
        metadata={"description": "The Dynamic World configuration"}
    )
    dataset: Dataset = field(metadata={"description": "The configuration for the application dataset"})


# Create a schema to help OmegaConf automatically perform validation during loading
schema = OmegaConf.structured(Config)

# Instantiate config.yaml path
config_path: Path = REPO_ROOT / "config/config.yaml"

# Populate repo_root in config file
OmegaConf.register_new_resolver(
    "repo_root",
    lambda: str(REPO_ROOT),
    replace=True,
)

# Read and validate config.yaml dataset
config = OmegaConf.merge(schema, OmegaConf.load(config_path).config)

# Convert config datatype to compatible python counterpart. This ensures seamless integration with other part of 
# the repo allowing for value integration with other python libraries
resolved_config: Config = OmegaConf.to_object(config) # type: ignore