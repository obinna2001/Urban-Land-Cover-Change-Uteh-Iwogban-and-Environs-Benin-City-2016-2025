import re
from pathlib import Path

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


def extract_year(path: str | Path) -> int:
    """Extract a single four-digit year from a file name.

    The function identifies a year between 1900 and 2099. The year must not
    be immediately preceded or followed by another digit. Only the file name
    is searched; years appearing in parent directory names are ignored.

    Parameters
    ----------
    path : str or pathlib.Path
        File path or file name containing the year to extract.

    Returns
    -------
    int
        Four-digit year extracted from the file name.

    Raises
    ------
    TypeError
        If ``path`` is neither a string nor a ``Path`` object.
    ValueError
        If the file name contains no valid year or contains more than one
        valid year.

    """
    if not isinstance(path, (str, Path)):
        raise TypeError("path must be a str or Path object")

    year_pattern = r"(?<!\d)(?:19|20)\d{2}(?!\d)"
    file_name = Path(path).name
    year_matches = re.findall(year_pattern, file_name)

    if not year_matches:
        raise ValueError(
            f"No valid year was found in file name {file_name!r}"
        )

    if len(year_matches) > 1:
        raise ValueError(
            f"Multiple valid years were found in file name {file_name!r}"
        )

    return int(year_matches[0])

    