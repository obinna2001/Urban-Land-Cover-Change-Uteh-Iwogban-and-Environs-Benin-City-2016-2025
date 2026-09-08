import streamlit as st

# define the pages with title
home_page = st.Page("views/home.py", title="Home", icon=":material/home:", default=True)
map_page = st.Page("views/map.py", title="LULC Map", icon=":material/map:")
area_page = st.Page("views/class_area_analysis.py", title="Class Area analysis", icon=":material/analytics:")
transition_page = st.Page("views/transition_analysis.py", title="Class Transition analysis", icon=":material/moving:")


pages = st.navigation([home_page, map_page, area_page, transition_page], position='top')

# 3. Configure common page elements and run
st.set_page_config(page_title="My Multi-Page App", layout="centered")
pages.run()