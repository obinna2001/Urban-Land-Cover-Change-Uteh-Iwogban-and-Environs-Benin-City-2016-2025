from pathlib import Path
import geopandas as gpd


def load_vector_data(path: str | Path) -> gpd.GeoDataFrame:
    """Load and validate a vector file as a GeoDataFrame.

    Parameters
    ----------
    path : str or pathlib.Path
        Path to the vector file.

    Returns
    -------
    geopandas.GeoDataFrame
        The loaded vector data.

    Raises
    ------
    FileNotFoundError
        If the specified file does not exist.
    ValueError
        If the file is empty, all geometries are missing, or the data has no
        defined coordinate reference system.

    """
    file_path = Path(path)

    if not file_path.is_file():
        raise FileNotFoundError(f"{str(path)!r} not found")

    vector_data = gpd.read_file(file_path)

    if vector_data.empty:
        raise ValueError(f"{file_path.name!r} is an empty file")

    if vector_data.geometry.isna().all():
        raise ValueError(
            f"All geometries in {file_path.name!r} are missing"
        )

    if vector_data.crs is None:
        raise ValueError(
            f"{file_path.name!r} has no defined coordinate reference system"
        )

    return vector_data


def save_shapefile(
    data: gpd.GeoDataFrame,
    output_path: str | Path,
) -> Path:
    """Save a GeoDataFrame as an ESRI Shapefile.

    Parameters
    ----------
    data : geopandas.GeoDataFrame
        Vector data to save.
    output_path : str or pathlib.Path
        Destination path for the ``.shp`` file. Missing parent directories
        are created automatically.

    Returns
    -------
    pathlib.Path
        Path to the saved ``.shp`` file.

    Raises
    ------
    TypeError
        If ``data`` is not a GeoDataFrame or ``output_path`` is not a string
        or Path.
    ValueError
        If the GeoDataFrame is empty, has no active geometry column, all
        geometries are missing, or its CRS is undefined.

    Notes
    -----
    GeoPandas and the underlying file-writing library may raise additional
    filesystem or driver errors if the destination cannot be written.
    """
    if not isinstance(data, gpd.GeoDataFrame):
        raise TypeError("Input data must be a GeoDataFrame")

    if not hasattr(data, "geometry"):
        raise ValueError("Input data has no active geometry column")

    if data.empty:
        raise ValueError("Input GeoDataFrame is empty")

    if data.geometry.isna().all():
        raise ValueError("All geometries in the input data are missing")

    if data.crs is None:
        raise ValueError(
            "Input GeoDataFrame has no defined coordinate reference system"
        )

    if not isinstance(output_path, (str, Path)):
        raise TypeError(f"output_path must be either str or Path")

    file_path = Path(output_path)

    file_path.parent.mkdir(parents=True, exist_ok=True)
    data.to_file(
        file_path,
        driver="ESRI Shapefile",
        encoding="utf-8",
        index=False,
    )

    return file_path
