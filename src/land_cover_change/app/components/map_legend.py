from collections.abc import Mapping
from html import escape
import re

from branca.element import MacroElement, Template

from land_cover_change.config.config import DynamicWorldClass


_HEX_COLOUR_PATTERN = re.compile(r"#[0-9a-fA-F]{6}")


def build_dynamic_world_legend(
    classes: Mapping[int, DynamicWorldClass],
    title: str = "Dynamic World classes",
) -> MacroElement:
    """Build a categorical Folium legend from the Dynamic World registry.

    Parameters
    ----------
    classes : collections.abc.Mapping[int, DynamicWorldClass]
        Dynamic World definitions keyed by their raster class values.
    title : str, default "Dynamic World classes"
        Heading displayed above the class entries.

    Returns
    -------
    branca.element.MacroElement
        Legend that can be added to a Folium map with ``legend.add_to(map_)``.

    Raises
    ------
    TypeError
        If ``classes`` is not a mapping, a class key is not an integer, a
        class definition is not a ``DynamicWorldClass``, or ``title`` is not
        a string.
    ValueError
        If ``classes`` is empty, ``title`` is empty, or a class colour is not
        a six-digit hexadecimal colour.

    """
    if not isinstance(classes, Mapping):
        raise TypeError("classes must be a mapping of class values to definitions")

    if not classes:
        raise ValueError("classes cannot be empty")

    if not isinstance(title, str):
        raise TypeError("title must be a string")

    if not title.strip():
        raise ValueError("title cannot be empty")

    legend_items: list[str] = []

    for class_value, class_definition in sorted(classes.items()):
        if isinstance(class_value, bool) or not isinstance(class_value, int):
            raise TypeError("Dynamic World class values must be integers")

        if not isinstance(class_definition, DynamicWorldClass):
            raise TypeError(
                "Dynamic World class definitions must be DynamicWorldClass "
                "instances"
            )

        if not _HEX_COLOUR_PATTERN.fullmatch(class_definition.colour):
            raise ValueError(
                f"Invalid hexadecimal colour {class_definition.colour!r} "
                f"for class {class_value}"
            )

        legend_items.append(
            f'<li data-class-value="{class_value}">'
            '<span class="dynamic-world-legend__swatch" '
            f'style="background-color: {class_definition.colour};"></span>'
            '<span class="dynamic-world-legend__label">'
            f"{escape(class_definition.name)}"
            "</span>"
            "</li>"
        )

    legend = MacroElement()
    legend._name = "DynamicWorldLegend"
    legend._template = Template(
        """
        {% macro html(this, kwargs) %}
        <div id="{{ this.get_name() }}"
             class="dynamic-world-legend"
             role="group"
             aria-label="""
        + escape(title, quote=True)
        + """">
          <div class="dynamic-world-legend__title">"""
        + escape(title)
        + """</div>
          <ul>"""
        + "".join(legend_items)
        + """</ul>
        </div>
        <style>
          .dynamic-world-legend {
            position: fixed;
            right: 20px;
            bottom: 30px;
            z-index: 9999;
            min-width: 190px;
            padding: 12px 14px;
            border: 1px solid rgba(0, 0, 0, 0.2);
            border-radius: 6px;
            background: rgba(255, 255, 255, 0.94);
            box-shadow: 0 1px 5px rgba(0, 0, 0, 0.25);
            color: #222;
            font: 13px/1.35 Arial, Helvetica, sans-serif;
          }
          .dynamic-world-legend__title {
            margin-bottom: 8px;
            font-weight: 700;
          }
          .dynamic-world-legend ul {
            margin: 0;
            padding: 0;
            list-style: none;
          }
          .dynamic-world-legend li {
            display: flex;
            align-items: center;
            gap: 8px;
            margin: 4px 0;
          }
          .dynamic-world-legend__swatch {
            width: 14px;
            height: 14px;
            flex: 0 0 14px;
            border: 1px solid rgba(0, 0, 0, 0.35);
          }
          .dynamic-world-legend__label {
            text-transform: capitalize;
          }
        </style>
        {% endmacro %}
        """
    )

    return legend
