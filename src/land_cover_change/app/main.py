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

with st.container(key="footer"):
    st.html(
        "Developed as a reproducible land-cover change analysis using Python, Google Earth Engine, Dynamic World and Streamlit.",
        unsafe_allow_javascript=True,
    )
# # Keep shared project attribution at the bottom of every page.
# with st.container(key="app_footer", horizontal_alignment="center"):
#     st.caption(
#         "Developed as a reproducible land-cover change analysis using "
#         "Python, Google Earth Engine, Dynamic World and Streamlit."
#     )
