import streamlit as st
import numpy as np
import rasterio
import geopandas as gpd
from rasterio.features import shapes
import folium
from streamlit_folium import st_folium

# ------------------------------------
# Logo
# ------------------------------------
st.image("cerknica_digital_twin/UL_FGG-logoENG-HOR-RGB_color.png", width=660)

st.markdown(
    "### Authors: Ana Potočnik Buhvald, Krištof Oštir, Neja Flogie, Klemen Kozmus Trajkovski"
)

# ------------------------------------
# Title
# ------------------------------------
st.title("The intermittent lake phenomenon of Lake Cerknica")

st.markdown("---")

# ------------------------------------
# REFERENCE HEIGHT
# ------------------------------------
REF_HEIGHT = 545.417  # m a.s.l.

# ------------------------------------
# Load DEM
# ------------------------------------
@st.cache_data
def load_dem():
    with rasterio.open("DMR.tif") as src:
        dem = src.read(1).astype(np.float32)
        transform_aff = src.transform
        crs = src.crs
        pixel_size = src.res[0]
    return dem, transform_aff, crs, pixel_size

dem, transform_aff, crs, pixel_size = load_dem()

# ------------------------------------
# Slider
# ------------------------------------
h_cm = st.slider("Water level (cm)", 0, 600, 300)
h_abs = REF_HEIGHT + h_cm / 100.0

st.write(f"Absolute water elevation: {h_abs:.3f} m")

# ------------------------------------
# Flood mask
# ------------------------------------
water = dem <= h_abs

if np.sum(water) == 0:
    st.warning("No flooded areas at this water level.")
    st.stop()

# ------------------------------------
# Raster → polygon (EPSG:3794)
# ------------------------------------
results = (
    {"properties": {"water": v}, "geometry": s}
    for (s, v) in shapes(water.astype(np.uint8), transform=transform_aff)
    if v == 1
)

gdf = gpd.GeoDataFrame.from_features(list(results), crs=crs)

# ------------------------------------
# Load AOI (EPSG:3794)
# ------------------------------------
aoi = gpd.read_file("aoi.gpkg")

# ------------------------------------
# Clip flood polygons
# ------------------------------------
gdf = gpd.overlay(gdf, aoi, how="intersection")

if gdf.empty:
    st.warning("Flood extent outside AOI.")
    st.stop()

# ------------------------------------
# Correct area calculation (from clipped polygon)
# ------------------------------------
area_m2 = gdf.geometry.area.sum()
area_ha = area_m2 / 10000

# ------------------------------------
# Volume calculation (still raster-based inside AOI)
# ------------------------------------
pixel_area = pixel_size ** 2
depth = np.where(water, h_abs - dem, 0)
volume_m3 = np.sum(depth) * pixel_area
volume_hm3 = volume_m3 / 1_000_000

st.markdown(f"### Area: {area_ha:.1f} ha")
st.markdown(f"### Volume: {volume_hm3:.2f} hm³")

# ------------------------------------
# Transform to WGS84 for web map
# ------------------------------------
gdf_web = gdf.to_crs(epsg=4326)

# ------------------------------------
# Map
# ------------------------------------
center = gdf_web.geometry.unary_union.centroid

m = folium.Map(
    location=[center.y, center.x],
    zoom_start=12,
    tiles="OpenStreetMap"
)

folium.GeoJson(
    gdf_web,
    style_function=lambda x: {
        "fillColor": "blue",
        "color": "blue",
        "weight": 1,
        "fillOpacity": 0.6
    }
).add_to(m)

st_folium(m, width=900, height=600)

st.markdown(
    "<div style='text-align: right; font-size: 20px; color: gray;'>© UL FGG, 2026</div>",
    unsafe_allow_html=True
)
