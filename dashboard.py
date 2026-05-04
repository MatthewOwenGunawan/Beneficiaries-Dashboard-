import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit.components.v1 import html
import time
import re

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="AIM ASEAN Analytics", layout="wide", page_icon="📊")

# --- KUSTOMISASI TAMPILAN (GHOST MODE) ---
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden; display: none !important;} 
    header {visibility: hidden;}
    [data-testid="stStatusWidget"] {display: none !important;}
    .stAppDeployButton {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    #streamlit_share_button {display: none !important;}
    .viewerBadge_container__1QSob {display: none !important;}
    .viewerBadge_link__1S137 {display: none !important;}
    
    [data-testid="stMetric"] { background-color: transparent !important; border: none !important; box-shadow: none !important; padding: 0px !important; }
    [data-testid="stMetricLabel"] { color: #FAFAFA !important; font-weight: 600 !important; font-size: 16px !important;}
    [data-testid="stMetricValue"] { color: #4FACFE !important; font-weight: bold !important; }
    
    .chart-card { background-color: transparent; margin-bottom: 30px; display: flex; flex-direction: column; align-items: center; }
    h1 { color: #FAFAFA; font-family: 'Segoe UI', sans-serif; font-weight: 800; }
    h3 { color: #FAFAFA; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

html('<script>window.top.document.querySelectorAll(`[href*="streamlit.io"]`).forEach(e => e.setAttribute("style", "display: none;"));</script>')

# --- PENGATURAN SIDEBAR (LIVE DATA MULTI-SHEET) ---
st.sidebar.title("Pengaturan Data Live")

st.sidebar.markdown("**1. Data Online/Offline Training**")
url_training = st.sidebar.text_input("Link Tab Training", placeholder="Paste link tab Training di sini...", key="url_train")

st.sidebar.markdown("**2. Data Self Learning (LMS)**")
url_lms = st.sidebar.text_input("Link Tab LMS", placeholder="Paste link tab LMS di sini...", key="url_lms")

st.sidebar.markdown("---")
auto_refresh = st.sidebar.checkbox("Aktifkan Auto-Refresh Real-Time")
refresh_rate = st.sidebar.slider("Interval Refresh (detik)", min_value=5, max_value=60, value=10)

# --- FUNGSI LOAD DATA JALUR CEPAT (OTOMATIS KASIH LABEL) ---
def load_single_csv(url, tipe_pembelajaran):
    if not url:
        return pd.DataFrame()
    try:
        doc_id_match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
        gid_match = re.search(r"gid=([0-9]+)", url)
        
        if doc_id_match:
            doc_id = doc_id_match.group(1)
            gid = gid_match.group(1) if gid_match else "0"
            export_url = f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=csv&gid={gid}&t={int(time.time())}"
            
            df_temp = pd.read_csv(export_url)
            df_temp.columns = df_temp.columns.astype(str).str.strip()
            
            if 'Nama Lengkap' not in df_temp.columns:
                df_temp = pd.read_csv(export_url, header=1)
                df_temp.columns = df_temp.columns.astype(str).str.strip()

            df_temp = df_temp.dropna(how='all')
            if 'Nama Lengkap' in df_temp.columns:
                df_temp = df_temp.dropna(subset=['Nama Lengkap'])

            if 'Umur' in df_temp.columns:
                df_temp['Umur'] = pd.to_numeric(df_temp['Umur'], errors='coerce')
                def tentukan_rentang(u):
                    if pd.isna(u): return "Tidak Diketahui"
                    if u < 16: return "Anak-anak (< 16 Tahun)"
                    elif 16 <= u <= 19: return "Remaja (16 - 19 Tahun)"
                    elif 20 <= u <= 35: return "Muda (20 - 35 Tahun)"
                    elif 36 <= u <= 65: return "Dewasa (36 - 65 Tahun)"
                    elif u > 65: return "Lansia (> 65 Tahun)"
                    return "Tidak Diketahui"
                df_temp['Rentang Usia'] = df_temp['Umur'].apply(tentukan_rentang)
            
            df_temp['Tipe Pembelajaran'] = tipe_pembelajaran
            return df_temp
        return pd.DataFrame()
    except Exception as e:
        st.sidebar.error(f"Gagal memuat data {tipe_pembelajaran}. Error: {e}")
        return pd.DataFrame()

# --- PENGGABUNGAN DATA (CONCAT) ---
df_train = load_single_csv(url_training, "Training (Online/Offline)")
df_lms = load_single_csv(url_lms, "Self Learning (LMS)")

frames = []
if not df_train.empty: frames.append(df_train)
if not df_lms.empty: frames.append(df_lms)

df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

# --- HEADER DASHBOARD ---
st.title("AIM ASEAN CERTIFIED BENEFICIARIES DASHBOARD")
st.markdown("---")

# --- KONTEN UTAMA DASHBOARD ---
if not df.empty:
    
    st.subheader("Filter Data")
    
    # Baris Filter 1
    c1, c2, c3, c4 = st.columns(4)
    def get_opsi(kolom):
        if kolom in df.columns:
            if kolom == 'Rentang Usia':
                return ["Semua", "Anak-anak (< 16 Tahun)", "Remaja (16 - 19 Tahun)", "Muda (20 - 35 Tahun)", "Dewasa (36 - 65 Tahun)", "Lansia (> 65 Tahun)", "Tidak Diketahui"]
            return ["Semua"] + sorted([str(x) for x in df[kolom].dropna().unique()])
        return ["Semua"]

    with c1: filter_prov = st.selectbox("Provinsi", get_opsi('Provinsi'))
    with c2: filter_usia = st.selectbox("Rentang Usia", get_opsi('Rentang Usia'))
    with c3: filter_sektor = st.selectbox("Sektor UMKM", get_opsi('Sektor UMKM'))
    with c4: filter_gender = st.selectbox("Jenis Kelamin", get_opsi('Jenis Kelamin'))
    
    # Baris Filter 2
    c5, c6, c7 = st.columns(3)
    with c5: filter_kat = st.selectbox("Kategori UMKM", get_opsi('Kategori UMKM'))
    with c6: filter_peny = st.selectbox("Penyelenggara", get_opsi('Penyelenggara'))
    with c7: filter_tipe = st.selectbox("Tipe Pembelajaran", get_opsi('Tipe Pembelajaran'))

    # Eksekusi Filter
    dff = df.copy()
    if filter_prov != "Semua" and 'Provinsi' in dff.columns: dff = dff[dff['Provinsi'] == filter_prov]
    if filter_usia != "Semua" and 'Rentang Usia' in dff.columns: dff = dff[dff['Rentang Usia'] == filter_usia]
    if filter_sektor != "Semua" and 'Sektor UMKM' in dff.columns: dff = dff[dff['Sektor UMKM'] == filter_sektor]
    if filter_gender != "Semua" and 'Jenis Kelamin' in dff.columns: dff = dff[dff['Jenis Kelamin'] == filter_gender]
    if filter_kat != "Semua" and 'Kategori UMKM' in dff.columns: dff = dff[dff['Kategori UMKM'] == filter_kat]
    if filter_peny != "Semua" and 'Penyelenggara' in dff.columns: dff = dff[dff['Penyelenggara'] == filter_peny]
    if filter_tipe != "Semua" and 'Tipe Pembelajaran' in dff.columns: dff = dff[dff['Tipe Pembelajaran'] == filter_tipe]

    st.markdown("###")
    
    # --- METRIK UTAMA ---
    total_peserta = len(dff)
    
    if 'Tipe Pembelajaran' in dff.columns:
        t_count = len(dff[dff['Tipe Pembelajaran'] == 'Training (Online/Offline)'])
        l_count = len(dff[dff['Tipe Pembelajaran'] == 'Self Learning (LMS)'])
    else:
        t_count, l_count = 0, 0
        
    p_count = len(dff[dff['Jenis Kelamin'] == 'Perempuan']) if 'Jenis Kelamin' in dff.columns else 0
    
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("Total Peserta Live", f"{total_peserta} Orang")
    with m2: st.metric("Peserta Training", f"{t_count} Orang")
    with m3: st.metric("Peserta LMS", f"{l_count} Orang")

    st.markdown("###")

    # --- FUNGSI PEMBUAT GRAFIK PIE/DONUT ---
    def buat_pie_chart(kolom, judul, is_donut=False):
        if kolom in dff.columns and not dff[kolom].empty:
            counts = dff[dff[kolom].notna()][kolom].value_counts().reset_index()
            counts.columns = [kolom, 'Jumlah']
            hole_val = 0.7 if is_donut else 0
            fig = px.pie(counts, names=kolom, values='Jumlah', hole=hole_val)
            fig.update_traces(textposition='inside', textinfo='percent',
                              marker=dict(colors=px.colors.qualitative.Pastel, line=dict(color='#0E1117', width=1)),
                              domain=dict(x=[0, 1], y=[0.25, 1]))
            fig.update_layout(title=dict(text=f"<b>{judul}</b>", x=0.5, y=0.98, xanchor='center', font=dict(color='white', size=16)),
                              margin=dict(t=30, b=0, l=10, r=10), height=400, showlegend=True,
                              legend=dict(orientation="h", yanchor="top", y=0.2, xanchor="center", x=0.5, font=dict(size=10, color='white')),
                              uniformtext_minsize=10, uniformtext_mode='hide', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            return fig
        return None

    # --- RENDER 5 GRAFIK ---
    r1_c1, r1_c2, r1_c3 = st.columns(3)
    with r1_c1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        f1 = buat_pie_chart('Sektor UMKM', "Sektor UMKM", is_donut=True)
        if f1: st.plotly_chart(f1, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with r1_c2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        f2 = buat_pie_chart('Rentang Usia', "Rentang Usia")
        if f2: st.plotly_chart(f2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with r1_c3:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        f3 = buat_pie_chart('Kategori UMKM', "Skala Bisnis")
        if f3: st.plotly_chart(f3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    r2_c1, r2_c2 = st.columns(2)
    with r2_c1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        f4 = buat_pie_chart('Penyelenggara', "Penyelenggara")
        if f4: st.plotly_chart(f4, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with r2_c2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        f5 = buat_pie_chart('Jenis Kelamin', "Jenis Kelamin")
        if f5: st.plotly_chart(f5, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- RENDER TABEL PROVINSI ---
    st.markdown("---")
    st.markdown("<h3 style='text-align: center;'>Sebaran Wilayah Provinsi</h3>", unsafe_allow_html=True)
    
    if 'Provinsi' in dff.columns and not dff['Provinsi'].empty:
        # Hitung jumlah per provinsi dan urutkan dari yang terbanyak
        df_prov = dff[dff['Provinsi'].notna()]['Provinsi'].value_counts().reset_index()
        df_prov.columns = ['Nama Provinsi', 'Jumlah Peserta']
        
        # Atur index agar dimulai dari 1 (untuk nomor urut)
        df_prov.index = range(1, len(df_prov) + 1)
        
        # Buat 3 kolom layout agar tabel tidak terlalu melebar ke samping (ditengahkan)
        col_space_left, col_table, col_space_right = st.columns([1, 2, 1])
        with col_table:
            st.dataframe(df_prov, use_container_width=True)
    else:
        st.info("Data Provinsi tidak tersedia di dalam dataset.")

else:
    st.info("Silakan masukkan URL tab Google Sheets yang valid di panel sebelah kiri untuk memulai.")

if st.sidebar.button("Refresh data manual"):
    st.rerun()

if auto_refresh and (url_training or url_lms):
    time.sleep(refresh_rate)
    st.rerun()