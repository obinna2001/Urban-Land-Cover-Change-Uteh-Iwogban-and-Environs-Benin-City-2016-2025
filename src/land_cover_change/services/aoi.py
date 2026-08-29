from typing import cast
import geopandas as gpd
from shapely.geometry.base import BaseGeometry


def select_administrative_area(
    administrative_data: gpd.GeoDataFrame,
    ward_name: str,
    state_name: str,
) -> gpd.GeoDataFrame:
    """
    Select an administrative area by ward and state name.

    Parameters
    ----------
    administrative_data : geopandas.GeoDataFrame
        GeoDataFrame containing administrative boundary data.
    ward_name : str
        Name of the ward to select.
    state_name : str
        Name of the state containing the ward.

    Returns
    -------
    geopandas.GeoDataFrame
        GeoDataFrame containing the administrative area matching the
        specified ward and state.

    Raises
    ------
    KeyError
        If either the ``wardname`` or ``statename`` column is missing.
    ValueError
        If the specified ward or state is not present, the ward-state
        combination is not found, or all selected geometries are missing.
    """
    required_columns = ["wardname", "statename"]

    administrative_data = administrative_data.rename(
        columns=str.lower
    )

    for col in required_columns:
        if col not in administrative_data.columns:
            raise KeyError(
                f"Required column '{col}' not found in administrative_data"
            )

    ward_name = ward_name.strip().lower()
    state_name = state_name.strip().lower()

    ward_values = administrative_data["wardname"].str.strip().str.lower()   # type: ignore
    state_values = administrative_data["statename"].str.strip().str.lower()

    if ward_name not in ward_values.values:
        raise ValueError(
            f"{ward_name!r} not found in 'wardname' column"
        )

    if state_name not in state_values.values:
        raise ValueError(
            f"{state_name!r} not found in 'statename' column"
        )

    selected_administrative_area = administrative_data.loc[
        (ward_values == ward_name)
        & (state_values == state_name)
    ].copy()

    if selected_administrative_area.empty:
        raise ValueError(
            f"No administrative area found for ward {ward_name!r} "
            f"in state {state_name!r}"
        )

    if selected_administrative_area.geometry.isna().all():
        raise ValueError(
            f"No geometries found for ward {ward_name!r} "
            f"in state {state_name!r}"
        )

    return selected_administrative_area


def normalize_aoi(
    aoi: gpd.GeoDataFrame,
    target_crs: str = "EPSG:4326",
    name: str = "Custom area of interest",
) -> gpd.GeoDataFrame:
    """Validate and standardize an area of interest.

    The input geometries are reprojected, repaired, restricted to polygonal
    features, and combined into one area-of-interest feature.

    Parameters
    ----------
    aoi : geopandas.GeoDataFrame
        GeoDataFrame containing the area-of-interest geometries.
    target_crs : str, default "EPSG:4326"
        Coordinate reference system for the normalized AOI.
    name : str, default "Custom area of interest"
        Descriptive name assigned to the normalized AOI.

    Returns
    -------
    geopandas.GeoDataFrame
        A one-row GeoDataFrame containing a valid Polygon or MultiPolygon,
        an integer ``id`` column, and a ``name`` column.

    Raises
    ------
    TypeError
        If ``aoi`` is not a GeoDataFrame.
    ValueError
        If the input is empty, has no active geometry column, has no defined
        CRS, contains no usable polygon geometry, or cannot produce a valid
        normalized AOI.
    """
    if not isinstance(aoi, gpd.GeoDataFrame):
        raise TypeError("Input aoi must be a GeoDataFrame")

    if not hasattr(aoi, "geometry"):
        raise ValueError("Input aoi has no active geometry column")

    aoi_copy = aoi.copy()

    if aoi_copy.empty:
        raise ValueError(
            "Input aoi is an empty GeoDataFrame. Input a valid GeoDataFrame."
        )

    if aoi_copy.crs is None:
        raise ValueError(
            "Invalid GeoDataFrame. Input aoi has no defined coordinate "
            "reference system."
        )

    aoi_copy = aoi_copy.to_crs(target_crs)

    usable_geometry = (
        aoi_copy.geometry.notna()
        & ~aoi_copy.geometry.is_empty
    )
    aoi_copy = aoi_copy.loc[usable_geometry].copy()

    if aoi_copy.empty:
        raise ValueError("Input aoi contains no usable geometries")

    aoi_copy["geometry"] = aoi_copy.geometry.make_valid()

    # expand possible multipolygon or geometrycollection into separate columns
    aoi_copy = aoi_copy.explode(
        index_parts=False,
        ignore_index=True,
    )

    # filter only Polygon and Multipolygon
    polygon_geometry = (
        aoi_copy.geometry.notna()
        & ~aoi_copy.geometry.is_empty
        & aoi_copy.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
    )
    polygon_data = aoi_copy.loc[polygon_geometry].copy()

    if polygon_data.empty:
        raise ValueError(
            "Input aoi contains no Polygon or MultiPolygon geometry"
        )

    combined_geometry = polygon_data.geometry.union_all()
    normalized_aoi = gpd.GeoDataFrame(
        {
            "id": [1],
            "name": [name],
        },
        geometry=[combined_geometry],
        crs=polygon_data.crs,
    )

    normalized_geometry = normalized_aoi.geometry.iloc[0]
    normalized_geometry = cast(
        BaseGeometry,
        normalized_aoi.geometry.iloc[0],
    )   # silent runtime check error

    if normalized_geometry is None or normalized_geometry.is_empty:
        raise ValueError("Normalized aoi has no usable geometry")

    if normalized_geometry.geom_type not in {"Polygon", "MultiPolygon"}:
        raise ValueError(
            "Normalized aoi is not a Polygon or MultiPolygon"
        )

    if not normalized_geometry.is_valid:
        raise ValueError("Normalized aoi geometry is invalid")

    return normalized_aoi