import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest

from land_cover_change.services.transition import (
    summarize_transitions,
    transition_areas,
    transition_percentages,
)


@pytest.mark.parametrize(
    ("matrix", "pixel_area_m2", "expected"),
    [
        pytest.param(
            pd.DataFrame(
                [[2, 1], [0, 3]],
                index=pd.Index([0, 1], name="from_class"),
                columns=pd.Index([0, 1], name="to_class"),
            ),
            100.0,
            pd.DataFrame(
                [[0.0002, 0.0001], [0.0, 0.0003]],
                index=pd.Index([0, 1], name="from_class"),
                columns=pd.Index([0, 1], name="to_class"),
            ),
            id="integer-counts",
        ),
        pytest.param(
            pd.DataFrame(
                [[1.0, 4.0], [2.0, 0.0]],
                index=pd.Index([1, 0], name="earlier"),
                columns=pd.Index([0, 1], name="later"),
            ),
            np.int64(900),
            pd.DataFrame(
                [[0.0009, 0.0036], [0.0018, 0.0]],
                index=pd.Index([1, 0], name="earlier"),
                columns=pd.Index([0, 1], name="later"),
            ),
            id="whole-float-counts-and-different-axis-order",
        ),
    ],
)
def test_transition_areas_converts_counts_and_preserves_axes(
    matrix: pd.DataFrame,
    pixel_area_m2: float,
    expected: pd.DataFrame,
) -> None:
    original = matrix.copy(deep=True)

    result = transition_areas(matrix, pixel_area_m2)

    assert_frame_equal(result, expected)
    assert_frame_equal(matrix, original)
    assert result is not matrix


@pytest.mark.parametrize(
    ("matrix", "pixel_area_m2", "error_type", "error_match"),
    [
        pytest.param(
            [[1]],
            100.0,
            TypeError,
            "must be a pandas DataFrame",
            id="non-dataframe",
        ),
        pytest.param(
            pd.DataFrame(),
            100.0,
            ValueError,
            "cannot be empty",
            id="empty-matrix",
        ),
        pytest.param(
            pd.DataFrame([[1, 2, 3], [4, 5, 6]]),
            100.0,
            ValueError,
            "must be square",
            id="non-square-matrix",
        ),
        pytest.param(
            pd.DataFrame(
                [[1, 2], [3, 4]],
                index=pd.MultiIndex.from_tuples([(0, "a"), (1, "b")]),
            ),
            100.0,
            ValueError,
            "must each contain exactly one level",
            id="multi-level-index",
        ),
        pytest.param(
            pd.DataFrame(
                [[1, 2], [3, 4]],
                columns=pd.MultiIndex.from_tuples([(0, "a"), (1, "b")]),
            ),
            100.0,
            ValueError,
            "must each contain exactly one level",
            id="multi-level-columns",
        ),
        pytest.param(
            pd.DataFrame([[1, 2], [3, 4]], index=[0, 0]),
            100.0,
            ValueError,
            "index class labels must be unique",
            id="duplicate-index-labels",
        ),
        pytest.param(
            pd.DataFrame([[1, 2], [3, 4]], columns=[0, 0]),
            100.0,
            ValueError,
            "column class labels must be unique",
            id="duplicate-column-labels",
        ),
        pytest.param(
            pd.DataFrame([[1, 2], [3, 4]], index=[0, np.nan]),
            100.0,
            ValueError,
            "index cannot contain missing",
            id="missing-index-label",
        ),
        pytest.param(
            pd.DataFrame([[1, 2], [3, 4]], columns=[0, np.nan]),
            100.0,
            ValueError,
            "columns cannot contain missing",
            id="missing-column-label",
        ),
        pytest.param(
            pd.DataFrame(
                [[1, 2], [3, 4]],
                index=[0, 1],
                columns=[0, 2],
            ),
            100.0,
            ValueError,
            "same class labels",
            id="different-axis-labels",
        ),
        pytest.param(
            pd.DataFrame([[1, "2"], [3, 4]]),
            100.0,
            TypeError,
            "real numeric counts",
            id="non-numeric-count",
        ),
        pytest.param(
            pd.DataFrame([[True, False], [False, True]]),
            100.0,
            TypeError,
            "real numeric counts",
            id="boolean-count",
        ),
        pytest.param(
            pd.DataFrame([[1 + 0j, 2], [3, 4]]),
            100.0,
            TypeError,
            "real numeric counts",
            id="complex-count",
        ),
        pytest.param(
            pd.DataFrame([[1, np.nan], [3, 4]]),
            100.0,
            ValueError,
            "finite and cannot be missing",
            id="missing-count",
        ),
        pytest.param(
            pd.DataFrame([[1, np.inf], [3, 4]]),
            100.0,
            ValueError,
            "finite and cannot be missing",
            id="infinite-count",
        ),
        pytest.param(
            pd.DataFrame([[1, -1], [3, 4]]),
            100.0,
            ValueError,
            "cannot be negative",
            id="negative-count",
        ),
        pytest.param(
            pd.DataFrame([[1, 1.5], [3, 4]]),
            100.0,
            ValueError,
            "must be whole numbers",
            id="fractional-count",
        ),
        pytest.param(
            pd.DataFrame([[1]]),
            True,
            TypeError,
            "must be a real number",
            id="boolean-pixel-area",
        ),
        pytest.param(
            pd.DataFrame([[1]]),
            "100",
            TypeError,
            "must be a real number",
            id="non-numeric-pixel-area",
        ),
        pytest.param(
            pd.DataFrame([[1]]),
            np.nan,
            ValueError,
            "must be finite",
            id="nan-pixel-area",
        ),
        pytest.param(
            pd.DataFrame([[1]]),
            np.inf,
            ValueError,
            "must be finite",
            id="infinite-pixel-area",
        ),
        pytest.param(
            pd.DataFrame([[1]]),
            0.0,
            ValueError,
            "greater than zero",
            id="zero-pixel-area",
        ),
        pytest.param(
            pd.DataFrame([[1]]),
            -100.0,
            ValueError,
            "greater than zero",
            id="negative-pixel-area",
        ),
    ],
)

def test_transition_areas_rejects_invalid_input(
    matrix: object,
    pixel_area_m2: object,
    error_type: type[Exception],
    error_match: str,
) -> None:
    with pytest.raises(error_type, match=error_match):
        transition_areas(  
            matrix,   # type: ignore
            pixel_area_m2,  # type: ignore
        ) 


@pytest.mark.parametrize(
    ("matrix", "expected"),
    [
        pytest.param(
            pd.DataFrame(
                [[6, 3, 1], [0, 2, 2], [0, 0, 0]],
                index=pd.Index([0, 1, 2], name="from_class"),
                columns=pd.Index([0, 1, 2], name="to_class"),
            ),
            pd.DataFrame(
                [
                    [60.0, 30.0, 10.0],
                    [0.0, 50.0, 50.0],
                    [np.nan, np.nan, np.nan],
                ],
                index=pd.Index([0, 1, 2], name="from_class"),
                columns=pd.Index([0, 1, 2], name="to_class"),
            ),
            id="integer-counts-with-empty-class",
        ),
        pytest.param(
            pd.DataFrame(
                [[1.0, 3.0], [1.0, 1.0]],
                index=pd.Index([1, 0], name="earlier"),
                columns=pd.Index([0, 1], name="later"),
            ),
            pd.DataFrame(
                [[25.0, 75.0], [50.0, 50.0]],
                index=pd.Index([1, 0], name="earlier"),
                columns=pd.Index([0, 1], name="later"),
            ),
            id="whole-float-counts-and-different-axis-order",
        ),
    ],
)
def test_transition_percentages_returns_row_wise_percentages(
    matrix: pd.DataFrame,
    expected: pd.DataFrame,
) -> None:
    original = matrix.copy(deep=True)

    result = transition_percentages(matrix)

    assert_frame_equal(result, expected)
    assert_frame_equal(matrix, original)
    assert result is not matrix
    np.testing.assert_allclose(
        result.dropna(how="all").sum(axis=1).to_numpy(),
        100.0,
    )


@pytest.mark.parametrize(
    ("matrix", "error_type", "error_match"),
    [
        pytest.param(
            [[1]],
            TypeError,
            "must be a pandas DataFrame",
            id="non-dataframe",
        ),
        pytest.param(
            pd.DataFrame(),
            ValueError,
            "cannot be empty",
            id="empty-matrix",
        ),
        pytest.param(
            pd.DataFrame([[1, 2, 3], [4, 5, 6]]),
            ValueError,
            "must be square",
            id="non-square-matrix",
        ),
        pytest.param(
            pd.DataFrame(
                [[1, 2], [3, 4]],
                index=[0, 1],
                columns=[0, 2],
            ),
            ValueError,
            "same class labels",
            id="different-axis-labels",
        ),
        pytest.param(
            pd.DataFrame([[1, "2"], [3, 4]]),
            TypeError,
            "real numeric counts",
            id="non-numeric-count",
        ),
        pytest.param(
            pd.DataFrame([[True, False], [False, True]]),
            TypeError,
            "real numeric counts",
            id="boolean-count",
        ),
        pytest.param(
            pd.DataFrame([[1, np.nan], [3, 4]]),
            ValueError,
            "finite and cannot be missing",
            id="missing-count",
        ),
        pytest.param(
            pd.DataFrame([[1, np.inf], [3, 4]]),
            ValueError,
            "finite and cannot be missing",
            id="infinite-count",
        ),
        pytest.param(
            pd.DataFrame([[1, -1], [3, 4]]),
            ValueError,
            "cannot be negative",
            id="negative-count",
        ),
        pytest.param(
            pd.DataFrame([[1, 1.5], [3, 4]]),
            ValueError,
            "must be whole numbers",
            id="fractional-count",
        ),
        pytest.param(
            pd.DataFrame(
                [[np.finfo("float64").max] * 2] * 2,
            ),
            ValueError,
            "row totals must be finite",
            id="overflowing-row-total",
        ),
    ],
)
def test_transition_percentages_rejects_invalid_input(
    matrix: object,
    error_type: type[Exception],
    error_match: str,
) -> None:
    with pytest.raises(error_type, match=error_match):
        transition_percentages(matrix)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("area_matrix", "expected"),
    [
        pytest.param(
            pd.DataFrame(
                [
                    [5.0, 2.0, 0.0],
                    [3.0, 10.0, 0.0],
                    [0.0, 0.0, 0.0],
                ],
                index=pd.Index([0, 1, 2], name="from_class"),
                columns=pd.Index([0, 1, 2], name="to_class"),
            ),
            pd.DataFrame(
                [
                    [7.0, 8.0, 5.0, 3.0, 2.0, 1.0, 5.0],
                    [13.0, 12.0, 10.0, 2.0, 3.0, -1.0, 5.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                ],
                index=pd.Index([0, 1, 2], name="from_class"),
                columns=[
                    "earlier_area_km2",
                    "later_area_km2",
                    "persistence_km2",
                    "gain_km2",
                    "loss_km2",
                    "net_change_km2",
                    "total_change_km2",
                ],
            ),
            id="area-summary-with-empty-class",
        ),
        pytest.param(
            pd.DataFrame(
                [[0.2, 0.5], [1.0, 0.3]],
                index=pd.Index(["trees", "built"], name="earlier"),
                columns=pd.Index(["built", "trees"], name="later"),
            ),
            pd.DataFrame(
                [
                    [0.7, 0.8, 0.5, 0.3, 0.2, 0.1, 0.5],
                    [1.3, 1.2, 1.0, 0.2, 0.3, -0.1, 0.5],
                ],
                index=pd.Index(["trees", "built"], name="earlier"),
                columns=[
                    "earlier_area_km2",
                    "later_area_km2",
                    "persistence_km2",
                    "gain_km2",
                    "loss_km2",
                    "net_change_km2",
                    "total_change_km2",
                ],
            ),
            id="fractional-areas-and-different-axis-order",
        ),
    ],
)
def test_summarize_transitions_returns_class_metrics(
    area_matrix: pd.DataFrame,
    expected: pd.DataFrame,
) -> None:
    original = area_matrix.copy(deep=True)

    result = summarize_transitions(area_matrix)

    assert_frame_equal(result, expected)
    assert_frame_equal(area_matrix, original)
    assert result is not area_matrix


@pytest.mark.parametrize(
    ("area_matrix", "error_type", "error_match"),
    [
        pytest.param(
            [[1.0]],
            TypeError,
            "must be a pandas DataFrame",
            id="non-dataframe",
        ),
        pytest.param(
            pd.DataFrame(),
            ValueError,
            "cannot be empty",
            id="empty-matrix",
        ),
        pytest.param(
            pd.DataFrame([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]),
            ValueError,
            "must be square",
            id="non-square-matrix",
        ),
        pytest.param(
            pd.DataFrame(
                [[1.0, 2.0], [3.0, 4.0]],
                index=[0, 1],
                columns=[0, 2],
            ),
            ValueError,
            "same class labels",
            id="different-axis-labels",
        ),
        pytest.param(
            pd.DataFrame([[1.0, "2"], [3.0, 4.0]]),
            TypeError,
            "real numeric areas",
            id="non-numeric-area",
        ),
        pytest.param(
            pd.DataFrame([[True, False], [False, True]]),
            TypeError,
            "real numeric areas",
            id="boolean-area",
        ),
        pytest.param(
            pd.DataFrame([[1.0, 2.0j], [3.0, 4.0]]),
            TypeError,
            "real numeric areas",
            id="complex-area",
        ),
        pytest.param(
            pd.DataFrame([[1.0, np.nan], [3.0, 4.0]]),
            ValueError,
            "finite and cannot be missing",
            id="missing-area",
        ),
        pytest.param(
            pd.DataFrame([[1.0, np.inf], [3.0, 4.0]]),
            ValueError,
            "finite and cannot be missing",
            id="infinite-area",
        ),
        pytest.param(
            pd.DataFrame([[1.0, -2.0], [3.0, 4.0]]),
            ValueError,
            "cannot be negative",
            id="negative-area",
        ),
        pytest.param(
            pd.DataFrame(
                [[np.finfo("float64").max] * 2] * 2,
            ),
            ValueError,
            "summary must be finite",
            id="overflowing-summary",
        ),
    ],
)
def test_summarize_transitions_rejects_invalid_input(
    area_matrix: object,
    error_type: type[Exception],
    error_match: str,
) -> None:
    with pytest.raises(error_type, match=error_match):
        summarize_transitions(area_matrix)  # type: ignore[arg-type]
