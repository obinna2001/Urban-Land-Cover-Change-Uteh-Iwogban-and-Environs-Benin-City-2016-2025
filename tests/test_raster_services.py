from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest
from rasterio.errors import RasterioIOError

from land_cover_change.services.class_area import (
    build_class_count_table,
    count_land_cover_classes,
)
from land_cover_change.services.raster import (
    colour_land_cover,
    prepare_map_overlay,
)


@pytest.fixture
def palette() -> dict[int, str]:
    return {
        0: "#419BDF",
        1: "#397D49",
        2: "#88B053",
        6: "#C4281B",
    }


@pytest.mark.parametrize(
    "path_converter",
    [
        pytest.param(lambda path: path, id="path-object"),
        pytest.param(str, id="string-path"),
    ],
)
def test_count_land_cover_classes_counts_only_valid_pixels(
    raster_factory: Callable[..., Path],
    path_converter: Callable[[Path], str | Path],
) -> None:
    raster_path = raster_factory(
        "classes.tif",
        np.array([[0, 1, 1], [6, 255, 6]], dtype=np.uint8),
    )

    result = count_land_cover_classes(path_converter(raster_path))

    assert result == {0: 1, 1: 2, 6: 2}
    assert all(type(value) is int for value in result)


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
            "multiple-bands",
            ValueError,
            "exactly one raster band",
            id="multiple-bands",
        ),
        pytest.param(
            "all-masked",
            ValueError,
            "no valid land-cover pixels",
            id="all-masked",
        ),
        pytest.param(
            "unreadable",
            RasterioIOError,
            "Unable to read raster file",
            id="unreadable-file",
        ),
    ],
)
def test_count_land_cover_classes_rejects_invalid_input(
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
    elif variant == "multiple-bands":
        raster_path = raster_factory(
            "multiple_bands.tif",
            np.array([[[0]], [[1]]], dtype=np.uint8),
        )
    elif variant == "all-masked":
        raster_path = raster_factory(
            "all_masked.tif",
            np.full((2, 2), 255, dtype=np.uint8),
        )
    else:
        raster_path = tmp_path / "unreadable.tif"
        raster_path.write_text("not a raster", encoding="utf-8")

    with pytest.raises(error_type, match=error_match):
        count_land_cover_classes(raster_path)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "sequence_factory",
    [
        pytest.param(lambda first, second: [first, str(second)], id="list"),
        pytest.param(lambda first, second: (str(first), second), id="tuple"),
    ],
)
def test_build_class_count_table_combines_rasters_and_fills_missing_classes(
    raster_factory: Callable[..., Path],
    sequence_factory: Callable[[Path, Path], list[str | Path] | tuple[str | Path, ...]],
) -> None:
    first_path = raster_factory(
        "lulc_2016.tif",
        np.array([[0, 1], [1, 255]], dtype=np.uint8),
    )
    second_path = raster_factory(
        "lulc_2020.tif",
        np.array([[1, 2], [2, 2]], dtype=np.uint8),
    )

    result = build_class_count_table(
        sequence_factory(first_path, second_path)
    )
    expected = pd.DataFrame(
        {
            "class_value": [0, 1, 2],
            "lulc_2016.tif": [1, 2, 0],
            "lulc_2020.tif": [0, 1, 3],
        },
        dtype="int64",
    )

    assert_frame_equal(result, expected)


@pytest.mark.parametrize(
    ("variant", "error_type", "error_match"),
    [
        pytest.param(
            "single-string",
            TypeError,
            "must be a sequence",
            id="single-string-path",
        ),
        pytest.param(
            "single-path",
            TypeError,
            "must be a sequence",
            id="single-path-object",
        ),
        pytest.param(
            "empty",
            ValueError,
            "cannot be empty",
            id="empty-sequence",
        ),
        pytest.param(
            "unsupported-item",
            TypeError,
            "must be either str or Path",
            id="unsupported-item-type",
        ),
        pytest.param(
            "duplicate-filenames",
            ValueError,
            "file names must be unique",
            id="duplicate-filenames",
        ),
    ],
)
def test_build_class_count_table_rejects_invalid_input(
    tmp_path: Path,
    variant: str,
    error_type: type[Exception],
    error_match: str,
) -> None:
    if variant == "single-string":
        raster_paths: object = "raster.tif"
    elif variant == "single-path":
        raster_paths = Path("raster.tif")
    elif variant == "empty":
        raster_paths = []
    elif variant == "unsupported-item":
        raster_paths = [Path("raster.tif"), 42]
    else:
        first_directory = tmp_path / "first"
        second_directory = tmp_path / "second"
        first_directory.mkdir()
        second_directory.mkdir()
        raster_paths = [
            first_directory / "same_name.tif",
            second_directory / "same_name.tif",
        ]

    with pytest.raises(error_type, match=error_match):
        build_class_count_table(raster_paths)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("land_cover", "expected"),
    [
        pytest.param(
            np.array([[0, 1], [2, 6]], dtype=np.uint8),
            np.array(
                [
                    [[65, 155, 223, 255], [57, 125, 73, 255]],
                    [[136, 176, 83, 255], [196, 40, 27, 255]],
                ],
                dtype=np.uint8,
            ),
            id="plain-array",
        ),
        pytest.param(
            np.ma.array(
                [[0, 1], [2, 6]],
                mask=[[False, True], [False, False]],
            ),
            np.array(
                [
                    [[65, 155, 223, 255], [0, 0, 0, 0]],
                    [[136, 176, 83, 255], [196, 40, 27, 255]],
                ],
                dtype=np.uint8,
            ),
            id="masked-array",
        ),
    ],
)
def test_colour_land_cover_returns_expected_rgba_image(
    palette: dict[int, str],
    land_cover: np.ndarray,
    expected: np.ndarray,
) -> None:
    result = colour_land_cover(land_cover, palette)

    np.testing.assert_array_equal(result, expected)


@pytest.mark.parametrize(
    ("land_cover", "palette_value", "error_type", "error_match"),
    [
        pytest.param(
            [[0]],
            {0: "#000000"},
            TypeError,
            "must be a NumPy array",
            id="non-array",
        ),
        pytest.param(
            np.array([0]),
            {0: "#000000"},
            ValueError,
            "two-dimensional",
            id="one-dimensional-array",
        ),
        pytest.param(
            np.empty((0, 0), dtype=np.uint8),
            {0: "#000000"},
            ValueError,
            "cannot be empty",
            id="empty-array",
        ),
        pytest.param(
            np.array([[0]]),
            [],
            TypeError,
            "palette must be a mapping",
            id="non-mapping-palette",
        ),
        pytest.param(
            np.array([[0]]),
            {},
            ValueError,
            "palette cannot be empty",
            id="empty-palette",
        ),
        pytest.param(
            np.array([[0]]),
            {True: "#000000"},
            TypeError,
            "class values must be integers",
            id="boolean-class-value",
        ),
        pytest.param(
            np.array([[0]]),
            {0: 123},
            TypeError,
            "must be a string",
            id="non-string-colour",
        ),
        pytest.param(
            np.array([[0]]),
            {0: "not-a-colour"},
            ValueError,
            "Invalid colour",
            id="invalid-colour",
        ),
        pytest.param(
            np.array([[8]]),
            {0: "#000000"},
            ValueError,
            "classes missing from the palette",
            id="unknown-raster-class",
        ),
    ],
)
def test_colour_land_cover_rejects_invalid_input(
    land_cover: object,
    palette_value: object,
    error_type: type[Exception],
    error_match: str,
) -> None:
    with pytest.raises(error_type, match=error_match):
        colour_land_cover(  # type: ignore[arg-type]
            land_cover,
            palette_value,
        )


@pytest.mark.parametrize(
    ("source_crs", "path_converter"),
    [
        pytest.param(
            "EPSG:4326",
            lambda path: path,
            id="geographic-path-object",
        ),
        pytest.param(
            "EPSG:4326",
            str,
            id="geographic-string-path",
        ),
        pytest.param(
            "EPSG:3857",
            lambda path: path,
            id="web-mercator-path-object",
        ),
    ],
)
def test_prepare_map_overlay_returns_rgba_image_and_geographic_bounds(
    raster_factory: Callable[..., Path],
    palette: dict[int, str],
    source_crs: str,
    path_converter: Callable[[Path], str | Path],
) -> None:
    raster_path = raster_factory(
        "overlay.tif",
        np.array([[0, 1], [6, 255]], dtype=np.uint8),
        crs=source_crs,
    )

    result = prepare_map_overlay(path_converter(raster_path), palette)
    (south, west), (north, east) = result.bounds

    assert result.image.ndim == 3
    assert result.image.shape[2] == 4
    assert result.image.dtype == np.uint8
    assert set(np.unique(result.image[..., 3]).tolist()) == {0, 255}
    assert -90 <= south < north <= 90
    assert -180 <= west < east <= 180


@pytest.mark.parametrize(
    ("variant", "error_type", "error_match"),
    [
        pytest.param(
            "unsupported-path-type",
            TypeError,
            "raster_path must be a string or Path",
            id="unsupported-path-type",
        ),
        pytest.param(
            "non-mapping-palette",
            TypeError,
            "palette must be a mapping",
            id="non-mapping-palette",
        ),
        pytest.param(
            "invalid-crs-type",
            TypeError,
            "projected_crs must be an integer",
            id="invalid-projected-crs-type",
        ),
        pytest.param(
            "non-web-mercator",
            ValueError,
            "must be EPSG:3857",
            id="non-web-mercator-target",
        ),
        pytest.param(
            "missing-file",
            FileNotFoundError,
            "Raster file not found",
            id="missing-file",
        ),
        pytest.param(
            "missing-crs",
            ValueError,
            "defined coordinate reference system",
            id="missing-crs",
        ),
        pytest.param(
            "multiple-bands",
            ValueError,
            "exactly one raster band",
            id="multiple-bands",
        ),
        pytest.param(
            "nodata-conflict",
            ValueError,
            "NoData value that conflicts",
            id="nodata-conflicts-with-class",
        ),
        pytest.param(
            "all-masked",
            ValueError,
            "no valid land-cover pixels",
            id="all-masked",
        ),
        pytest.param(
            "unknown-class",
            ValueError,
            "classes missing from the palette",
            id="unknown-raster-class",
        ),
        pytest.param(
            "unreadable",
            RasterioIOError,
            "not recognized as being in a supported file format",
            id="unreadable-file",
        ),
    ],
)
def test_prepare_map_overlay_rejects_invalid_input(
    tmp_path: Path,
    raster_factory: Callable[..., Path],
    palette: dict[int, str],
    variant: str,
    error_type: type[Exception],
    error_match: str,
) -> None:
    raster_path: object = raster_factory(
        "valid.tif",
        np.array([[0, 1]], dtype=np.uint8),
    )
    palette_value: object = palette
    projected_crs: object = 3857

    if variant == "unsupported-path-type":
        raster_path = 42
    elif variant == "non-mapping-palette":
        palette_value = []
    elif variant == "invalid-crs-type":
        projected_crs = "EPSG:3857"
    elif variant == "non-web-mercator":
        projected_crs = 32631
    elif variant == "missing-file":
        raster_path = tmp_path / "missing.tif"
    elif variant == "missing-crs":
        raster_path = raster_factory(
            "missing_crs.tif",
            np.array([[0]], dtype=np.uint8),
            crs=None,
        )
    elif variant == "multiple-bands":
        raster_path = raster_factory(
            "multiple_bands.tif",
            np.array([[[0]], [[1]]], dtype=np.uint8),
        )
    elif variant == "nodata-conflict":
        raster_path = raster_factory(
            "nodata_conflict.tif",
            np.array([[1]], dtype=np.uint8),
            nodata=0,
        )
    elif variant == "all-masked":
        raster_path = raster_factory(
            "all_masked.tif",
            np.full((2, 2), 255, dtype=np.uint8),
        )
    elif variant == "unknown-class":
        raster_path = raster_factory(
            "unknown_class.tif",
            np.array([[8]], dtype=np.uint8),
        )
    elif variant == "unreadable":
        raster_path = tmp_path / "unreadable.tif"
        raster_path.write_text("not a raster", encoding="utf-8")

    with pytest.raises(error_type, match=error_match):
        prepare_map_overlay(  # type: ignore[arg-type]
            raster_path,
            palette_value,
            projected_crs,
        )
