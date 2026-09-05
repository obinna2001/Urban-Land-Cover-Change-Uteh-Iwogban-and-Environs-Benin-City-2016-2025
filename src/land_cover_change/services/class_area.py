import numpy as np
from pathlib import Path
from collections.abc import Collection, Sequence

import rasterio
import pandas as pd
from rasterio import errors
from rasterio.errors import RasterioIOError

from .raster import (
    calculate_pixel_area,
    prepare_analysis_raster,
    validate_raster_alignment,
)
from ..utils.utils import extract_year


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
    if isinstance(raster_paths, (str, Path)):
        raise TypeError(
            "raster_paths must be a sequence of paths, not a single path"
        )

    if not raster_paths:
        raise ValueError(f"{raster_paths!r} cannot be empty.")

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

    return land_cover_classes_count_table


def calculate_class_areas(
    raster_path: str | Path,
    classes: Collection[int],
    projected_crs: int = 32631,
) -> pd.DataFrame:
    """Calculate land-cover area and percentage for one raster.

    A temporary analysis copy of the raster is reprojected to a metric
    coordinate reference system using nearest-neighbour resampling. This
    preserves categorical class values while allowing pixel area to be
    calculated in square metres.

    Parameters
    ----------
    raster_path : str or pathlib.Path
        Path to a single-band categorical land-cover raster. Its file name
        must contain exactly one year between 1900 and 2099.
    classes : collections.abc.Collection[int]
        Supported land-cover class values. The returned table contains one
        row for every supplied class, including classes with no pixels.
    projected_crs : int, default 32631
        EPSG code for a projected CRS whose linear unit is the metre. The
        default is WGS 84 / UTM zone 31N, appropriate for the current Benin
        City study area.

    Returns
    -------
    pandas.DataFrame
        Table sorted by ``class_value`` with the columns ``year``,
        ``class_value``, ``pixel_count``, ``area_km2``, and
        ``class_percentage``.

    Raises
    ------
    TypeError
        If ``raster_path`` is not a string or ``Path``; ``classes`` is not a
        non-string collection of integers; or ``projected_crs`` is not an
        integer.
    FileNotFoundError
        If ``raster_path`` does not identify an existing file.
    ValueError
        If ``classes`` is empty or contains duplicates; ``projected_crs`` is
        invalid, geographic, or not metre-based; the file name does not
        contain exactly one year; the raster has no CRS, does not contain
        exactly one band, has a NoData value that conflicts with a configured
        class, contains no valid pixels, or contains unsupported class values.
    rasterio.errors.RasterioIOError
        If the file exists but Rasterio cannot open, reproject, or read it.

    """
    if not isinstance(raster_path, (str, Path)):
        raise TypeError("raster_path must be a string or Path object")

    if (
        isinstance(classes, (str, bytes))
        or not isinstance(classes, Collection)
    ):
        raise TypeError(
            "classes must be a non-string collection of integer class values"
        )

    if not classes:
        raise ValueError("classes cannot be empty")

    if not all(
        not isinstance(class_value, (bool, np.bool_))
        and isinstance(class_value, (int, np.integer))
        for class_value in classes
    ):
        raise TypeError("classes must contain only integer class values")

    normalised_classes = [int(class_value) for class_value in classes]

    if len(normalised_classes) != len(set(normalised_classes)):
        raise ValueError("classes must not contain duplicate class values")

    raster_path = Path(raster_path)
    supported_classes = set(normalised_classes)
    analysis_raster = prepare_analysis_raster(
        raster_path,
        projected_crs,
    )
    year = extract_year(raster_path)

    if (
        analysis_raster.nodata is not None
        and analysis_raster.nodata in supported_classes
    ):
        raise ValueError(
            f"{raster_path.name!r} has a NoData value that conflicts "
            "with a configured land-cover class"
        )

    valid_pixels = analysis_raster.data.compressed()
    observed_classes = set(
        np.unique(valid_pixels).tolist()
    )
    unsupported_classes = observed_classes.difference(
        supported_classes
    )

    if unsupported_classes:
        formatted_classes = ", ".join(
            repr(class_value)
            for class_value in sorted(
                unsupported_classes,
                key=repr,
            )
        )
        raise ValueError(
            f"{raster_path.name!r} contains unsupported "
            f"land-cover classes: {formatted_classes}"
        )

    class_values, pixel_counts = np.unique(
        valid_pixels,
        return_counts=True,
    )
    counts_by_class = {
        int(class_value): int(pixel_count)
        for class_value, pixel_count in zip(
            class_values,
            pixel_counts,
            strict=True,
        )
    }
    pixel_area_m2 = calculate_pixel_area(
        analysis_raster.transform
    )

    sorted_classes = sorted(normalised_classes)
    configured_pixel_counts = [
        counts_by_class.get(class_value, 0)
        for class_value in sorted_classes
    ]
    total_valid_pixels = sum(configured_pixel_counts)

    return pd.DataFrame(
        {
            "year": [year] * len(sorted_classes),
            "class_value": sorted_classes,
            "pixel_count": configured_pixel_counts,
            "area_km2": [
                pixel_count * pixel_area_m2 / 1_000_000
                for pixel_count in configured_pixel_counts
            ],
            "class_percentage": [
                pixel_count / total_valid_pixels * 100
                for pixel_count in configured_pixel_counts
            ],
        }
    )


def build_class_area_table(
    raster_paths: Sequence[str | Path],
    classes: Collection[int],
    projected_crs: int = 32631,
) -> pd.DataFrame:
    """Combine class-area results from one or more annual rasters.

    When multiple rasters are supplied, their source grids are validated
    before any area calculations are performed. Each raster is then processed
    with the same class registry and projected analysis CRS.

    Parameters
    ----------
    raster_paths : collections.abc.Sequence[str or pathlib.Path]
        Paths to one or more annual categorical land-cover rasters. Each file
        name must contain exactly one year, and each year must be unique.
    classes : collections.abc.Collection[int]
        Supported land-cover class values. Every year contains one output row
        for each supplied class, including classes with no pixels.
    projected_crs : int, default 32631
        EPSG code for the metre-based projected CRS used for area analysis.

    Returns
    -------
    pandas.DataFrame
        Long-form table sorted by ``year`` and ``class_value``, containing the
        columns ``year``, ``class_value``, ``pixel_count``, ``area_km2``, and
        ``class_percentage``.

    Raises
    ------
    TypeError
        If ``raster_paths`` is not a non-string sequence or contains values
        other than strings and ``Path`` objects. Input validation errors from
        ``calculate_class_areas`` are also propagated.
    FileNotFoundError
        If any supplied raster path does not identify an existing file.
    ValueError
        If ``raster_paths`` is empty, two files represent the same year, the
        raster grids are not aligned, or a raster cannot be used for class-area
        analysis.
    rasterio.errors.RasterioIOError
        If Rasterio cannot open, reproject, or read a raster.

    """
    if (
        isinstance(raster_paths, (str, Path))
        or not isinstance(raster_paths, Sequence)
    ):
        raise TypeError(
            "raster_paths must be a non-string sequence of file paths"
        )

    if not raster_paths:
        raise ValueError("raster_paths cannot be empty")

    if not all(
        isinstance(raster_path, (str, Path))
        for raster_path in raster_paths
    ):
        raise TypeError(
            "raster_paths must contain only str or Path objects"
        )

    normalised_paths = [
        Path(raster_path)
        for raster_path in raster_paths
    ]

    missing_paths = [
        raster_path
        for raster_path in normalised_paths
        if not raster_path.exists()
    ]

    if missing_paths:
        formatted_paths = ", ".join(map(str, missing_paths))
        raise FileNotFoundError(
            f"Raster paths do not exist: {formatted_paths}"
        )

    non_file_paths = [
        raster_path
        for raster_path in normalised_paths
        if not raster_path.is_file()
    ]

    if non_file_paths:
        formatted_paths = ", ".join(map(str, non_file_paths))
        raise ValueError(
            f"Raster paths are not files: {formatted_paths}"
        )

    years = [extract_year(raster_path) for raster_path in normalised_paths]
    duplicate_years = sorted({
        year
        for year in years
        if years.count(year) > 1
    })

    if duplicate_years:
        formatted_years = ", ".join(map(str, duplicate_years))
        raise ValueError(
            f"Raster years must be unique; duplicates found: "
            f"{formatted_years}"
        )

    if len(normalised_paths) > 1:
        validate_raster_alignment(normalised_paths)

    annual_tables = [
        calculate_class_areas(
            raster_path,
            classes,
            projected_crs,
        )
        for raster_path in normalised_paths
    ]

    return (
        pd.concat(annual_tables, ignore_index=True)
        .sort_values(["year", "class_value"], ignore_index=True)
    )


def build_area_comparison(table: pd.DataFrame) -> pd.DataFrame:
    """Pivot annual class-area results into a class-by-year comparison.

    Parameters
    ----------
    table : pandas.DataFrame
        Long-form class-area table containing ``year``, ``class_value``,
        ``area_km2``, and ``class_percentage`` columns.

    Returns
    -------
    pandas.DataFrame
        Comparison table indexed by ``class_value``. Its columns have two
        levels named ``measurement`` and ``year`` for the ``area_km2`` and
        ``class_percentage`` measurements. Missing class/year combinations
        are represented by zero.

    Raises
    ------
    TypeError
        If ``table`` is not a DataFrame or a required column is not numeric.
    ValueError
        If ``table`` is empty; column names are duplicated; required columns
        are absent; required values are missing, non-finite, or negative;
        years or class values are not whole numbers; percentages are outside
        0 through 100; or duplicate year/class combinations are present.

    """
    if not isinstance(table, pd.DataFrame):
        raise TypeError("table must be a pandas DataFrame")

    if table.empty:
        raise ValueError("table cannot be empty")

    if not table.columns.is_unique:
        duplicate_columns = (
            table.columns[table.columns.duplicated()]
            .unique()
            .tolist()
        )
        formatted_columns = ", ".join(
            repr(column)
            for column in duplicate_columns
        )
        raise ValueError(
            f"table contains duplicate column names: {formatted_columns}"
        )

    required_columns: list[str] = [
        "year",
        "class_value",
        "area_km2",
        "class_percentage",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in table.columns
    ]

    if missing_columns:
        formatted_columns = ", ".join(
            repr(column)
            for column in missing_columns
        )
        raise ValueError(
            f"table is missing required columns: {formatted_columns}"
        )

    comparison_data: pd.DataFrame = table.loc[
        :,
        required_columns,
    ].copy()

    columns_with_missing_values = [
        column
        for column in required_columns
        if comparison_data[column].isna().any()
    ]

    if columns_with_missing_values:
        formatted_columns = ", ".join(
            repr(column)
            for column in columns_with_missing_values
        )
        raise ValueError(
            f"table contains missing values in columns: {formatted_columns}"
        )

    non_numeric_columns = [
        column
        for column in required_columns
        if (
            pd.api.types.is_bool_dtype(comparison_data[column])
            or not pd.api.types.is_numeric_dtype(comparison_data[column])
        )
    ]

    if non_numeric_columns:
        formatted_columns = ", ".join(
            repr(column)
            for column in non_numeric_columns
        )
        raise TypeError(
            f"table columns must be numeric: {formatted_columns}"
        )

    numeric_values = comparison_data.loc[
        :,
        required_columns,
    ].to_numpy(dtype=float)

    if not np.isfinite(numeric_values).all():
        raise ValueError("table contains infinite or NaN values")

    if (numeric_values < 0).any():
        raise ValueError("table values cannot be negative")

    for column in ("year", "class_value"):
        values = comparison_data[column].to_numpy(dtype=float)

        if not np.equal(values, np.floor(values)).all():
            raise ValueError(
                f"{column} values must be whole numbers"
            )

        comparison_data[column] = comparison_data[column].astype(
            "int64"
        )

    if not comparison_data["class_percentage"].between(0, 100).all():
        raise ValueError(
            "class_percentage values must be between 0 and 100"
        )

    duplicate_rows = comparison_data.duplicated(
        subset=["year", "class_value"],
        keep=False,
    )

    if duplicate_rows.any():
        duplicate_pairs: pd.DataFrame = (
            comparison_data.loc[
                duplicate_rows,
                ["year", "class_value"],
            ]
            .drop_duplicates()
            .sort_values(by=["year", "class_value"])
        )

        formatted_pairs = ", ".join(
            f"({row.year}, {row.class_value})"
            for row in duplicate_pairs.itertuples(index=False)
        )

        raise ValueError(
            "table contains duplicate (year, class_value) combinations: "
            f"{formatted_pairs}"
        )

    comparison: pd.DataFrame = comparison_data.pivot(
        index="class_value",
        columns="year",
        values=["area_km2", "class_percentage"],
    )

    return (
        comparison
        .fillna(0.0)
        .sort_index()
        .sort_index(axis="columns", level=[0, 1])
        .rename_axis(
            index="class_value",
            columns=["measurement", "year"],
        )
    )


def calculate_percentage_changes(
    table: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate relative class-area changes between observation years.

    Changes are calculated between each consecutive pair of years. When more
    than two years are available, an additional first-to-last comparison is
    included. A class whose earlier area is zero receives ``NaN`` because its
    relative percentage change is undefined.

    Parameters
    ----------
    table : pandas.DataFrame
        Area-comparison table returned by ``build_area_comparison``. Columns
        must be a two-level MultiIndex whose first level contains
        ``area_km2`` and whose second level contains observation years.

    Returns
    -------
    pandas.DataFrame
        Relative percentage changes indexed like ``table``. Columns are
        chronological period labels such as ``"2016–2020"`` and have the
        axis name ``"period"``.

    Raises
    ------
    TypeError
        If ``table`` is not a DataFrame, year labels are not numeric, or area
        columns are not numeric.
    ValueError
        If ``table`` is empty; does not have unique two-level MultiIndex
        columns; does not contain ``area_km2``; contains fewer than two unique
        years; does not have a one-level, unique class index; has missing class
        values; has non-whole or non-finite years; or contains missing,
        non-finite, or negative areas.

    """
    if not isinstance(table, pd.DataFrame):
        raise TypeError("table must be a pandas DataFrame")

    if table.empty:
        raise ValueError("table cannot be empty")

    if (
        not isinstance(table.columns, pd.MultiIndex)
        or table.columns.nlevels != 2
    ):
        raise ValueError(
            "table columns must be a two-level MultiIndex"
        )

    if not table.columns.is_unique:
        raise ValueError("table columns must be unique")

    if "area_km2" not in table.columns.get_level_values(0):
        raise ValueError(
            "table must contain the 'area_km2' measurement"
        )

    if table.index.nlevels != 1:
        raise ValueError(
            "table class index must contain exactly one level"
        )

    if not table.index.is_unique:
        raise ValueError("table class index must be unique")

    if table.index.hasnans:
        raise ValueError(
            "table class index cannot contain missing values"
        )

    area_column_mask = (
        table.columns.get_level_values(0) == "area_km2"
    )

    area_by_year: pd.DataFrame = table.loc[
        :,
        area_column_mask,
    ].copy()

    # Remove the outer "area_km2" column level, leaving only years.
    area_by_year.columns = area_by_year.columns.get_level_values(1)

    if area_by_year.shape[1] < 2:
        raise ValueError(
            "table must contain at least two observation years"
        )

    non_numeric_area_columns = [
        year
        for year in area_by_year.columns
        if (
            pd.api.types.is_bool_dtype(area_by_year[year])
            or not pd.api.types.is_numeric_dtype(
                area_by_year[year]
            )
        )
    ]

    if non_numeric_area_columns:
        formatted_years = ", ".join(
            repr(year)
            for year in non_numeric_area_columns
        )
        raise TypeError(
            f"area columns must be numeric for years: "
            f"{formatted_years}"
        )

    invalid_year_types = [
        year
        for year in area_by_year.columns
        if (
            isinstance(year, (bool, np.bool_))
            or not isinstance(
                year,
                (int, float, np.integer, np.floating),
            )
        )
    ]

    if invalid_year_types:
        formatted_years = ", ".join(
            repr(year)
            for year in invalid_year_types
        )
        raise TypeError(
            f"year labels must be numeric: {formatted_years}"
        )

    numeric_years = np.asarray(
        area_by_year.columns,
        dtype=float,
    )

    if not np.isfinite(numeric_years).all():
        raise ValueError("year labels must be finite")

    if not np.equal(
        numeric_years,
        np.floor(numeric_years),
    ).all():
        raise ValueError("year labels must be whole numbers")

    normalised_years = [
        int(year)
        for year in numeric_years
    ]

    if len(normalised_years) != len(set(normalised_years)):
        raise ValueError("year labels must be unique")

    area_by_year.columns = normalised_years

    years = sorted(normalised_years)
    area_by_year = area_by_year.loc[:, years]

    area_values = area_by_year.to_numpy(dtype=float)

    if not np.isfinite(area_values).all():
        raise ValueError(
            "area values must be finite and cannot be missing"
        )

    if (area_values < 0).any():
        raise ValueError("area values cannot be negative")

    periods: list[tuple[int, int]] = list(
        zip(years[:-1], years[1:])
    )

    if len(years) > 2:
        periods.append((years[0], years[-1]))

    percentage_changes = pd.DataFrame(
        index=area_by_year.index.copy()
    )

    for earlier_year, later_year in periods:
        earlier_area = area_by_year[earlier_year]
        later_area = area_by_year[later_year]

        # Replace zero with NaN because division by an earlier area of
        # zero does not produce a meaningful relative percentage.
        valid_earlier_area = earlier_area.where(
            earlier_area != 0
        )

        percentage_changes[f"{earlier_year}–{later_year}"] = (
            later_area
            .sub(earlier_area)
            .div(valid_earlier_area)
            .mul(100)
        )

    return percentage_changes.rename_axis(columns="period")
