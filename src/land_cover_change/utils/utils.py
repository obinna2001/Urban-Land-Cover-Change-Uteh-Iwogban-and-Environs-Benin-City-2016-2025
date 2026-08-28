import rasterio
from pathlib import Path
from rasterio.crs import CRS
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling

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



def prepare_land_cover_raster(raster_path: Path):
    with rasterio.open(raster_path) as raster_data:
        if raster_data.crs is None:
            raise ValueError(f"{raster_path.stem} does not have a defined coordinate reference system")

        if raster_data.nodata is None:
            raise ValueError(f"{raster_path.stem} must have a NoData value before area analysis.")

        class_values = set(range(9))  # Dynamic world classes 0-8
        if raster_data.nodata in class_values:
            raise ValueError(
                f"{raster_path.stem} NoData value conflicts with a valid Dynamic World Class."
            )

        if raster_data.crs.is_projected:
            land_cover_array = raster_data.read(1, masked=True)
            resolution = raster_data.res
            transform = raster_data.transform

        # if raster_data is not projected, that is geographic, convert to projected coordinate system
        else:
            # define the target projected CRS considering AOI (Benin city) is in WGS 84/ UTM Zone 31N (EPSG:32631)
            target_crs = CRS.from_epsg(32631)

            with WarpedVRT(
                raster_data, 
                crs=target_crs,
                rasampling=Resampling.nearest
            ) as projected_raster:
                land_cover_array = projected_raster.read(1, masked=True)
                resolution = projected_raster.res
                transform = projected_raster.transform

        return {
            "data": land_cover_array,
            "resolution": resolution,
            "transform": transform
        }   
