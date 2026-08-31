import rasterio
from pathlib import Path
from rasterio import errors
from rasterio.errors import RasterioIOError



def discover_lulc_rasters(directory_path: Path | str) -> list[Path]:
    """Discover LULC raster files in a directory.

    Parameters
    ----------
    directory_path : pathlib.Path or str
        Path to the directory containing LULC raster files.

    Returns
    -------
    list[pathlib.Path]
        Sorted list of paths to discovered ``.tif`` and ``.tiff`` raster files.

    Raises
    ------
    TypeError
        If ``directory_path`` is neither a string nor a ``Path`` object.
    FileNotFoundError
        If the input path does not exist or no raster files are found in the directory.
    NotADirectoryError
        If the input path points to a file instead of a directory.

    """
    if not isinstance(directory_path, (str, Path)):
        raise TypeError(f"{directory_path!r} must be either str or Path")

    if isinstance(directory_path, str):
        directory_path = Path(directory_path)

    if not directory_path.exists():
        raise FileNotFoundError(f"Input path {directory_path!r} does not exist")

    if not directory_path.is_dir():
        raise NotADirectoryError(
            f"Input path {directory_path!r} is a file, not a directory. "
            "Input a valid directory path"
        )

    lulc_rasters_path = [
        raster_path
        for raster_path in [
            *directory_path.glob("*.tif", case_sensitive=False),
            *directory_path.glob("*.tiff", case_sensitive=False),
        ]
        if raster_path.is_file() and raster_path.suffix.lower() in {".tif", ".tiff"}
    ]

    if len(lulc_rasters_path) == 0:
        raise FileNotFoundError(
            f"No raster file found in {directory_path!r}"
        )

    lulc_rasters_path.sort()
    return lulc_rasters_path


def extract_raster_map_metadata(
    raster_path: str | Path,
) -> dict[str, object]:
    """Extract metadata from a raster map.

    Parameters
    ----------
    raster_path : str or pathlib.Path
        Path to the raster file.

    Returns
    -------
    dict[str, object]
        Dictionary containing raster metadata, including the coordinate
        reference system, shape, resolution, bounds, band count, data types,
        affine transform, and NoData value.

    Raises
    ------
    TypeError
        If ``raster_path`` is neither a string nor a ``Path`` object.
    FileNotFoundError
        If the specified raster file does not exist.
    ValueError
        If the raster does not have a coordinate reference system.

    """
    if not isinstance(raster_path, (str, Path)):
        raise TypeError(f"{raster_path!r} must be either str or Path")

    if isinstance(raster_path, str):
        raster_path = Path(raster_path)

    if not raster_path.is_file():
        raise FileNotFoundError(f"File not found in {raster_path!r}")

    try:
        with rasterio.open(raster_path) as raster_map:
            if not raster_map.crs:
                raise ValueError(
                    f"{raster_path.name!r} has no coordinate reference system"
                )

            return {
                "coordinate_reference_system": raster_map.crs,
                "shape": (raster_map.height, raster_map.width),
                "resolution": raster_map.res,
                "bounds": raster_map.bounds,
                "band_count": raster_map.count,
                "data_types": raster_map.dtypes,
                "transform": raster_map.transform,
                "nodata": raster_map.nodata,
            }
    except errors.RasterioIOError as exc:
        raise RasterioIOError(f"Unable to read raster file {raster_path.name!r}") from exc