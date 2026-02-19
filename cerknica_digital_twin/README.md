# Lake Cerknica Digital Twin

Interactive DEM-based flood simulation web application  
Developed at the University of Ljubljana, Faculty of Civil and Geodetic Engineering (UL FGG), 2026.

## Overview

This application simulates the intermittent flooding phenomenon of Lake Cerknica based on a high-resolution Digital Elevation Model (DEM).

Users can interactively adjust the water level and instantly observe:

- Flood extent (clipped to AOI)
- Flooded area (ha)
- Water volume (hm³)
- Interactive web map visualization

The model operates in EPSG:3794 (Slovenian national CRS) and is transformed to WGS84 for web visualization.

---

## Live Application

🔗 https://lake-cerknica-digital-twin.streamlit.app

---

## Features

- Water level slider (cm)
- Absolute elevation calculation (m a.s.l.)
- Raster-based flood simulation
- Vectorization of flood mask
- AOI clipping
- Area computation from clipped polygons
- Volume calculation from DEM depth
- Interactive Folium web map
- Cloud deployment via Streamlit

---

## Technical Stack

- Python 3.10
- Streamlit
- Rasterio
- GeoPandas
- Shapely
- PyProj
- Folium

---

## Project Structure

