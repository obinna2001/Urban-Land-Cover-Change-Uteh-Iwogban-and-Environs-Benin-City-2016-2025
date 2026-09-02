import numpy as np
from pathlib import Path
from typing import Sequence

import rasterio
import pandas as pd
from rasterio import errors
from rasterio.errors import RasterioIOError

def count_land_cover_classes(
    raster_path: str | Path,
) -> dict[int, int]:
    """Count the number of pixels belonging to each land-cover class.

    Parameters
    ----------
    raster_path : str or pathlib.Path
        Path to the LULC raster file.

    Returns
    -------
    dict[int, int]
        Mapping of land-cover class values to their corresponding
        pixel counts.

    Raises
    ------
    TypeError 
        If ``raster_path`` is neither a string nor a ``Path`` object. 
    FileNotFoundError 
        If the specified raster file does not exist. 
    ValueError 
        If the raster contains more or fewer than one band, or contains no 
        valid land-cover pixels after masked values are excluded. 
    RasterioIOError 
        If the raster file exists but cannot be opened or read by Rasterio.
    """
    if not isinstance(raster_path, (str, Path)):
        raise TypeError(f"{raster_path!r} must be either str or Path")

    if isinstance(raster_path, str):
        raster_path = Path(raster_path)

    if not raster_path.is_file():
        raise FileNotFoundError(f"File not found in {raster_path!r}")

    try:
        with rasterio.open(raster_path) as geotiff_file:
            if geotiff_file.count != 1:
                raise ValueError(
                    f"{raster_path.name!r} must contain exactly one raster band"
                )
            
            data = geotiff_file.read(1, masked=True)

            if data.count() == 0:
                raise ValueError(
                    f"{raster_path.name!r} contains no valid land-cover pixels"
                )

            class_values, class_counts = np.unique(
                data.compressed(),
                return_counts=True,
            )

            return {
                int(class_value): int(class_count)
                for class_value, class_count in zip(
                    class_values,
                    class_counts,
                    strict=True,
                )
            }

    except errors.RasterioIOError as exc:
        raise RasterioIOError(
            f"Unable to read raster file {raster_path.name!r}"
        ) from exc


def build_class_count_table(
    raster_paths: Sequence[str | Path],
) -> pd.DataFrame:
    """Build a table of land-cover class pixel counts for multiple rasters.

    Parameters
    ----------
    raster_paths : Sequence[str or pathlib.Path]
        Sequence of paths to LULC raster files. Raster filenames must be
        unique within the sequence.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing land-cover class values and their corresponding
        pixel counts for each raster. Missing class counts are filled with
        zero and converted to ``int64``.

    Raises
    ------
    TypeError
        If ``raster_paths`` is provided as a single string or ``Path`` object,
        or if any item in the sequence is neither a string nor a ``Path``.
    ValueError
        If ``raster_paths`` is empty, contains duplicate raster filenames,
        or if any raster contains more or fewer than one band or contains
        no valid land-cover pixels.
    FileNotFoundError
        If any specified raster file does not exist.
    rasterio.errors.RasterioIOError
        If any raster file exists but cannot be opened or read by Rasterio.

    """
<<<<<<< HEAD
    if not raster_paths:
        raise ValueError(f"{raster_paths!r} cannot be empty.")

=======
>>>>>>> 446a6a7 (refactor: create custom functions for resuseable logic in 02_inspect_dynamic_world.ipynb)
    if isinstance(raster_paths, (str, Path)):
        raise TypeError(
            "raster_paths must be a sequence of paths, not a single path"
        )

<<<<<<< HEAD
=======
    if not raster_paths:
        raise ValueError(f"{raster_paths!r} cannot be empty.")

>>>>>>> 446a6a7 (refactor: create custom functions for resuseable logic in 02_inspect_dynamic_world.ipynb)
    if not all(isinstance(item, (str, Path)) for item in raster_paths):
        raise TypeError(
            f"Values in {raster_paths!r} must be either str or Path."
        )

    normalised_paths = [
        Path(raster_path)
        for raster_path in raster_paths
    ]

    filenames = [path.name for path in normalised_paths]

    if len(filenames) != len(set(filenames)):
        raise ValueError(
            f"Raster file names must be unique."
        )

    land_cover_classes_count_results = {
        raster_path.name: count_land_cover_classes(raster_path)
        for raster_path in normalised_paths
    }

    land_cover_classes_count_table = (
        pd.DataFrame(land_cover_classes_count_results)
        .fillna(0)
        .astype("int64")
        .sort_index()
    )

    # name index
    land_cover_classes_count_table.index.name = "class_value"

    # convert index to a column
    land_cover_classes_count_table = land_cover_classes_count_table.reset_index()

<<<<<<< HEAD
    return land_cover_classes_count_table
=======
    return land_cover_classes_count_table
>>>>>>> 446a6a7 (refactor: create custom functions for resuseable logic in 02_inspect_dynamic_world.ipynb)
