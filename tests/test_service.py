from collections.abc import Callable

import geopandas as gpd
from geopandas.testing import assert_geodataframe_equal
import pytest
from shapely.geometry import (
    GeometryCollection,
    LineString,
    MultiPolygon,
    Point,
    Polygon,
)

from land_cover_change.services.aoi import (
    normalize_aoi,
    select_administrative_area,
)


def _square(x_offset: float = 0.0) -> Polygon:
    return Polygon(
        [
            (x_offset, 0),
            (x_offset + 1, 0),
            (x_offset + 1, 1),
            (x_offset, 1),
        ]
    )


def _administrative_data() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {
            "wardname": ["Alpha Ward", "Beta Ward"],
            "statename": ["Edo", "Lagos"],
        },
        geometry=[_square(), _square(2)],
        crs="EPSG:4326",
    )


@pytest.mark.parametrize(
    ("data_factory", "ward_name", "state_name"),
    [
        pytest.param(
            _administrative_data,
            "Alpha Ward",
            "Edo",
            id="exact-match",
        ),
        pytest.param(
            _administrative_data,
            "ALPHA WARD",
            "EDO",
            id="case-insensitive",
        ),
        pytest.param(
            _administrative_data,
            "  Alpha Ward  ",
            "  Edo  ",
            id="trimmed-input",
        ),
        pytest.param(
            lambda: _administrative_data().rename(columns=str.upper),
            "Alpha Ward",
            "Edo",
            id="uppercase-columns",
        ),
    ],
)
def test_select_administrative_area_returns_matching_copy(
    data_factory: Callable[[], gpd.GeoDataFrame],
    ward_name: str,
    state_name: str,
) -> None:
    source = data_factory()
    original = source.copy()

    result = select_administrative_area(source, ward_name, state_name)
    result.loc[:, "wardname"] = "Changed"

    assert len(result) == 1
    assert result["statename"].iloc[0] == "Edo"
    assert_geodataframe_equal(source, original)


@pytest.mark.parametrize(
    ("data_factory", "ward_name", "state_name", "error_type", "error_match"),
    [
        pytest.param(
            lambda: _administrative_data().drop(columns="wardname"),
            "Alpha Ward",
            "Edo",
            KeyError,
            "wardname",
            id="missing-ward-column",
        ),
        pytest.param(
            lambda: _administrative_data().drop(columns="statename"),
            "Alpha Ward",
            "Edo",
            KeyError,
            "statename",
            id="missing-state-column",
        ),
        pytest.param(
            _administrative_data,
            "Unknown Ward",
            "Edo",
            ValueError,
            "not found in 'wardname'",
            id="unknown-ward",
        ),
        pytest.param(
            _administrative_data,
            "Alpha Ward",
            "Unknown State",
            ValueError,
            "not found in 'statename'",
            id="unknown-state",
        ),
        pytest.param(
            _administrative_data,
            "Alpha Ward",
            "Lagos",
            ValueError,
            "No administrative area found",
            id="ward-state-mismatch",
        ),
        pytest.param(
            lambda: gpd.GeoDataFrame(
                {
                    "wardname": ["Alpha Ward", "Beta Ward"],
                    "statename": ["Edo", "Lagos"],
                },
                geometry=[None, _square(2)],
                crs="EPSG:4326",
            ),
            "Alpha Ward",
            "Edo",
            ValueError,
            "No geometries found",
            id="selected-geometry-missing",
        ),
    ],
)
def test_select_administrative_area_rejects_invalid_selection(
    data_factory: Callable[[], gpd.GeoDataFrame],
    ward_name: str,
    state_name: str,
    error_type: type[Exception],
    error_match: str,
) -> None:
    with pytest.raises(error_type, match=error_match):
        select_administrative_area(
            data_factory(),
            ward_name,
            state_name,
        )


def _single_polygon_aoi() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        geometry=[_square()],
        crs="EPSG:4326",
    )


def _separate_polygons_aoi() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        geometry=[_square(), _square(2)],
        crs="EPSG:4326",
    )


def _invalid_polygon_aoi() -> gpd.GeoDataFrame:
    bow_tie = Polygon(
        [(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)]
    )
    return gpd.GeoDataFrame(
        geometry=[bow_tie],
        crs="EPSG:4326",
    )


def _mixed_geometry_aoi() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        geometry=[_square(), Point(5, 5), LineString([(6, 6), (7, 7)])],
        crs="EPSG:4326",
    )


def _geometry_collection_aoi() -> gpd.GeoDataFrame:
    multipolygon = MultiPolygon([_square(), _square(2)])
    return gpd.GeoDataFrame(
        geometry=[GeometryCollection([multipolygon, Point(5, 5)])],
        crs="EPSG:4326",
    )


def _projected_aoi() -> gpd.GeoDataFrame:
    return _single_polygon_aoi().to_crs("EPSG:3857")


@pytest.mark.parametrize(
    (
        "data_factory",
        "target_crs",
        "name",
        "expected_geometry_type",
        "expected_epsg",
    ),
    [
        pytest.param(
            _single_polygon_aoi,
            "EPSG:4326",
            "Single AOI",
            "Polygon",
            4326,
            id="single-polygon",
        ),
        pytest.param(
            _separate_polygons_aoi,
            "EPSG:4326",
            "Separate AOI",
            "MultiPolygon",
            4326,
            id="separate-polygons",
        ),
        pytest.param(
            _invalid_polygon_aoi,
            "EPSG:4326",
            "Repaired AOI",
            "MultiPolygon",
            4326,
            id="invalid-polygon-repaired",
        ),
        pytest.param(
            _mixed_geometry_aoi,
            "EPSG:4326",
            "Polygon-only AOI",
            "Polygon",
            4326,
            id="non-polygons-filtered",
        ),
        pytest.param(
            _geometry_collection_aoi,
            "EPSG:4326",
            "Collection AOI",
            "MultiPolygon",
            4326,
            id="geometry-collection",
        ),
        pytest.param(
            _projected_aoi,
            "EPSG:4326",
            "Reprojected AOI",
            "Polygon",
            4326,
            id="reprojected-to-wgs84",
        ),
        pytest.param(
            _single_polygon_aoi,
            "EPSG:3857",
            "Web Mercator AOI",
            "Polygon",
            3857,
            id="custom-target-crs",
        ),
    ],
)
def test_normalize_aoi_returns_standardized_geometry(
    data_factory: Callable[[], gpd.GeoDataFrame],
    target_crs: str,
    name: str,
    expected_geometry_type: str,
    expected_epsg: int,
) -> None:
    source = data_factory()
    original = source.copy()

    result = normalize_aoi(source, target_crs=target_crs, name=name)
    geometry = result.geometry.iloc[0]

    assert len(result) == 1
    assert list(result.columns) == ["id", "name", "geometry"]
    assert result["id"].iloc[0] == 1
    assert result["name"].iloc[0] == name
    assert result.crs is not None
    assert result.crs.to_epsg() == expected_epsg
    assert geometry.geom_type == expected_geometry_type
    assert not geometry.is_empty
    assert geometry.is_valid
    assert_geodataframe_equal(source, original)


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
            "empty GeoDataFrame",
            id="empty-data",
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
        pytest.param(
            lambda: gpd.GeoDataFrame(
                {"geometry": [None]},
                geometry="geometry",
                crs="EPSG:4326",
            ),
            ValueError,
            "no usable geometries",
            id="null-geometry",
        ),
        pytest.param(
            lambda: gpd.GeoDataFrame(
                {"geometry": [Polygon()]},
                geometry="geometry",
                crs="EPSG:4326",
            ),
            ValueError,
            "no usable geometries",
            marks=pytest.mark.filterwarnings(
                "ignore:GeoSeries.notna:UserWarning"
            ),
            id="empty-geometry",
        ),
        pytest.param(
            lambda: gpd.GeoDataFrame(
                geometry=[Point(0, 0)],
                crs="EPSG:4326",
            ),
            ValueError,
            "no Polygon or MultiPolygon",
            id="point-only",
        ),
        pytest.param(
            lambda: gpd.GeoDataFrame(
                geometry=[LineString([(0, 0), (1, 1)])],
                crs="EPSG:4326",
            ),
            ValueError,
            "no Polygon or MultiPolygon",
            id="line-only",
        ),
        pytest.param(
            lambda: gpd.GeoDataFrame(
                geometry=[
                    GeometryCollection(
                        [Point(0, 0), LineString([(0, 0), (1, 1)])]
                    )
                ],
                crs="EPSG:4326",
            ),
            ValueError,
            "no Polygon or MultiPolygon",
            id="non-polygon-geometry-collection",
        ),
    ],
)
def test_normalize_aoi_rejects_invalid_input(
    data_factory: Callable[[], object],
    error_type: type[Exception],
    error_match: str,
) -> None:
    with pytest.raises(error_type, match=error_match):
        normalize_aoi(data_factory())  # type: ignore[arg-type]
