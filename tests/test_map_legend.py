from collections.abc import Mapping

import folium
import pytest

from land_cover_change.app.components.map_legend import (
    build_dynamic_world_legend,
)
from land_cover_change.config.config import DynamicWorldClass


def _class(name: str, colour: str) -> DynamicWorldClass:
    return DynamicWorldClass(name=name, colour=colour)


@pytest.mark.parametrize(
    ("title", "classes", "expected_text"),
    [
        pytest.param(
            "Dynamic World classes",
            {1: _class("trees", "#397D49"), 0: _class("water", "#419BDF")},
            ["Dynamic World classes", "water", "trees"],
            id="sorted-registry",
        ),
        pytest.param(
            "Classes <2025>",
            {0: _class("water <script>", "#419BDF")},
            ["Classes &lt;2025&gt;", "water &lt;script&gt;"],
            id="escaped-content",
        ),
    ],
)
def test_build_dynamic_world_legend_renders_registry_entries(
    title: str,
    classes: Mapping[int, DynamicWorldClass],
    expected_text: list[str],
) -> None:
    map_ = folium.Map(location=[6.4, 5.7], tiles="OpenStreetMap")
    build_dynamic_world_legend(classes, title=title).add_to(map_)

    rendered_html = map_.get_root().render()

    for text in expected_text:
        assert text in rendered_html

    if set(classes) == {0, 1}:
        assert rendered_html.index("water") < rendered_html.index("trees")

    assert "water <script>" not in rendered_html
    assert "Classes <2025>" not in rendered_html


@pytest.mark.parametrize(
    ("classes", "title", "error_type", "error_match"),
    [
        pytest.param(
            [],
            "Classes",
            TypeError,
            "classes must be a mapping",
            id="non-mapping-registry",
        ),
        pytest.param(
            {},
            "Classes",
            ValueError,
            "classes cannot be empty",
            id="empty-registry",
        ),
        pytest.param(
            {"0": _class("water", "#419BDF")},
            "Classes",
            TypeError,
            "class values must be integers",
            id="non-integer-class-value",
        ),
        pytest.param(
            {0: "water"},
            "Classes",
            TypeError,
            "must be DynamicWorldClass",
            id="invalid-class-definition",
        ),
        pytest.param(
            {0: _class("water", "blue")},
            "Classes",
            ValueError,
            "Invalid hexadecimal colour",
            id="invalid-class-colour",
        ),
        pytest.param(
            {0: _class("water", "#419BDF")},
            2025,
            TypeError,
            "title must be a string",
            id="non-string-title",
        ),
        pytest.param(
            {0: _class("water", "#419BDF")},
            "   ",
            ValueError,
            "title cannot be empty",
            id="empty-title",
        ),
    ],
)
def test_build_dynamic_world_legend_rejects_invalid_input(
    classes: object,
    title: object,
    error_type: type[Exception],
    error_match: str,
) -> None:
    with pytest.raises(error_type, match=error_match):
        build_dynamic_world_legend(  # type: ignore[arg-type]
            classes,
            title=title,
        )
