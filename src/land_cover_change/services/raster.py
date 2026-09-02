from pathlib import Path
from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
from matplotlib.colors import to_rgba

import rasterio
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT
from rasterio.warp import transform_bounds

# ------------------------------------------------------------------------------
# OUTPUT DATA MODELS
# ------------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class RasterMapOverlay:
    image: np.ndarray
    bounds: tuple[
        tuple[float, float],
        tuple[float, float]
    ]


# -----------------------------------------------------------------------------
# SERVICE FUNCTIONS
# -----------------------------------------------------------------------------
def colour_land_cover(
    land_cover: np.ndarray | np.ma.MaskedArray,
    palette: Mapping[int, str],
) -> np.ndarray:
    """Convert a categorical land-cover array to an RGBA image.

    Parameters
    ----------
    land_cover : numpy.ndarray or numpy.ma.MaskedArray
        Two-dimensional array containing categorical land-cover class values.
        Masked pixels are represented as fully transparent pixels in the
        returned image.
    palette : collections.abc.Mapping[int, str]
        Mapping from each supported land-cover class value to a Matplotlib-
        compatible colour string.

    Returns
    -------
    numpy.ndarray
        Unsigned 8-bit RGBA array with shape ``(height, width, 4)``.

    Raises
    ------
    TypeError
        If ``land_cover`` is not a NumPy array, ``palette`` is not a mapping,
        or the palette contains non-integer class values or non-string
        colours.
    ValueError
        If ``land_cover`` is empty or not two-dimensional, ``palette`` is
        empty, a palette colour is invalid, or an unmasked raster class is
        absent from the palette.

    """
    if not isinstance(land_cover, np.ndarray):
        raise TypeError(
            "land_cover must be a NumPy array or masked array"
        )

    if land_cover.ndim != 2:
        raise ValueError("land_cover must be a two-dimensional array")

    if land_cover.size == 0:
        raise ValueError("land_cover cannot be empty")

    if not isinstance(palette, Mapping):
        raise TypeError("palette must be a mapping of class values to colours")

    if not palette:
        raise ValueError("palette cannot be empty")

    rgba_palette: dict[int, tuple[int, int, int, int]] = {}

    for class_value, colour in palette.items():
        if (
            isinstance(class_value, (bool, np.bool_))
            or not isinstance(class_value, (int, np.integer))
        ):
            raise TypeError("palette class values must be integers")

        if not isinstance(colour, str):
            raise TypeError(
                f"Colour for class {class_value!r} must be a string"
            )

        try:
            red, green, blue, alpha = to_rgba(colour)

            rgba_palette[int(class_value)] = (
                round(red * 255),
                round(green * 255),
                round(blue * 255),
                round(alpha * 255),
            )
        except ValueError as exc:
            raise ValueError(
                f"Invalid colour {colour!r} for class {class_value!r}"
            ) from exc

    data = np.ma.getdata(land_cover)
    mask = np.ma.getmaskarray(land_cover)
    observed_classes = set(np.unique(data[~mask]).tolist())
    unknown_classes = observed_classes.difference(rgba_palette)

    if unknown_classes:
        formatted_classes = ", ".join(
            repr(class_value)
            for class_value in sorted(unknown_classes, key=repr)
        )
        raise ValueError(
            "land_cover contains classes missing from the palette: "
            f"{formatted_classes}"
        )

    rgba_image = np.zeros((*data.shape, 4), dtype=np.uint8)

    for class_value, rgba_colour in rgba_palette.items():
        class_pixels = (data == class_value) & ~mask
        rgba_image[class_pixels] = rgba_colour

    return rgba_image


def prepare_map_overlay(
    raster_path: str | Path,
    palette: Mapping[int, str],
    projected_crs: int = 3857,
) -> RasterMapOverlay:
    """Prepare a categorical raster for display over OpenStreetMap.

    The raster grid is reprojected to Web Mercator using nearest-neighbour
    resampling so its categorical class values remain unchanged. The returned
    bounds are converted to WGS 84 latitude/longitude order for Folium.

    Parameters
    ----------
    raster_path : str or pathlib.Path
        Path to a single-band categorical land-cover raster.
    palette : collections.abc.Mapping[int, str]
        Mapping from land-cover class values to display colours.
    projected_crs : int, default 3857
        EPSG code for the OpenStreetMap Web Mercator projection. Values other
        than ``3857`` are rejected because the resulting image would not align
        with the configured basemap.

    Returns
    -------
    RasterMapOverlay
        Colourised RGBA image and Folium bounds in
        ``((south, west), (north, east))`` order.

    Raises
    ------
    TypeError
        If ``raster_path`` is not a string or Path, ``palette`` is not a
        mapping, or ``projected_crs`` is not an integer.
    FileNotFoundError
        If ``raster_path`` does not identify an existing file.
    ValueError
        If ``projected_crs`` is not EPSG:3857, the raster has no CRS, does not
        contain exactly one band, has a NoData value that conflicts with a
        configured class, contains no valid pixels, or cannot be colourised
        with ``palette``.
    rasterio.errors.RasterioIOError
        If the file exists but Rasterio cannot open or read it.

    """
    if not isinstance(raster_path, (str, Path)):
        raise TypeError("raster_path must be a string or Path object")

    if not isinstance(palette, Mapping):
        raise TypeError("palette must be a mapping of class values to colours")

    if isinstance(projected_crs, bool) or not isinstance(projected_crs, int):
        raise TypeError("projected_crs must be an integer EPSG code")

    target_crs = CRS.from_epsg(projected_crs)
    web_mercator_crs = CRS.from_epsg(3857)

    if target_crs != web_mercator_crs:
        raise ValueError(
            "projected_crs must be EPSG:3857 for an OpenStreetMap overlay"
        )

    if isinstance(raster_path, str):
        raster_path = Path(raster_path)

    if not raster_path.is_file():
        raise FileNotFoundError(f"Raster file not found: {raster_path!r}")

    with rasterio.open(raster_path) as raster_data:
        if raster_data.crs is None:
            raise ValueError(
                f"{raster_path.name!r} does not have a defined coordinate "
                "reference system"
            )

        if raster_data.count != 1:
            raise ValueError(
                f"{raster_path.name!r} must contain exactly one raster band"
            )

        if (
            raster_data.nodata is not None
            and raster_data.nodata in palette
        ):
            raise ValueError(
                f"{raster_path.name!r} has a NoData value that conflicts "
                "with a configured land-cover class"
            )

        with WarpedVRT(
            raster_data,
            crs=target_crs,
            resampling=Resampling.nearest,
        ) as projected_raster:
            land_cover_array = projected_raster.read(1, masked=True)

            if land_cover_array.count() == 0:
                raise ValueError(
                    f"{raster_path.name!r} contains no valid land-cover pixels"
                )

            rgba_image = colour_land_cover(land_cover_array, palette)

            west, south, east, north = transform_bounds(
                projected_raster.crs,
                CRS.from_epsg(4326),
                *projected_raster.bounds,
                densify_pts=21,
            )

    return RasterMapOverlay(
        image=rgba_image,
        bounds=((south, west), (north, east)),
    )
