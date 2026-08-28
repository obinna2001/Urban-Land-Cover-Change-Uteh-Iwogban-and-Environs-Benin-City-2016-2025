import rasterio
from pathlib import Path

def extract_raster_map_metadata(path: Path) -> dict:
    with rasterio.open(path) as raster_map:
        return {
            "coordinate_reference_system": raster_map.crs,
            "shape": (raster_map.height, raster_map.width),
            "resolution": raster_map.res,
            "bounds": raster_map.bounds,
            "transform": raster_map.transform,
            "nodata": raster_map.nodata
        }




