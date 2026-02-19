import streamlit as st
import numpy as np
import rasterio
import geopandas as gpd
from rasterio.features import shapes
import folium
from streamlit_folium import st_folium
import pandas as pd
import os
from streamlit_vertical_slider import vertical_slider

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(layout="wide")

# --------------------------------------------------
# STYLE
# --------------------------------------------------
st.markdown("""
<style>
.block-container {
    max-width: 1800px;
    margin: auto;
}

.main-title {
    font-size: 46px;
    font-weight: 700;
}

.sub-title {
    font-size: 22px;
    color: #B00020;
    margin-bottom: 20px;
}

.section-title {
    font-size: 20px;
    font-weight: 600;
    margin-top: 25px;
}

.footer {
    font-size: 16px;
    color: gray;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.image("cerknica_digital_twin/UL_FGG-logoENG-HOR-RGB_color.png", width=280)
st.markdown("<div class='main-title'>Lake Cerknica Digital Twin</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>7-Day Playback & Scenario Simulation</div>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# --------------------------------------------------
# CONSTANTS
# --------------------------------------------------
REF_HEIGHT = 545.417
ARSO_URL = "http://hmljn.arso.gov.si/vode/podatki/amp/H5680_t_7.html"

# --------------------------------------------------
# LOAD ARSO DATA
# --------------------------------------------------
@st.cache_data(ttl=600)
def load_arso():
    tables = pd.read_html(ARSO_URL)
    df = None
    for t in tables:
        cols = [str(c).lower() for c in t.columns]
        if any("datum" in c for c in cols) and any("cm" in c for c in cols):
            df = t
            break

    df.columns = [str(c).strip() for c in df.columns]
    date_col = [c for c in df.columns if "Datum" in c][0]
    cm_col = [c for c in df.columns if "cm" in c.lower()][0]

    df["Datetime"] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")
    df["cm"] = pd.to_numeric(df[cm_col], errors="coerce")
    df = df.dropna(subset=["Datetime", "cm"]).sort_values("Datetime")

    return df

df_arso = load_arso()

# --------------------------------------------------
# LOAD DEM + AOI
# --------------------------------------------------
@st.cache_data
def load_dem():
    with rasterio.open("cerknica_digital_twin/DMR.tif") as src:
        dem = src.read(1).astype(np.float32)
        transform_aff = src.transform
        crs = src.crs
        pixel_size = src.res[0]
    return dem, transform_aff, crs, pixel_size

dem, transform_aff, crs, pixel_size = load_dem()
pixel_area = pixel_size ** 2

aoi = gpd.read_file("cerknica_digital_twin/aoi.gpkg")

# --------------------------------------------------
# PLAYBACK + STATUS PANEL
# --------------------------------------------------
col_slider, col_status = st.columns([1, 2])

with col_slider:
    index = vertical_slider(
        label="Water Level (cm)",
        key="time_slider",
        step=1,
        default_value=len(df_arso)-1,
        min_value=0,
        max_value=len(df_arso)-1,
        height=350
    )

selected_row = df_arso.iloc[index]
selected_cm = selected_row["cm"]
selected_time = selected_row["Datetime"]

# --------------------------------------------------
# RISK CLASSIFICATION
# --------------------------------------------------
def classify_risk(cm):
    if cm <= 346:
        return "Normal"
    elif cm <= 441:
        return "Elevated"
    elif cm <= 521:
        return "Very High"
    else:
        return "Extreme"

risk_class = classify_risk(selected_cm)

risk_colors = {
    "Normal": "#4CAF50",
    "Elevated": "#FFC107",
    "Very High": "#FF5722",
    "Extreme": "#B00020"
}

with col_status:
    st.markdown(f"### {selected_cm:.1f} cm")
    st.caption(selected_time.strftime("%d %b %Y %H:%M"))

    st.markdown(
        f"<div style='font-size:18px;'>"
        f"Status: "
        f"<span style='background-color:{risk_colors[risk_class]}; "
        f"color:white; padding:6px 14px; border-radius:6px;'>"
        f"{risk_class}"
        f"</span>"
        f"</div>",
        unsafe_allow_html=True
    )

# --------------------------------------------------
# RISK LEGEND
# --------------------------------------------------
st.markdown("##### Risk Classification (Reference period 1954–2025)")

st.markdown("""
<div style="display:flex; gap:15px; font-size:14px;">
<span style="background:#4CAF50; color:white; padding:4px 10px; border-radius:4px;">Normal ≤346</span>
<span style="background:#FFC107; padding:4px 10px; border-radius:4px;">346–441</span>
<span style="background:#FF5722; color:white; padding:4px 10px; border-radius:4px;">441–521</span>
<span style="background:#B00020; color:white; padding:4px 10px; border-radius:4px;">>521</span>
</div>
""", unsafe_allow_html=True)

st.caption("Thresholds derived from long-term daily water level observations (1954–2025).")

# --------------------------------------------------
# FLOOD COMPUTATION
# --------------------------------------------------
def compute_flood(cm_value):
    h_abs = REF_HEIGHT + cm_value / 100.0
    water = dem <= h_abs
    return water, h_abs

water_current, h_abs = compute_flood(selected_cm)

# --------------------------------------------------
# MASK TO GDF FUNCTION
# --------------------------------------------------
def mask_to_gdf(mask):
    if np.sum(mask) == 0:
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

    results = (
        {"properties": {"water": v}, "geometry": s}
        for (s, v) in shapes(mask.astype(np.uint8), transform=transform_aff)
        if v == 1
    )

    features = list(results)
    if len(features) == 0:
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

    gdf_temp = gpd.GeoDataFrame.from_features(features, crs=crs)
    gdf_temp = gpd.overlay(gdf_temp, aoi, how="intersection")
    gdf_temp = gdf_temp.to_crs(epsg=4326)

    return gdf_temp

gdf_current = mask_to_gdf(water_current)
aoi_web = aoi.to_crs(epsg=4326)
bounds = aoi_web.total_bounds

# --------------------------------------------------
# SCENARIO
# --------------------------------------------------
scenario_option = st.radio(
    "Scenario Simulation:",
    ["+20 cm", "-30 cm (Dry scenario)"],
    horizontal=True
)

if scenario_option == "+20 cm":
    scenario_cm = selected_cm + 20
else:
    scenario_cm = selected_cm - 30

water_scenario, _ = compute_flood(scenario_cm)

additional_water = water_scenario & (~water_current)
exposed_area = water_current & (~water_scenario)

gdf_additional = mask_to_gdf(additional_water)
gdf_exposed = mask_to_gdf(exposed_area)

# --------------------------------------------------
# MAPS SIDE BY SIDE
# --------------------------------------------------
col_map1, col_map2 = st.columns(2)

# --- CURRENT MAP
with col_map1:
    st.markdown("#### Current Flood Extent")

    m = folium.Map(tiles=None)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
              "World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri"
    ).add_to(m)

    if not gdf_current.empty:
        folium.GeoJson(
            gdf_current,
            style_function=lambda x: {
                "fillColor": "#1f77b4",
                "color": "#1f77b4",
                "weight": 1,
                "fillOpacity": 0.6
            }
        ).add_to(m)

    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
    st_folium(m, use_container_width=True, height=550)

# --- SCENARIO MAP
with col_map2:
    st.markdown("#### Scenario Simulation")

    m2 = folium.Map(tiles=None)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
              "World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri"
    ).add_to(m2)

    # Base current layer
    if not gdf_current.empty:
        folium.GeoJson(
            gdf_current,
            style_function=lambda x: {
                "fillColor": "#1f77b4",
                "color": "#1f77b4",
                "weight": 1,
                "fillOpacity": 0.4
            }
        ).add_to(m2)

    # Additional flood
    if scenario_option == "+20 cm" and not gdf_additional.empty:
        folium.GeoJson(
            gdf_additional,
            style_function=lambda x: {
                "fillColor": "#ff0000",
                "color": "#ff0000",
                "weight": 2,
                "fillOpacity": 0.6
            }
        ).add_to(m2)

    # Exposed area
    if scenario_option != "+20 cm" and not gdf_exposed.empty:
        folium.GeoJson(
            gdf_exposed,
            style_function=lambda x: {
                "fillColor": "#ff9900",
                "color": "#ff9900",
                "weight": 2,
                "fillOpacity": 0.6
            }
        ).add_to(m2)

    m2.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
    st_folium(m2, use_container_width=True, height=550)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.markdown("<hr>", unsafe_allow_html=True)

col_f1, col_f2 = st.columns(2)

with col_f1:
    st.markdown(
        "<div class='footer'>"
        "Authors: Ana Potočnik Buhvald, Krištof Oštir, "
        "Neja Flogie, Klemen Kozmus Trajkovski"
        "</div>",
        unsafe_allow_html=True
    )

with col_f2:
    st.markdown(
        "<div style='text-align:right;' class='footer'>© UL FGG, 2026</div>",
        unsafe_allow_html=True
    )
