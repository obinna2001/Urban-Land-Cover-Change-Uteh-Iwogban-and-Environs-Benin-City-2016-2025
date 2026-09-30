import streamlit as st

from components.styles import load_app_style

# Configure the shared browser tab and layout before creating any page elements.
st.set_page_config(
    page_title="Urban land-cover change",
    page_icon=":material/map:",
    layout="wide",
)

# Define the pages after applying the shared app configuration.
home_page = st.Page("views/home.py", title="Home", default=True)
map_page = st.Page("views/map.py", title="LULC Map")
area_page = st.Page("views/class_area_analysis.py", title="Area Analysis")
transition_page = st.Page("views/transition_analysis.py", title="Transition Analysis")

page = st.navigation(
    [home_page, map_page, area_page, transition_page],
    position="top",
    expanded=True,
)

# load custom css style
load_app_style()

page.run()

with st.container(key="footer"):
    with st.container(key="footer-content"):
        column_one, column_two, column_three = st.columns(3)

        with column_one:
            st.html("<h2>Navigation</h2>")
            st.page_link("views/home.py", label="Home")
            st.page_link("views/map.py", label="LULC Map")
            st.page_link("views/class_area_analysis.py", label="Area Analysis")
            st.page_link("views/transition_analysis.py", label="Transition Analysis")

        with column_two:
            st.html("<h2>Resources</h2>")
            st.html(
                """
                <nav class="footer-link-list">
                    <a target="_blank"
                        href="https://data.grid3.org/datasets/GRID3::grid3-nga-operational-wards-v1-0/about">
                        Administrative Boundaries
                    </a>
                    <a target="_blank"
                        href="https://dynamicworld.app/">
                        Dynamic World V1
                    </a>
                    <a target="_blank"
                        href="https://code.earthengine.google.com/ce4354f43bb0776d1be7e5984d8a7b79">
                        Google Earth Engine Script
                    </a> 
                </nav>               
                """
            )

        with column_three:
            st.html("<h2>Contact</h2>")
            st.html(
                """
                <nav class="footer-link-list">
                    <a target="_blank"
                        href="mailto:okeyobinna2001@gmail.com">
                        Email
                    </a>
                    <a target="_blank"
                        href="https://github.com/obinna2001">
                        GitHub
                    </a> 
                </nav>               
                """
            )

        st.html(
            "<p>&copy; 2026 Okey Obinna. All rights reserved.</p>" 
        )

