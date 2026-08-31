from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest
from rasterio.crs import CRS
from rasterio.errors import RasterioIOError

from land_cover_change.data_access.raster import (
    discover_lulc_rasters,
    extract_raster_map_metadata,
)


@pytest.mark.parametrize(
    "path_converter",
    [
        pytest.param(lambda path: path, id="path-object"),
        pytest.param(str, id="string-path"),
    ],
)
def test_discover_lulc_rasters_returns_sorted_raster_files(
    tmp_path: Path,
    path_converter: Callable[[Path], str | Path],
) -> None:
    raster_directory = tmp_path / "rasters"
    raster_directory.mkdir()
    expected_paths = [
        raster_directory / "lulc_2016.TIF",
        raster_directory / "lulc_2020.tiff",
        raster_directory / "lulc_2025.tif",
    ]

    for raster_path in expected_paths:
        raster_path.touch()

    (raster_directory / "notes.txt").touch()
    (raster_directory / "not_a_file.tif").mkdir()
    nested_directory = raster_directory / "nested"
    nested_directory.mkdir()
    (nested_directory / "nested.tif").touch()

    result = discover_lulc_rasters(path_converter(raster_directory))

    assert result == sorted(expected_paths)


@pytest.mark.parametrize(
    ("variant", "error_type", "error_match"),
    [
        pytest.param(
            "unsupported-type",
            TypeError,
            "must be either str or Path",
            id="unsupported-path-type",
        ),
        pytest.param(
            "missing",
            FileNotFoundError,
            "does not exist",
            id="missing-directory",
        ),
        pytest.param(
            "file",
            NotADirectoryError,
            "not a directory",
            id="path-is-file",
        ),
        pytest.param(
            "empty",
            FileNotFoundError,
            "No raster file found",
            id="no-raster-files",
        ),
    ],
)
def test_discover_lulc_rasters_rejects_invalid_input(
    tmp_path: Path,
    variant: str,
    error_type: type[Exception],
    error_match: str,
) -> None:
    if variant == "unsupported-type":
        directory_path: object = 42
    elif variant == "missing":
        directory_path = tmp_path / "missing"
    elif variant == "file":
        directory_path = tmp_path / "raster.tif"
        directory_path.touch()
    else:
        directory_path = tmp_path / "empty"
        directory_path.mkdir()

    with pytest.raises(error_type, match=error_match):
        discover_lulc_rasters(directory_path)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "path_converter",
    [
        pytest.param(lambda path: path, id="path-object"),
        pytest.param(str, id="string-path"),
    ],
)
def test_extract_raster_map_metadata_returns_expected_values(
    raster_factory: Callable[..., Path],
    path_converter: Callable[[Path], str | Path],
) -> None:
    raster_path = raster_factory(
        "metadata.tif",
        np.array([[0, 1, 2], [3, 4, 255]], dtype=np.uint8),
    )

    result = extract_raster_map_metadata(path_converter(raster_path))

    assert result["coordinate_reference_system"] == CRS.from_epsg(4326)
    assert result["shape"] == (2, 3)
    assert result["resolution"] == (0.01, 0.01)
    assert result["band_count"] == 1
    assert result["data_types"] == ("uint8",)
    assert result["nodata"] == 255


@pytest.mark.parametrize(
    ("variant", "error_type", "error_match"),
    [
        pytest.param(
            "unsupported-type",
            TypeError,
            "must be either str or Path",
            id="unsupported-path-type",
        ),
        pytest.param(
            "missing",
            FileNotFoundError,
            "File not found",
            id="missing-file",
        ),
        pytest.param(
            "missing-crs",
            ValueError,
            "no coordinate reference system",
            id="missing-crs",
        ),
        pytest.param(
            "unreadable",
            RasterioIOError,
            "Unable to read raster file",
            id="unreadable-file",
        ),
    ],
)
def test_extract_raster_map_metadata_rejects_invalid_input(
    tmp_path: Path,
    raster_factory: Callable[..., Path],
    variant: str,
    error_type: type[Exception],
    error_match: str,
) -> None:
    if variant == "unsupported-type":
        raster_path: object = 42
    elif variant == "missing":
        raster_path = tmp_path / "missing.tif"
    elif variant == "missing-crs":
        raster_path = raster_factory(
            "missing_crs.tif",
            np.array([[0]], dtype=np.uint8),
            crs=None,
        )
    else:
        raster_path = tmp_path / "unreadable.tif"
        raster_path.write_text("not a raster", encoding="utf-8")

    with pytest.raises(error_type, match=error_match):
        extract_raster_map_metadata(raster_path)  # type: ignore[arg-type]
