import streamlit as st

st.html(
    """
    <style>
    [data-testid="stMarkdownContainer"] p {
        text-align: justify;
    }
    </style>
    """
)

st.title(
    "Urban Land Cover Change: Uteh/Iwogban and Environs"
)
st.caption(
    "Exploring land-cover patterns and change in Benin City, "
    "Edo State, Nigeria (2016–2025)"
)

st.header("Introduction")
st.write(
    "This project examines and quantifies land-cover change in part of Umagbae South Ward, " \
    "Uhunmwonde Local Government Area of Edo State, Nigeria. "
    "The results provide evidence of observed spatial change, but they should not " \
    "be interpreted as proving that every change was caused exclusively by urbanisation. "

    "This project is also a personal inquiry. Having spent much of the past "
    "decade in and around the study area, I wanted to understand and communicate how its landscape has changed over time."
)
st.write(
    "The analysis compares Dynamic World land-cover maps for 2016, 2020 and "
    "2025. Because the selected imagery represents January and February, "
    "seasonally responsive classes—particularly water, grass, crops, flooded "
    "vegetation, and shrub and scrub—should be interpreted in relation to that "
    "observation period."
)

st.header("Study area")
st.write(
    "The study area encompasses approximately **57.64 km²** within Umagbae "
    "South Ward, Uhunmwonde Local Government Area, Edo State. It includes Uteh, "
    "Iwogban and surrounding parts of Akiuwa, Edosowan and Iguenan, extending "
    "from **6.368957° N to 6.454160° N** and **5.638733° E to 5.733318° E**. "
    "Located northeast of Benin City, the area captures a peri-urban landscape "
    "where settlement expansion, agriculture and remnant vegetation coexist. "
    "This combination makes it well suited for examining land-cover change "
    "between 2016 and 2025."
)
st.info(
    "The AOI area was calculated from the project boundary after projection to "
    "EPSG:32631; the coordinates describe its geographic bounds."
)

st.subheader("Climate and vegetation")
st.write(
    "The study area has a tropical rainforest climate shaped strongly by the "
    "West African Monsoon. The rainy season generally extends from late March "
    "to early November and has a double rainfall peak. The dry season runs from "
    "early November to late March and includes periods influenced by the dry, "
    "dust-laden Harmattan winds from the northeast. Regional meteorological "
    "baselines indicate a mean annual maximum temperature of 31.9 °C, a mean "
    "minimum temperature of 22.2 °C, and relative humidity above 50%."
)
st.write(
    "Its natural vegetation belongs to the lowland rainforest belt. Urban "
    "expansion, real-estate development and shifting cultivation have reshaped "
    "the landscape into a mosaic of secondary regrowth forest, oil-palm "
    "clusters, active food-crop farmland and expanding built-up areas."
)

st.subheader("Socioeconomic context")
st.write(
    "The area is populated predominantly by Edo-speaking communities alongside "
    "migrant farming populations. Subsistence and small-scale commercial "
    "agriculture form an important part of the local economy. Major crops "
    "include cassava (*Manihot esculenta*), yams (*Dioscorea* spp.), maize, "
    "plantain and local vegetables, together with cash crops such as oil palm "
    "and rubber. Its position along transport routes leading out of Benin City "
    "also supports real-estate activity, sand mining and petty trading."
)

st.header("Data sources")
st.markdown(
    """
**Administrative boundaries — [GRID3 Nigeria Operational Wards v1.0](https://data.grid3.org/datasets/GRID3::grid3-nga-operational-wards-v1-0/about)**

The GRID3 ward-level boundary dataset was used to identify the administrative
location of the study area and provide the spatial reference for preparing its
boundary.

**Land use and land cover — [Dynamic World V1](https://dynamicworld.app/)**

The land-cover maps were obtained from Dynamic World V1, a global near-real-time
dataset produced by Google in partnership with the National Geographic Society
and the World Resources Institute. Dynamic World is derived from Sentinel-2
Level-1C imagery and has been available since June 2015.

Each valid pixel receives probabilities for nine land-cover classes: water,
trees, grass, flooded vegetation, crops, shrub and scrub, built area, bare ground,
and snow and ice. The class with the highest probability is recorded in the
categorical `label` band used in this analysis.
"""
)

with st.expander("Dynamic World technical details"):
    st.markdown(
        """
- **Spatial resolution:** 10 metres
- **Spectral basis:** Sentinel-2 bands B2, B3, B4, B5, B6, B7, B8, B11 and B12
- **Output:** Nine probability bands and one categorical label band

Further technical information is available in the
[Google Earth Engine data catalogue](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1)
and the
[Dynamic World publication](https://www.nature.com/articles/s41597-022-01307-4).
"""
    )

st.markdown(
    """
**Data access and export — [Google Earth Engine script](https://code.earthengine.google.com/ce4354f43bb0776d1be7e5984d8a7b79)**

Google Earth Engine was used to access the Dynamic World collection, select the
study years and area, and export the resulting land-cover maps as GeoTIFF files
for analysis in Python. The linked script documents this acquisition and export
process.
"""
)

st.header("Key findings")
area_column, built_column, trees_column = st.columns(3)

area_column.metric("Study area", "57.64 km²")
built_column.metric(
    "Built area in 2025",
    "36.43 km²",
    "+14.28 km² since 2016",
    delta_color="off",
)
trees_column.metric(
    "Tree cover in 2025",
    "11.76 km²",
    "−19.30 km² since 2016",
    delta_color="off",
)

st.write(
    "The largest mapped class conversion between 2016 and 2020 was "
    "**trees to built area**, covering approximately **3.40 km²**."
)
st.caption(
    "Land-cover areas are derived from classified raster pixels and may not "
    "exactly match the vector AOI area because boundary pixels are discrete."
)

st.subheader("Explore the analysis")
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
