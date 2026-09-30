import streamlit as st


with st.container(key="title-section"):
    with st.container(key="title-content"):
        st.markdown(
            """
                <p class="hero-eyebrow">
                    2016–2025 · BENIN CITY, NIGERIA
                </p>

                <h1 class="hero-title">
                    How is the landscape around Uteh and Iwogban changing?
                </h1>
                
                <p class="hero-lead">
                    An interactive study of land-cover patterns across a 57.64 km² peri-urban landscape, 
                    using Dynamic World imagery 2016, 2020 and 2025
                </p>
            """,
            unsafe_allow_html=True,
        )

with st.container(key="main-content"):
    st.markdown(
        """
            <p class="important-note">
                This project began as a personal inquiry into the extent to which different land-cover classes have changed 
                across Uteh/Iwogban and its environs. Having spent much of the past decade in and around the study area, 
                I wanted to examine these changes systematically and communicate how the landscape has evolved over time.
            </p>   
            <p>
            <span style={font-weight: bold}>Urban land cover change: Uteh/Iwogban and environs <span> examines and quantifies land-cover change in part of Umagbae South Ward, Uhunmwonde Local Government
            Area of Edo State, Nigeria. The results provide evidence of observed spatial change, but they should not be interpreted 
            as proving that every change was caused exclusively by urbanisation. 
            
            The analysis compares Dynamic World land-cover maps for 2016, 2020 and 2025. Because the selected imagery represents January and February, 
            seasonally responsive classes—particularly water, grass, crops, flooded vegetation, and shrub and scrub—should 
            be interpreted in relation to that observation period.
            </p>
        """, 
        unsafe_allow_html=True
    )

    st.html("<h2>Study Area</h2>")
    st.markdown(
        """
        <p> 
            The study area covers approximately 57.64 km² within Umagbae South Ward, Uhunmwonde Local Government Area, 
            Edo State, Nigeria. It includes Uteh, Iwogban and surrounding parts of Akiuwa, Edosowan and Iguenan. 
            Its geographic extent ranges from 6.368957° N to 6.454160° N and from 5.638733° E to 5.733318° E.
        </p>    
        <p> 
            Located northeast of Benin City, the study area represents a peri-urban landscape where expanding settlements,
            agricultural land and remnant vegetation coexist. This combination makes it well suited for examining land-cover
            patterns and changes between 2016 and 2025.
        </p>
        <p>
            The study-area boundary was projected to WGS 84 / UTM Zone 31N (EPSG:32631) before its area was calculated. 
            The coordinates above represent its geographic extent in latitude and longitude.
        </p>
        """,
        unsafe_allow_html=True
    )

    st.html("<h2>Climate and Vegetation</h2>")
    st.markdown(
        """The study area has a tropical rainforest climate shaped strongly by the West African Monsoon. 
        The rainy season generally extends from late March to early November and has a double rainfall peak. 
        The dry season runs from early November to late March and includes periods influenced by the dry, 
        dust-laden Harmattan winds from the northeast. Regional meteorological baselines indicate a mean annual maximum 
        temperature of 31.9 °C, a mean minimum temperature of 22.2 °C, and relative humidity above 50%. <br><br> 
        Its natural vegetation belongs to the lowland rainforest belt. Urban expansion, real-estate development and shifting
        cultivation have reshaped the landscape into a mosaic of secondary regrowth forest, oil-palm clusters, active food-crop 
        farmland and expanding built-up areas.
        """,
        unsafe_allow_html=True
    )

    st.html("<h2>Socioeconomic Activity</h2>")
    st.markdown(
        """
        The area is populated predominantly by Edo-speaking communities alongside migrant farming populations. 
        Subsistence and small-scale commercial agriculture form an important part of the local economy. 
        Major crops include cassava (*Manihot esculenta*), yams (*Dioscorea* spp.), maize, plantain and local vegetables, 
        together with cash crops such as oil palm and rubber. Its position along transport routes leading out of Benin City
        also supports real-estate activity, sand mining and petty trading.
        """
    )

    st.html("<h2>Data sources</h2>")
    st.markdown(
        """
        Administrative boundaries — 
        <a target="_blank" 
            href="https://data.grid3.org/datasets/GRID3::grid3-nga-operational-wards-v1-0/about">
            GRID3 Nigeria Operational Wards v1.0
        </a>

        The GRID3 ward-level boundary dataset was used to identify the administrative
        location of the study area and provide the spatial reference for preparing its
        boundary.

        Land use and land cover — 
        <a target="_blank" 
            href="https://dynamicworld.app/">
            Dynamic World V1
        </a>

        The land-cover maps were obtained from Dynamic World V1, a global near-real-time
        dataset produced by Google in partnership with the National Geographic Society
        and the World Resources Institute. Dynamic World is derived from Sentinel-2
        Level-1C imagery and has been available since June 2015.

        Each valid pixel receives probabilities for nine land-cover classes: water,
        trees, grass, flooded vegetation, crops, shrub and scrub, built area, bare ground,
        and snow and ice. The class with the highest probability is recorded in the
        categorical `label` band used in this analysis.
        """,
        unsafe_allow_html=True
    )

    with st.expander("Dynamic World technical details"):
        st.markdown(
            """
            - **Spatial resolution:** 10 metres
            - **Spectral basis:** Sentinel-2 bands B2, B3, B4, B5, B6, B7, B8, B11 and B12
            - **Output:** Nine probability bands and one categorical label band

            Further technical information is available in the
            <a target="_blank" 
                href="https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1">
                Google Earth Engine data catalogue
            </a>
            and the
            <a target="_blank" 
                href="https://www.nature.com/articles/s41597-022-01307-4">
                Dynamic World publication
            </a>.
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            Data access and export — 
            <a target="_blank"
                href="https://code.earthengine.google.com/ce4354f43bb0776d1be7e5984d8a7b79">
                Google Earth Engine script
            </a>

            Google Earth Engine was used to access the Dynamic World collection, select the
            study years and area, and export the resulting land-cover maps as GeoTIFF files
            for analysis in Python. The linked script documents this acquisition and export
            process.
            """,
            unsafe_allow_html=True
        )

    
    st.html("<h2>Key findings</h2>")
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

    st.markdown(
        """The largest mapped class conversion between 2016 and 2020 was **trees to built area**, covering approximately **3.40 km²**."""
    )
    st.caption(
        "Land-cover areas are derived from classified raster pixels and may not "
        "exactly match the vector AOI area because boundary pixels are discrete."
    )
