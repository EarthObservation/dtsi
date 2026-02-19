import streamlit as st
import numpy as np
import rasterio
import geopandas as gpd
from rasterio.features import shapes
import folium
from streamlit_folium import st_folium
from streamlit_vertical_slider import vertical_slider

# ------------------------------------
# PAGE CONFIG
# ------------------------------------
st.set_page_config(layout="wide")

# ------------------------------------
# GLOBAL STYLE (TEXT x2, numbers unchanged)
# ------------------------------------
st.markdown("""
<style>

/* Global spacing */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Default text doubled */
html, body, [class*="css"]  {
    font-size: 36px;
}

/* Title */
.main-title {
    font-size: 66px;
    font-weight: 700;
}

.sub-title {
    font-size: 52px;
    font-weight: 600;
    color: #B00020;
    margin-bottom: 30px;
}

/* Section header */
.section-header {
    font-size: 42px;
    font-weight: 600;
    margin-bottom: 15px;
}

/* Metric numbers (UNCHANGED) */
.metric-number {
    font-size: 62px;
    font-weight: 700;
    color: #003366;
}

.metric-unit {
    font-size: 32px;
}

.metric-label {
    font-size: 32px;
}

/* Footer */
.footer {
    font-size: 32px;
    color: #777777;
    margin-top: 50px;
}

</style>
""", unsafe_allow_html=True)



# ------------------------------------
# TITLES
# ------------------------------------
#st.markdown("<div class='main-title'>Intermittent Lake Phenomenon</div>", unsafe_allow_html=True)
#st.markdown("<div class='sub-title'>Lake Cerknica (Slovenia)</div>", unsafe_allow_html=True)

col_title, col_logo = st.columns([5, 2])

with col_title:
    st.markdown(
        "<div class='main-title'>Intermittent Lake Phenomenon</div>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<div class='sub-title'>Lake Cerknica (Slovenia)</div>",
        unsafe_allow_html=True
    )

with col_logo:
    st.image("cerknica_digital_twin/UL_FGG-logoENG-HOR-RGB_color.png", width=840)

# ------------------------------------
# REFERENCE HEIGHT
# ------------------------------------
REF_HEIGHT = 545.417


# ------------------------------------
# LOAD DEM
# ------------------------------------
@st.cache_data
def load_dem():
    with rasterio.open("cerknica_digital_twin/DMR.tif") as src:
        dem = src.read(1).astype(np.float32)
        transform_aff = src.transform
        crs = src.crs
        pixel_size = src.res[0]
    return dem, transform_aff, crs, pixel_size

dem, transform_aff, crs, pixel_size = load_dem()


# ------------------------------------
# LAYOUT
# ------------------------------------
st.markdown("<div class='section-header'>Water Level Simulation</div>", unsafe_allow_html=True)

# col_slider, col_map = st.columns([1,5])

with col_slider:

    st.markdown("654 cm ↑")

    h_cm = vertical_slider(
        label="",
        key="vert_slider",
        step=1,
        default_value=281.5,
        min_value=0,
        max_value=654,
        height=350
    )

    st.markdown("0 cm ↓")

    h_abs = REF_HEIGHT + h_cm / 100.0

    st.markdown(f"""
    <div style='margin-top:20px;'>
        <div><b>Water Level</b></div>
        <div style='color:#B00020; font-size:32px; font-weight:700;'>{h_cm} cm</div>
        <br>
        <div><b>Elevation</b></div>
        <div style='font-size:34px; color:#003366;'>{h_abs:.2f} m a.s.l.</div>
    </div>
    """, unsafe_allow_html=True)


# ------------------------------------
# FLOOD MASK
# ------------------------------------
water = dem <= h_abs
if np.sum(water) == 0:
    st.warning("No flooded areas.")
    st.stop()

results = (
    {"properties": {"water": v}, "geometry": s}
    for (s, v) in shapes(water.astype(np.uint8), transform=transform_aff)
    if v == 1
)

gdf = gpd.GeoDataFrame.from_features(list(results), crs=crs)
aoi = gpd.read_file("cerknica_digital_twin/aoi.gpkg")
gdf = gpd.overlay(gdf, aoi, how="intersection")

if gdf.empty:
    st.warning("Flood outside AOI.")
    st.stop()

area_m2 = gdf.geometry.area.sum()
area_ha = area_m2 / 10000

pixel_area = pixel_size ** 2
depth = np.where(water, h_abs - dem, 0)
volume_m3 = np.sum(depth) * pixel_area
volume_hm3 = volume_m3 / 1_000_000


# ------------------------------------
# MAP (LIMITED TO LAKE AREA)
# ------------------------------------
with col_map:

    gdf_web = gdf.to_crs(epsg=4326)
    aoi_web = aoi.to_crs(epsg=4326)

    m = folium.Map(tiles=None)

    folium.TileLayer(
       tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Imagery/MapServer/tile/{z}/{y}/{x}",
      attr="Esri",
      name="ESRI Satellite",
      overlay=False,
     control=True
    ).add_to(m)

    folium.GeoJson(
        gdf_web,
        style_function=lambda x: {
            "fillColor": "#1f77b4",
            "color": "#1f77b4",
            "weight": 1.5,
            "fillOpacity": 0.7
        }
    ).add_to(m)

    bounds = aoi_web.total_bounds
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    st_folium(m, use_container_width=True, height=900)


# ------------------------------------
# METRICS
# ------------------------------------
st.markdown("<br><br>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div style='text-align:center;'>
        <div class='metric-number'>{area_ha:.1f}</div>
        <div class='metric-unit'>ha</div>
        <div class='metric-label'>Area</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style='text-align:center;'>
        <div class='metric-number'>{volume_hm3:.2f}</div>
        <div class='metric-unit'>hm³</div>
        <div class='metric-label'>Volume</div>
    </div>
    """, unsafe_allow_html=True)


# ------------------------------------
# FOOTER
# ------------------------------------
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
        "<div class='footer' style='text-align:right;'>© UL FGG, 2026</div>",
        unsafe_allow_html=True
    )
