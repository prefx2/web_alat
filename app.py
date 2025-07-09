import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import geopandas as gpd
import os

# Set tampilan lebar
st.set_page_config(layout="wide")
st.title("🗺️ Peta Sebaran Alat Pemantauan Indonesia")

# Pilihan alat & basemap di 2 kolom
col1, col2 = st.columns(2)

with col1:
    alat_options = ['AAWS', 'ARG', 'ASRS', 'AWS', 'IKRO', 'SM']
    selected_alat = st.selectbox("🔍 Pilih Jenis Alat:", alat_options)

with col2:
    basemap_options = ['ZOM', 'Provinsi']
    selected_basemap = st.selectbox("🗺️ Pilih Basemap:", basemap_options)

# Path folder
base_folder = os.getcwd()
data_folder = os.path.join(base_folder, 'data')
image_folder = os.path.join(base_folder, 'image')
shapefile_folder = os.path.join(base_folder, 'shapefile')

# Path GeoJSON
geojson_path = os.path.join(shapefile_folder, 'zom_s_simplified.geojson')

# Load data CSV
data_path = os.path.join(data_folder, f"{selected_alat.lower()}.csv")
try:
    df = pd.read_csv(data_path, delimiter=';', encoding='utf-8', on_bad_lines='skip')
    df.columns = df.columns.str.strip()
except Exception as e:
    st.error(f"Gagal memuat data CSV: {e}")
    df = pd.DataFrame()

# ➕ Filter Provinsi (jika data ada)
prov_options = df['nama_propinsi'].dropna().unique().tolist() if not df.empty and 'nama_propinsi' in df.columns else []
prov_options = sorted([p for p in prov_options if p])  # Hapus yang kosong/null

selected_provinsi = st.selectbox("🗂️ Pilih Provinsi (Opsional):", ['Semua'] + prov_options)

# Terapkan filter provinsi ke dataframe
if selected_provinsi != 'Semua' and not df.empty:
    df_filtered = df[df['nama_propinsi'] == selected_provinsi]
else:
    df_filtered = df.copy()

# Buat peta
m = folium.Map(location=[-2.5, 118], zoom_start=5, tiles='cartodb positron')

# Cache GeoJSON
@st.cache_resource
def load_geojson(path):
    return gpd.read_file(path)

# Tambahkan layer ZOM jika dipilih
if selected_basemap == 'ZOM':
    try:
        gdf = load_geojson(geojson_path)
        folium.GeoJson(
            gdf,
            name='ZOM',
            style_function=lambda x: {
                'fillColor': 'none',
                'color': 'black',
                'weight': 1
            }
        ).add_to(m)
        st.success("✅ Layer ZOM berhasil dimuat")
    except Exception as e:
        st.warning(f"Gagal memuat layer ZOM: {e}")
else:
    st.info("📌 Basemap: Provinsi ")

# Tambahkan Marker Cluster
if not df_filtered.empty:
    required_columns = {'latt_station', 'long_station', 'name_station'}
    if required_columns.issubset(df_filtered.columns):
        marker_cluster = MarkerCluster().add_to(m)
        for _, row in df_filtered.iterrows():
            try:
                lat, lon = float(row['latt_station']), float(row['long_station'])
                prov = row.get('nama_propinsi', 'Tidak Diketahui')
                popup = f"<b>{row['name_station']}</b><br>Provinsi: {prov}"
                folium.Marker(
                    location=[lat, lon],
                    popup=popup,
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(marker_cluster)
            except:
                continue
    else:
        st.warning("❗ Data tidak lengkap: Pastikan kolom 'latt_station', 'long_station', dan 'name_station' ada.")
else:
    st.info("📌 Tidak ada data untuk ditampilkan.")

# Layer Control dan tampilkan peta
folium.LayerControl().add_to(m)
st_folium(m, width=1200, height=700)

# Download Peta Statis
st.subheader("📥 Download Peta Statis")

# Keterangan Dinamis
nama_peta = f"{selected_alat} dengan {selected_basemap}"
st.write(f"Silakan download peta **{nama_peta}** berikut:")

image_basename = f"{'zom' if selected_basemap == 'ZOM' else 'shp'}_{selected_alat}.png"
image_path = os.path.join(image_folder, image_basename)

if os.path.isfile(image_path):
    with open(image_path, "rb") as img_file:
        st.download_button(f"⬇️ Download Peta {selected_alat}", img_file, file_name=image_basename, mime="image/png")
else:
    st.warning(f"❗ Peta statis untuk {nama_peta} belum tersedia.")
