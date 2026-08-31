from collections.abc import Callable
from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import Point, Polygon

from land_cover_change.data_access.vector import (
    load_vector_data,
    save_shapefile,
)


def _valid_vector_data() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {"label": ["study area"]},
        geometry=[Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])],
        crs="EPSG:4326",
    )


@pytest.mark.parametrize(
    "path_converter",
    [
        pytest.param(lambda path: path, id="path-object"),
        pytest.param(str, id="string-path"),
    ],
)
def test_load_vector_data_accepts_supported_path_types(
    tmp_path: Path,
    path_converter: Callable[[Path], str | Path],
) -> None:
    source_path = tmp_path / "source.geojson"
    expected = _valid_vector_data()
    expected.to_file(source_path, driver="GeoJSON", index=False)

    result = load_vector_data(path_converter(source_path))

    assert len(result) == 1
    assert result.crs == expected.crs
    assert result.geometry.iloc[0] == expected.geometry.iloc[0]


@pytest.mark.parametrize(
    "missing_path",
    [
        pytest.param("missing.geojson", id="string-path"),
        pytest.param(Path("missing.shp"), id="path-object"),
    ],
)
def test_load_vector_data_rejects_missing_file(
    tmp_path: Path,
    missing_path: str | Path,
) -> None:
    path = tmp_path / missing_path

    with pytest.raises(FileNotFoundError, match="not found"):
        load_vector_data(path)


@pytest.mark.parametrize(
    ("data_factory", "error_match"),
    [
        pytest.param(
            lambda: gpd.GeoDataFrame(
                {"geometry": []},
                geometry="geometry",
                crs="EPSG:4326",
            ),
            "empty file",
            id="empty-data",
        ),
        pytest.param(
            lambda: gpd.GeoDataFrame(
                {"geometry": [None]},
                geometry="geometry",
                crs="EPSG:4326",
            ),
            "All geometries",
            id="all-geometries-missing",
        ),
        pytest.param(
            lambda: gpd.GeoDataFrame(
                {"geometry": [Point(0, 0)]},
                geometry="geometry",
                crs=None,
            ),
            "no defined coordinate reference system",
            id="missing-crs",
        ),
    ],
)
def test_load_vector_data_rejects_invalid_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    data_factory: Callable[[], gpd.GeoDataFrame],
    error_match: str,
) -> None:
    existing_path = tmp_path / "source.geojson"
    existing_path.touch()
    monkeypatch.setattr(gpd, "read_file", lambda _: data_factory())

    with pytest.raises(ValueError, match=error_match):
        load_vector_data(existing_path)


@pytest.mark.parametrize(
    "path_converter",
    [
        pytest.param(lambda path: path, id="path-object"),
        pytest.param(str, id="string-path"),
    ],
)
def test_save_shapefile_writes_reloadable_data(
    tmp_path: Path,
    path_converter: Callable[[Path], str | Path],
) -> None:
    data = _valid_vector_data()
    output_path = tmp_path / "nested" / "aoi.shp"

    saved_path = save_shapefile(data, path_converter(output_path))
    reloaded = load_vector_data(saved_path)

    assert saved_path == output_path
    assert saved_path.is_file()
    assert list(reloaded.columns) == ["label", "geometry"]
    assert reloaded.crs == data.crs
    assert reloaded.geometry.iloc[0] == data.geometry.iloc[0]


@pytest.mark.parametrize(
    ("data_factory", "error_type", "error_match"),
    [
        pytest.param(
            lambda: {"geometry": []},
            TypeError,
            "must be a GeoDataFrame",
            id="not-geodataframe",
        ),
        pytest.param(
            lambda: gpd.GeoDataFrame({"value": [1]}),
            ValueError,
            "no active geometry column",
            id="missing-geometry-column",
        ),
        pytest.param(
            lambda: gpd.GeoDataFrame(
                {"geometry": []},
                geometry="geometry",
                crs="EPSG:4326",
            ),
            ValueError,
            "is empty",
            id="empty-data",
        ),
        pytest.param(
            lambda: gpd.GeoDataFrame(
                {"geometry": [None]},
                geometry="geometry",
                crs="EPSG:4326",
            ),
            ValueError,
            "All geometries",
            id="all-geometries-missing",
        ),
        pytest.param(
            lambda: gpd.GeoDataFrame(
                {"geometry": [Point(0, 0)]},
                geometry="geometry",
                crs=None,
            ),
            ValueError,
            "no defined coordinate reference system",
            id="missing-crs",
        ),
    ],
)
def test_save_shapefile_rejects_invalid_data(
    tmp_path: Path,
    data_factory: Callable[[], object],
    error_type: type[Exception],
    error_match: str,
) -> None:
    with pytest.raises(error_type, match=error_match):
        save_shapefile(data_factory(), tmp_path / "aoi.shp")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "invalid_path",
    [
        pytest.param(None, id="none-path"),
        pytest.param(123, id="integer-path"),
        pytest.param([], id="list-path"),
    ],
)
def test_save_shapefile_rejects_invalid_path_type(
    invalid_path: object,
) -> None:
    with pytest.raises(TypeError, match="output_path must be either str or Path"):
        save_shapefile(_valid_vector_data(), invalid_path)  # type: ignore[arg-type]
