from collections.abc import Collection
from numbers import Real

import numpy as np
import pandas as pd


def calculate_transition_matrix(
    earlier: np.ndarray | np.ma.MaskedArray,
    later: np.ndarray | np.ma.MaskedArray,
    classes: Collection[int],
) -> pd.DataFrame:
    """Count pixel-level land-cover transitions between two aligned arrays.

    Only pixels valid in both arrays are included. Rows represent classes in
    the earlier observation and columns represent classes in the later
    observation.

    Parameters
    ----------
    earlier : numpy.ndarray or numpy.ma.MaskedArray
        Two-dimensional categorical raster values for the earlier period.
    later : numpy.ndarray or numpy.ma.MaskedArray
        Two-dimensional categorical raster values for the later period on the
        same spatial grid as ``earlier``.
    classes : collections.abc.Collection[int]
        Supported land-cover class values. Every class appears on both matrix
        axes, including classes with no observed transitions.

    Returns
    -------
    pandas.DataFrame
        Integer transition-count matrix with index name ``from_class`` and
        column name ``to_class``.

    Raises
    ------
    TypeError
        If either raster is not a NumPy array, contains non-numeric data, or
        ``classes`` is not a non-string collection of integers.
    ValueError
        If either raster is empty or not two-dimensional; their shapes differ;
        ``classes`` is empty or contains duplicates; no pixels are valid in
        both rasters; an unmasked value is non-finite; or either raster
        contains unsupported class values.

    Notes
    -----
    Array shape equality does not establish geospatial alignment. Callers must
    prepare both rasters on the same projected grid before using this function.

    """
    if not isinstance(earlier, np.ndarray):
        raise TypeError("earlier must be a NumPy array or masked array")

    if not isinstance(later, np.ndarray):
        raise TypeError("later must be a NumPy array or masked array")

    for name, raster in (("earlier", earlier), ("later", later)):
        if raster.ndim != 2:
            raise ValueError(f"{name} must be a two-dimensional array")

        if raster.size == 0:
            raise ValueError(f"{name} cannot be empty")

        data_type = np.ma.getdata(raster).dtype

        if (
            np.issubdtype(data_type, np.bool_)
            or not np.issubdtype(data_type, np.number)
        ):
            raise TypeError(f"{name} must contain numeric class values")

    if earlier.shape != later.shape:
        raise ValueError("earlier and later must have the same shape")

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

    sorted_classes = sorted(normalised_classes)
    supported_classes = set(sorted_classes)
    common_valid_mask = ~(
        np.ma.getmaskarray(earlier)
        | np.ma.getmaskarray(later)
    )

    if not common_valid_mask.any():
        raise ValueError("earlier and later have no commonly valid pixels")

    earlier_values = np.ma.getdata(earlier)[common_valid_mask]
    later_values = np.ma.getdata(later)[common_valid_mask]

    if not np.isfinite(earlier_values).all():
        raise ValueError("earlier contains non-finite unmasked class values")

    if not np.isfinite(later_values).all():
        raise ValueError("later contains non-finite unmasked class values")

    for name, values in (
        ("earlier", earlier_values),
        ("later", later_values),
    ):
        observed_classes = set(np.unique(values).tolist())
        unsupported_classes = observed_classes.difference(supported_classes)

        if unsupported_classes:
            formatted_classes = ", ".join(
                repr(class_value)
                for class_value in sorted(
                    unsupported_classes,
                    key=repr,
                )
            )
            raise ValueError(
                f"{name} contains unsupported land-cover classes: "
                f"{formatted_classes}"
            )

    transition_matrix = pd.crosstab(
        pd.Categorical(earlier_values, categories=sorted_classes),
        pd.Categorical(later_values, categories=sorted_classes),
        rownames=["from_class"],
        colnames=["to_class"],
        dropna=False,
    ).astype("int64")

    transition_matrix.index = pd.Index(
        sorted_classes,
        dtype="int64",
        name="from_class",
    )
    transition_matrix.columns = pd.Index(
        sorted_classes,
        dtype="int64",
        name="to_class",
    )

    return transition_matrix


def _validate_transition_matrix(
    matrix: pd.DataFrame,
    *,
    require_whole_numbers: bool = True,
) -> np.ndarray:
    """Validate a transition matrix and return its values as floats."""
    value_kind = "counts" if require_whole_numbers else "areas"

    if not isinstance(matrix, pd.DataFrame):
        raise TypeError("matrix must be a pandas DataFrame")

    if matrix.empty:
        raise ValueError("matrix cannot be empty")

    if matrix.shape[0] != matrix.shape[1]:
        raise ValueError("matrix must be square")

    if matrix.index.nlevels != 1 or matrix.columns.nlevels != 1:
        raise ValueError(
            "matrix index and columns must each contain exactly one level"
        )

    if not matrix.index.is_unique:
        raise ValueError("matrix index class labels must be unique")

    if not matrix.columns.is_unique:
        raise ValueError("matrix column class labels must be unique")

    if matrix.index.hasnans:
        raise ValueError("matrix index cannot contain missing class labels")

    if matrix.columns.hasnans:
        raise ValueError("matrix columns cannot contain missing class labels")

    if not (
        matrix.index.isin(matrix.columns).all()
        and matrix.columns.isin(matrix.index).all()
    ):
        raise ValueError(
            "matrix index and columns must contain the same class labels"
        )

    invalid_columns = [
        column
        for column in matrix.columns
        if (
            pd.api.types.is_bool_dtype(matrix[column])
            or pd.api.types.is_complex_dtype(matrix[column])
            or not pd.api.types.is_numeric_dtype(matrix[column])
        )
    ]

    if invalid_columns:
        formatted_columns = ", ".join(
            repr(column) for column in invalid_columns
        )
        raise TypeError(
            f"matrix must contain only real numeric {value_kind}; "
            "invalid columns: "
            f"{formatted_columns}"
        )

    numeric_counts = matrix.to_numpy(dtype="float64", na_value=np.nan)

    if not np.isfinite(numeric_counts).all():
        raise ValueError(
            f"matrix {value_kind} must be finite and cannot be missing"
        )

    if (numeric_counts < 0).any():
        raise ValueError(f"matrix {value_kind} cannot be negative")

    if (
        require_whole_numbers
        and not np.equal(numeric_counts, np.floor(numeric_counts)).all()
    ):
        raise ValueError("matrix counts must be whole numbers")

    return numeric_counts


def transition_areas(
    matrix: pd.DataFrame,
    pixel_area_m2: float,
) -> pd.DataFrame:
    """Convert a transition-count matrix to areas in square kilometres.

    Parameters
    ----------
    matrix : pandas.DataFrame
        Square transition matrix containing non-negative, whole-number pixel
        counts. Its row and column axes must contain the same unique class
        labels. Axis ordering may differ.
    pixel_area_m2 : float
        Area represented by one raster pixel in square metres.

    Returns
    -------
    pandas.DataFrame
        Floating-point transition-area matrix in square kilometres, with the
        same index, columns, and axis names as ``matrix``.

    Raises
    ------
    TypeError
        If ``matrix`` is not a DataFrame; its values are not real numeric
        counts; or ``pixel_area_m2`` is not a real number.
    ValueError
        If ``matrix`` is empty or not square; either axis contains duplicate
        or missing labels or more than one level; the axes do not contain the
        same class labels; a count is missing, non-finite, negative, or
        fractional; or ``pixel_area_m2`` is non-finite or not greater than
        zero.

    """
    _validate_transition_matrix(matrix)

    if (
        isinstance(pixel_area_m2, (bool, np.bool_))
        or not isinstance(pixel_area_m2, Real)
    ):
        raise TypeError("pixel_area_m2 must be a real number")

    normalised_pixel_area = float(pixel_area_m2)

    if not np.isfinite(normalised_pixel_area):
        raise ValueError("pixel_area_m2 must be finite")

    if normalised_pixel_area <= 0:
        raise ValueError("pixel_area_m2 must be greater than zero")

    square_metres_per_square_kilometre = 1_000_000
    area_scale = (
        normalised_pixel_area / square_metres_per_square_kilometre
    )
    areas = matrix.astype("float64") * area_scale

    if not np.isfinite(areas.to_numpy()).all():
        raise ValueError("calculated transition areas must be finite")

    return areas


def transition_percentages(matrix: pd.DataFrame) -> pd.DataFrame:
    """Calculate row-wise percentages for a transition-count matrix.

    Each row describes how an earlier land-cover class is distributed among
    later classes. Rows containing at least one pixel sum to 100 percent. An
    all-zero row produces ``NaN`` values because its percentages are
    undefined.

    Parameters
    ----------
    matrix : pandas.DataFrame
        Square transition matrix containing non-negative, whole-number pixel
        counts. Its row and column axes must contain the same unique class
        labels. Axis ordering may differ.

    Returns
    -------
    pandas.DataFrame
        Floating-point percentage matrix with the same index, columns, and
        axis names as ``matrix``.

    Raises
    ------
    TypeError
        If ``matrix`` is not a DataFrame or its values are not real numeric
        counts.
    ValueError
        If ``matrix`` is empty or not square; either axis contains duplicate
        or missing labels or more than one level; the axes do not contain the
        same class labels; a count is missing, non-finite, negative, or
        fractional; or a row total cannot be represented as a finite number.

    """
    numeric_counts = _validate_transition_matrix(matrix)

    with np.errstate(over="ignore"):
        row_totals = numeric_counts.sum(axis=1, keepdims=True)

    if not np.isfinite(row_totals).all():
        raise ValueError("matrix row totals must be finite")

    percentages = np.full_like(
        numeric_counts,
        np.nan,
        dtype="float64",
    )
    np.divide(
        numeric_counts,
        row_totals,
        out=percentages,
        where=row_totals != 0,
    )
    percentages *= 100

    return pd.DataFrame(
        percentages,
        index=matrix.index.copy(),
        columns=matrix.columns.copy(),
    )


def summarize_transitions(area_matrix: pd.DataFrame) -> pd.DataFrame:
    """Summarize persistence, gain, and loss by land-cover class.

    Parameters
    ----------
    area_matrix : pandas.DataFrame
        Transition-area matrix in square kilometres, normally returned by
        ``transition_areas``. Rows represent earlier classes and columns
        represent later classes. The axes may contain the classes in
        different orders.

    Returns
    -------
    pandas.DataFrame
        Summary indexed like ``area_matrix`` with the columns
        ``earlier_area_km2``, ``later_area_km2``, ``persistence_km2``,
        ``gain_km2``, ``loss_km2``, ``net_change_km2``, and
        ``total_change_km2``.

    Raises
    ------
    TypeError
        If ``area_matrix`` is not a DataFrame or its values are not real
        numeric areas.
    ValueError
        If ``area_matrix`` is empty or not square; either axis contains
        duplicate or missing labels or more than one level; the axes do not
        contain the same class labels; an area is missing, non-finite, or
        negative; or a calculated total is non-finite.

    """
    numeric_areas = _validate_transition_matrix(
        area_matrix,
        require_whole_numbers=False,
    )

    aligned_column_positions = area_matrix.columns.get_indexer(
        area_matrix.index
    )
    label_aligned_areas = numeric_areas[:, aligned_column_positions]

    with np.errstate(over="ignore", invalid="ignore"):
        earlier_area = numeric_areas.sum(axis=1)
        later_area = label_aligned_areas.sum(axis=0)
        persistence = np.diag(label_aligned_areas)
        loss = earlier_area - persistence
        gain = later_area - persistence
        net_change = gain - loss
        total_change = gain + loss

    summary_values = np.column_stack(
        (
            earlier_area,
            later_area,
            persistence,
            gain,
            loss,
            net_change,
            total_change,
        )
    )

    if not np.isfinite(summary_values).all():
        raise ValueError("calculated transition summary must be finite")

    return pd.DataFrame(
        summary_values,
        index=area_matrix.index.copy(),
        columns=[
            "earlier_area_km2",
            "later_area_km2",
            "persistence_km2",
            "gain_km2",
            "loss_km2",
            "net_change_km2",
            "total_change_km2",
        ],
    )
