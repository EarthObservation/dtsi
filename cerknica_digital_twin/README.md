# Lake Cerknica Digital Twin

Interactive DEM-based flood simulation web application  
Developed at the University of Ljubljana, Faculty of Civil and Geodetic Engineering (UL FGG), 2026.

---

## Overview

This web application simulates the intermittent flooding phenomenon of Lake Cerknica (Slovenia) using a Digital Elevation Model (DEM).

Users can interactively adjust the water level and instantly observe:

- Flood extent (clipped to Area of Interest)
- Flooded area (ha)
- Water volume (hm³)
- Interactive web map visualization

The application operates in the Slovenian national coordinate system (EPSG:3794) and is transformed to WGS84 for web visualization.

---

## Live Application

🔗 https://lake-cerknica-digital-twin.streamlit.app

---

## Digital Elevation Model (DEM)

The public web application uses a **15 m resolution Digital Elevation Model (DEM)** to ensure:

- Real-time raster processing performance  
- Stable cloud deployment  
- Efficient interactive visualization  

The reduced-resolution DEM preserves the overall morphologic characteristics of the Cerknica lake basin while allowing responsive simulation in a web environment.

### Higher-Resolution Data

Higher-resolution datasets are available internally at UL FGG:

- 1 m DEM
- Very High Resolution (VHR) UAV-derived DEM (September 2025 survey)

These datasets are not included in this public repository.

---

## Methodology

The flood simulation workflow includes:

1. Water level definition (cm → absolute elevation)
2. Raster-based flood mask generation
3. Raster-to-vector conversion
4. AOI clipping
5. Area computation from clipped polygons
6. Volume estimation from water depth (DEM difference)
7. Web map visualization (Folium / Leaflet)

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
cerknica_digital_twin/
│
├── app.py
├── requirements.txt
├── DMR.tif (15 m DEM)
├── aoi.gpkg
└── UL_FGG-logoENG-HOR-RGB_color.png


---

## Authors

Ana Potočnik Buhvald  
Krištof Oštir  
Neja Flogie  
Klemen Kozmus Trajkovski  

University of Ljubljana  
Faculty of Civil and Geodetic Engineering (UL FGG)

---

## Data Policy

The 15 m DEM included in this repository is used for demonstration and web visualization purposes.

High-resolution UAV-derived elevation data (2025) remain the intellectual property of UL FGG and are not publicly distributed.

---

## Citation

If referencing this application, please cite:

Potočnik Buhvald, A., Oštir, K., Flogie, N., & Kozmus Trajkovski, K. (2026).  
Lake Cerknica Digital Twin – DEM-based flood simulation web application.  
University of Ljubljana, UL FGG.

---

## License

This project was developed for research and educational purposes.

