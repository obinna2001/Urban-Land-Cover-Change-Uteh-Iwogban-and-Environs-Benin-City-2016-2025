from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest
import rasterio
from affine import Affine
from rasterio.transform import from_origin


@pytest.fixture
def raster_factory(tmp_path: Path) -> Callable[..., Path]:
    """Return a factory that writes small GeoTIFF fixtures."""

    def write_raster(
        name: str,
        data: np.ndarray,
        *,
        crs: str | None = "EPSG:4326",
        nodata: int | float | None = 255,
        transform: Affine | None = None,
        directory: Path | None = None,
    ) -> Path:
        raster_data = np.asarray(data)

        if raster_data.ndim == 2:
            raster_data = raster_data[np.newaxis, ...]

        output_directory = directory or tmp_path
        output_directory.mkdir(parents=True, exist_ok=True)
        raster_path = output_directory / name

        with rasterio.open(
            raster_path,
            "w",
            driver="GTiff",
            height=raster_data.shape[1],
            width=raster_data.shape[2],
            count=raster_data.shape[0],
            dtype=raster_data.dtype,
            crs=crs,
            transform=transform or from_origin(5.0, 7.0, 0.01, 0.01),
            nodata=nodata,
        ) as raster:
            raster.write(raster_data)

        return raster_path

    return write_raster
