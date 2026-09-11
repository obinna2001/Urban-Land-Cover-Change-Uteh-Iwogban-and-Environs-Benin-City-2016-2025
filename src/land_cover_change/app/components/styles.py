from pathlib import Path

import streamlit as st

ROOT: Path = Path(__file__).resolve().parents[1]
CSS_STYLE_FILE: Path = ROOT / "assets" / "styles" / "app.css"

def load_app_style() -> None:
    """Load the application shared CSS stylesheet"""
    if not CSS_STYLE_FILE.is_file():
        raise FileNotFoundError(
            f"Custom CSS stylesheet not found: {CSS_STYLE_FILE!r}"
        )

    st.html(CSS_STYLE_FILE)