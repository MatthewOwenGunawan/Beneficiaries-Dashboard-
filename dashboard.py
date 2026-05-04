import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit.components.v1 import html
import time
import re

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="AIM ASEAN Analytics", layout="wide")

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

    [data-testid="stMetric"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0px !important;
    }
    [data-testid="stMetricLabel"] { color: #FAFAFA !important; font-weight: 600 !important; font-size: 16px !important;}
    [data-testid="stMetricValue"] { color: #4FACFE !important; font-weight: bold !important; }

    .chart-card {
        background-color: transparent;
        margin-bottom: 30px;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    
    h1 { color: #FAFAFA; font-family: 'Segoe UI', sans-serif; font-weight: 800; }
    h3 { color: #FAFAFA; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

html('''
   <script>
    window.top.document.querySelectorAll(`[href*="streamlit.io"]`).forEach(e => e.setAttribute("style", "display: none;"));
  </script>
''')

# --- PENGATURAN SIDEBAR (LIVE DATA) ---
st.sidebar.title("Pengaturan Data Live")

# Input URL
data_url = st.sidebar.text_input(
    "Masukkan Link Dataset (Google Sheets)", 
    placeholder="Paste link Google Sheets di sini..."
)

# Toggle Auto-Refresh
st.sidebar.markdown("---")
auto_refresh = st.sidebar.checkbox("Aktifkan Auto-Refresh Real-Time")
refresh_rate = st.sidebar.slider("Interval Refresh (detik)", min_value=5, max_value=60, value=10)
target_peserta = st.sidebar.number_input("🎯 Target Total Peserta", min_value=1, value=1000, step=100)


# --- FUNGSI LOAD DATA DARI URL DENGAN PENCARI SHEET ---
@st.cache_data(ttl=5) # Cache 5 detik
def load_data_from_url(url):
    if not url:
        return pd.DataFrame()
    
    try:
        # EKSTRAK ID DARI URL & PAKSA DOWNLOAD XLSX (Bukan CSV)
        doc_id_match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
        if doc_id_match:
            doc_id = doc_id_match.group(1)
            export_url = f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=xlsx"
            
            xls = pd.ExcelFile(export_url)
            
            # --- MESIN PENCARI SHEET YANG BENAR ---
            target_sheet = None
            # 1. Cari nama persis
            for sheet in xls.sheet_names:
                if sheet.strip() in ["RAW Data ONLINE/OFFLINE", "RAW Data ONLINEOFFLINE"]:
                    target_sheet = sheet
                    break
            # 2. Kalau ga ketemu, cari yang mengandung kata 'RAW'
            if not target_sheet:
                for sheet in xls.sheet_names:
                    if "RAW" in sheet.upper():
                        target_sheet = sheet
                        break
            # 3. Pilihan terakhir ambil sheet pertama
            if not target_sheet:
                target_sheet = xls.sheet_names[0]
            
            # BACA EXCEL, BARIS KE-2 SEBAGAI HEADER
            df_temp = pd.read_excel(xls, sheet_name=target_sheet, header=1)
            
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
                
            return df_temp
        else:
            st.sidebar.error("Link Google Sheets tidak valid.")
            return pd.DataFrame()
            
    except Exception as e:
        st.sidebar.error(f"Gagal memuat data. Pastikan link Google Sheets disetting 'Anyone with the link can view'. Error: {e}")
        return pd.DataFrame()

df = load_data_from_url(data_url)

# --- HEADER DASHBOARD ---
st.title("AIM ASEAN CERTIFIED BENEFICIARIES DASHBOARD")
st.markdown("---")

# --- KONTEN UTAMA DASHBOARD ---
if not df.empty:
    
    # --- ALARM JIKA MASIH SALAH BACA SHEET ---
    dibutuhkan = ['Provinsi', 'Rentang Usia', 'Sektor UMKM', 'Jenis Kelamin', 'Kategori UMKM']
    missing_cols = [col for col in dibutuhkan if col not in df.columns]
    if missing_cols:
        st.error(f"🚨 Ups! Filter gagal karena sistem tidak menemukan kolom data yang benar. Data yang ditarik tidak memiliki kolom-kolom ini: {', '.join(missing_cols)}")
        with st.expander("🔍 Cek Kolom yang Terbaca Streamlit di Sini"):
            st.write("Kolom yang terbaca saat ini:", df.columns.tolist())

    st.subheader("Filter Data")
    sf1, sf2, sf3, sf4, sf5, sf6 = st.columns(6)
    
    def get_opsi(kolom):
        if kolom in df.columns:
            if kolom == 'Rentang Usia':
                return ["Semua", "Anak-anak (< 16 Tahun)", "Remaja (16 - 19 Tahun)", "Muda (20 - 35 Tahun)", "Dewasa (36 - 65 Tahun)", "Lansia (> 65 Tahun)", "Tidak Diketahui"]
            return ["Semua"] + sorted([str(x) for x in df[kolom].dropna().unique()])
        return ["Semua"]

    with sf1: filter_prov = st.selectbox("Provinsi", get_opsi('Provinsi'))
    with sf2: filter_usia = st.selectbox("Rentang Usia", get_opsi('Rentang Usia'))
    with sf3: filter_sektor = st.selectbox("Sektor UMKM", get_opsi('Sektor UMKM'))
    with sf4: filter_gender = st.selectbox("Jenis Kelamin", get_opsi('Jenis Kelamin'))
    with sf5: filter_kat = st.selectbox("Kategori UMKM", get_opsi('Kategori UMKM'))
    with sf6: filter_peny = st.selectbox("Penyelenggara", get_opsi('Penyelenggara'))

    # Implementasi Filter
    dff = df.copy()
    if filter_prov != "Semua" and 'Provinsi' in dff.columns: dff = dff[dff['Provinsi'] == filter_prov]
    if filter_usia != "Semua" and 'Rentang Usia' in dff.columns: dff = dff[dff['Rentang Usia'] == filter_usia]
    if filter_sektor != "Semua" and 'Sektor UMKM' in dff.columns: dff = dff[dff['Sektor UMKM'] == filter_sektor]
    if filter_gender != "Semua" and 'Jenis Kelamin' in dff.columns: dff = dff[dff['Jenis Kelamin'] == filter_gender]
    if filter_kat != "Semua" and 'Kategori UMKM' in dff.columns: dff = dff[dff['Kategori UMKM'] == filter_kat]
    if filter_peny != "Semua" and 'Penyelenggara' in dff.columns: dff = dff[dff['Penyelenggara'] == filter_peny]

    st.markdown("###")
    
    # --- PANTAUAN PROGRESS ---
    total_peserta = len(dff)
    
    st.markdown(f"**Pantauan Progress Peserta (Target: {target_peserta})**")
    progress_ratio = total_peserta / target_peserta if target_peserta > 0 else 0
    progress_val = min(progress_ratio, 1.0)
    st.progress(progress_val)
    st.caption(f"Pencapaian saat ini: {total_peserta} orang ({progress_ratio*100:.1f}%)")
    
    st.markdown("###")
    
    # --- METRIK UTAMA ---
    proyeksi = int(total_peserta * 1.15) 
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("Total Peserta Live", f"{total_peserta} Orang")
    with m2: st.metric("Target Proyeksi (+15%)", f"{proyeksi} Orang")
    with m3:
        p_count = len(dff[dff['Jenis Kelamin'] == 'Perempuan']) if 'Jenis Kelamin' in dff.columns else 0
        st.metric("Peserta Perempuan", f"{p_count} Orang")
    with m4:
        st.metric("Peserta Laki-laki", f"{total_peserta - p_count} Orang")

    st.markdown("###")

    # --- FUNGSI PEMBUAT GRAFIK ---
    def buat_chart(kolom, judul, is_donut=False):
        if kolom in dff.columns and not dff[kolom].empty:
            counts = dff[kolom].value_counts().reset_index()
            counts.columns = [kolom, 'Jumlah']
            
            hole_val = 0.7 if is_donut else 0
            fig = px.pie(counts, names=kolom, values='Jumlah', hole=hole_val)
            
            fig.update_traces(
                textposition='inside', 
                textinfo='percent',
                marker=dict(colors=px.colors.qualitative.Pastel, line=dict(color='#0E1117', width=1)),
                domain=dict(x=[0, 1], y=[0.25, 1])
            )

            fig.update_layout(
                title=dict(text=f"<b>{judul}</b>", x=0.5, y=0.98, xanchor='center', font=dict(color='white', size=16)),
                margin=dict(t=30, b=0, l=10, r=10),
                height=500,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="top", 
                    y=0.2, 
                    xanchor="center", 
                    x=0.5,
                    font=dict(size=10, color='white')
                ),
                uniformtext_minsize=10,
                uniformtext_mode='hide',
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)'   
            )
            return fig
        return None

    # --- RENDER GRAFIK (PLOT) ---
    r1_c1, r1_c2, r1_c3 = st.columns(3)
    with r1_c1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        f1 = buat_chart('Sektor UMKM', "Sektor UMKM", is_donut=True)
        if f1: st.plotly_chart(f1, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with r1_c2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        f2 = buat_chart('Rentang Usia', "Rentang Usia")
        if f2: st.plotly_chart(f2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with r1_c3:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        f3 = buat_chart('Kategori UMKM', "Skala Bisnis")
        if f3: st.plotly_chart(f3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    r2_c1, r2_c2 = st.columns(2)
    with r2_c1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        f4 = buat_chart('Penyelenggara', "Penyelenggara")
        if f4: st.plotly_chart(f4, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with r2_c2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        f5 = buat_chart('Jenis Kelamin', "Jenis Kelamin")
        if f5: st.plotly_chart(f5, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("Silakan masukkan URL dataset atau Google Sheets yang valid di panel sebelah kiri untuk memulai.")

# Tombol Refresh Manual (selalu tampil sebagai opsi cadangan)
if st.sidebar.button("Refresh data manual"):
    st.cache_data.clear()
    st.rerun()

# --- LOGIKA AUTO-REFRESH REAL-TIME ---
if auto_refresh and data_url:
    time.sleep(refresh_rate)
    st.rerun()