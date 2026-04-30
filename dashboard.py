import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="AIM ASEAN Analytics", layout="wide", page_icon="📊")

st.markdown("""
    <style>
    /* Background Utama Dashboard */
    .main { background-color: #0E1117; }
    
    /* --- MENYEMBUNYIKAN CREATOR INFO & FOOTER STREAMLIT --- */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Metrik: Hapus box putih dan buat transparan */
    [data-testid="stMetric"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0px !important;
    }
    
    /* Warna Teks Metric agar selalu terlihat jelas */
    [data-testid="stMetricLabel"] { color: #FAFAFA !important; font-weight: 600 !important; font-size: 16px !important;}
    [data-testid="stMetricValue"] { color: #4FACFE !important; font-weight: bold !important; }

    /* Container untuk Chart (Transparan) */
    .chart-card {
        background-color: transparent;
        margin-bottom: 20px;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    
    /* Judul Dashboard */
    h1 { color: #FAFAFA; font-family: 'Segoe UI', sans-serif; font-weight: 800; }
    h3 { color: #FAFAFA; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

st.sidebar.title("Pengaturan Data")
uploaded_files = st.sidebar.file_uploader(
    "Upload Dataset (Bisa pilih >1 file Excel/CSV)", 
    type=["xlsx", "xls", "csv"], 
    accept_multiple_files=True
)

@st.cache_data(ttl=10)
def load_data(files):
    if not files:
        return pd.DataFrame()
    
    df_list = []
    for file in files:
        try:
            if file.name.endswith('.csv'):
                df_temp = pd.read_csv(file, header=1)
            else:
                df_temp = pd.read_excel(file, sheet_name='Raw Data', header=1)
            
            df_temp.columns = df_temp.columns.astype(str).str.strip()
            df_temp = df_temp.dropna(how='all')
             
            if 'Nama Lengkap' in df_temp.columns:
                df_temp = df_temp.dropna(subset=['Nama Lengkap'])

            # --- LOGIKA DATA: Mengisi Rentang Usia jika kosong ---
            if 'Umur' in df_temp.columns:
                df_temp['Umur'] = pd.to_numeric(df_temp['Umur'], errors='coerce')
                def tentukan_rentang(u):
                    if u < 16: return "Anak-anak (< 16 Tahun)"
                    elif 16 <= u <= 19: return "Remaja (16 - 19 Tahun)"
                    elif 20 <= u <= 35: return "Muda (20 - 35 Tahun)"
                    elif 36 <= u <= 65: return "Dewasa (36 - 65 Tahun)"
                    elif u > 65: return "Lansia (> 65 Tahun)"
                    return "Tidak Diketahui"
                df_temp['Rentang Usia'] = df_temp['Umur'].apply(tentukan_rentang)
                
            df_list.append(df_temp)
        except Exception as e:
            st.sidebar.error(f"Gagal baca file {file.name}: {e}")
            
    if df_list:
        return pd.concat(df_list, ignore_index=True)
    return pd.DataFrame()

df = load_data(uploaded_files)

st.title("AIM ASEAN CERTIFIED BENEFICIARIES DASHBOARD")
st.markdown("---")

if not df.empty:
    st.subheader("Filter Data")
    sf1, sf2, sf3, sf4, sf5, sf6 = st.columns(6)
    
    def get_opsi(kolom):
        if kolom in df.columns:
            if kolom == 'Rentang Usia':
                return ["Semua", "Anak-anak (< 16 Tahun)", "Remaja (16 - 19 Tahun)", "Muda (20 - 35 Tahun)", "Dewasa (36 - 65 Tahun)", "Lansia (> 65 Tahun)"]
            return ["Semua"] + sorted([str(x) for x in df[kolom].dropna().unique()])
        return ["Semua"]

    with sf1: filter_prov = st.selectbox("Provinsi", get_opsi('Provinsi'))
    with sf2: filter_usia = st.selectbox("Rentang Usia", get_opsi('Rentang Usia'))
    with sf3: filter_sektor = st.selectbox("Sektor UMKM", get_opsi('Sektor UMKM'))
    with sf4: filter_gender = st.selectbox("Jenis Kelamin", get_opsi('Jenis Kelamin'))
    with sf5: filter_kat = st.selectbox("Kategori UMKM", get_opsi('Kategori UMKM'))
    with sf6: filter_peny = st.selectbox("Penyelenggara", get_opsi('Penyelenggara'))

    dff = df.copy()
    if filter_prov != "Semua": dff = dff[dff['Provinsi'] == filter_prov]
    if filter_usia != "Semua": dff = dff[dff['Rentang Usia'] == filter_usia]
    if filter_sektor != "Semua": dff = dff[dff['Sektor UMKM'] == filter_sektor]
    if filter_gender != "Semua": dff = dff[dff['Jenis Kelamin'] == filter_gender]
    if filter_kat != "Semua": dff = dff[dff['Kategori UMKM'] == filter_kat]
    if filter_peny != "Semua": dff = dff[dff['Penyelenggara'] == filter_peny]

    st.markdown("###")

    total_peserta = len(dff)
    proyeksi = int(total_peserta * 1.15) 
    
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("Total Peserta", f"{total_peserta} Orang")
    with m2: st.metric("Target Proyeksi (+15%)", f"{proyeksi} Orang")
    with m3:
        p_count = len(dff[dff['Jenis Kelamin'] == 'Perempuan']) if 'Jenis Kelamin' in dff.columns else 0
        st.metric("Peserta Perempuan", f"{p_count} Orang")
    with m4:
        st.metric("Peserta Laki-laki", f"{total_peserta - p_count} Orang")

    st.markdown("###")

    def buat_donut(kolom, judul):
        if kolom in dff.columns and not dff[kolom].empty:
            counts = dff[kolom].value_counts().reset_index()
            counts.columns = [kolom, 'Jumlah']
            
            # hole ditingkatkan sedikit agar lebih elegan
            fig = px.pie(counts, names=kolom, values='Jumlah', hole=0.7)
            
            fig.update_traces(
                textposition='inside', 
                textinfo='percent',    
                hovertemplate="<b>%{label}</b><br>Jumlah: %{value} Orang",
                marker=dict(colors=px.colors.qualitative.Pastel),
                # domain x dan y mengunci ukuran lingkaran donat agar tidak berubah-ubah
                domain=dict(x=[0, 1], y=[0.15, 1])
            )

            fig.update_layout(
                title=dict(text=f"<b>{judul}</b>", x=0.5, y=0.95, xanchor='center', font=dict(color='white')),
                margin=dict(t=40, b=10, l=10, r=10),
                height=450, 
                showlegend=True,
                legend=dict(
                    orientation="h", 
                    yanchor="top", 
                    y=0.1, 
                    xanchor="center", 
                    x=0.5,
                    font=dict(size=10, color='white')
                ),
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)'   
            )
            return fig
        return None

    r1_c1, r1_c2, r1_c3 = st.columns(3)
    with r1_c1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        fig1 = buat_donut('Sektor UMKM', "Sektor UMKM")
        if fig1: st.plotly_chart(fig1, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with r1_c2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        fig2 = buat_donut('Rentang Usia', "Rentang Usia")
        if fig2: st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with r1_c3:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        fig3 = buat_donut('Kategori UMKM', "Skala Bisnis")
        if fig3: st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    r2_c1, r2_c2 = st.columns(2)
    with r2_c1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        fig4 = buat_donut('Penyelenggara', "Penyelenggara Program")
        if fig4: st.plotly_chart(fig4, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with r2_c2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        fig5 = buat_donut('Provinsi', "Sebaran Wilayah")
        if fig5: st.plotly_chart(fig5, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("Silakan unggah file dataset (Excel/CSV) di menu sebelah kiri untuk memunculkan dashboard.")

if st.sidebar.button("Refresh data terbaru"):
    st.cache_data.clear()
    st.rerun()