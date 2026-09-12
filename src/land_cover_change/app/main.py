import streamlit as st

from components.styles import load_app_style

# Configure the shared browser tab and layout before creating any page elements.
st.set_page_config(
    page_title="Urban land-cover change",
    page_icon=":material/map:",
    layout="wide",
)



# Define the pages after applying the shared app configuration.
home_page = st.Page(
    "views/home.py", title="Home", icon=":material/home:", default=True
)
map_page = st.Page("views/map.py", title="LULC map", icon=":material/map:")
area_page = st.Page(
    "views/class_area_analysis.py",
    title="Class area analysis",
    icon=":material/analytics:",
)
transition_page = st.Page(
    "views/transition_analysis.py",
    title="Class transition analysis",
    icon=":material/moving:",
)

page = st.navigation(
    [home_page, map_page, area_page, transition_page],
    position="sidebar",
    expanded=True,
)

# load custom css style
load_app_style()

page.run()

st.html("<h2>Explore the analysis</h2>")
with st.container(horizontal=True):
    st.page_link("views/map.py", label="LULC map", icon=":material/map:")
    st.page_link(
        "views/class_area_analysis.py",
        label="Class area analysis",
        icon=":material/analytics:",
    )
    st.page_link(
        "views/transition_analysis.py",
        label="Transition analysis",
        icon=":material/moving:",
    )


with st.container(key="footer"):
    column_one, column_two, column_three = st.columns(3)

    with column_one:
        st.html("<h2>Navigation</h2>")
        st.page_link("view/map.py", label="LULC map")
        st.page_link("views/class_area_analysis.py", label="Class area analysis")
        st.page_link("views/transition_analysis.py", label="Transition analysis")

    with column_two:
        st.html("<h2>Resource</h2>")
        st.markdown(
            """
            <a href=https://data.grid3.org/datasets/GRID3::grid3-nga-operational-wards-v1-0/about>Administrative Boundaries</a>
            """
        )
        st.markdown(
            """
            <a href=https://dynamicworld.app/>Dynamic World V1</a>
            """
        )
        st.markdown(
            """
            <a href=https://code.earthengine.google.com/ce4354f43bb0776d1be7e5984d8a7b79>Google Earth Engine Script</a>
            """
        )

    with column_three:
        st.html("<h2>Contact</h2")
        st.markdown("<a href=https://okeyobinna2001@gmail.com>Email</a>")
        st.markdown("<a href=https://github.com/obinna2001>GitHub</a>")

    st.html(
        "<p>&copy; 2026 Okey Obinna. All rights reserved.</p>" 
    )

