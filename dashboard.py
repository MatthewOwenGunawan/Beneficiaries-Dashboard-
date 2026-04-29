import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="AIM ASEAN MSME Dashboard", layout="wide")


hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

DEFAULT_FILE = "Copy of Beneficiaries Monitoring Sheet - AIM ASEAN Dashboard.xlsx"
SHEET_NAME = "Raw Data"

def load_data(file_source):
    try:
        df = pd.read_excel(file_source, sheet_name=SHEET_NAME, skiprows=1)
        df.columns = df.columns.astype(str).str.strip() 
        return df
    except Exception as e:
        return None

st.title("AIM ASEAN CERTIFIED BENEFICIARIES DASHBOARD")
uploaded_file = st.file_uploader("Opsi: Upload file Excel baru untuk memperbarui data di bawah", type=["xlsx"])

source = uploaded_file if uploaded_file is not None else DEFAULT_FILE
df = load_data(source)

if df is not None and not df.empty:
    st.markdown("---")
    
    st.subheader("📌 INTERACTIVE SLICER")
    st.info("💡 Kosongkan pilihan untuk menampilkan SEMUA data. Kamu bisa memilih lebih dari 1 opsi.")
    
    sf1, sf2, sf3 = st.columns(3)
    sf4, sf5, sf6 = st.columns(3)
    
    def get_opsi(kolom):
        return sorted(list(df[kolom].dropna().unique())) if kolom in df.columns else []

    with sf1: f_prov = st.multiselect("📍 Provinsi", get_opsi('Provinsi'))
    with sf2: f_usia = st.multiselect("👥 Rentang Usia", get_opsi('Rentang Usia'))
    with sf3: f_sektor = st.multiselect("🏭 Sektor UMKM", get_opsi('Sektor UMKM'))
    with sf4: f_gender = st.multiselect("🚻 Jenis Kelamin", get_opsi('Jenis Kelamin'))
    with sf5: f_kat = st.multiselect("💼 Kategori UMKM", get_opsi('Kategori UMKM'))
    with sf6: f_peny = st.multiselect("🏢 Penyelenggara", get_opsi('Penyelenggara'))

    df_filtered = df.copy()
    if f_prov: df_filtered = df_filtered[df_filtered['Provinsi'].isin(f_prov)]
    if f_usia: df_filtered = df_filtered[df_filtered['Rentang Usia'].isin(f_usia)]
    if f_sektor: df_filtered = df_filtered[df_filtered['Sektor UMKM'].isin(f_sektor)]
    if f_gender: df_filtered = df_filtered[df_filtered['Jenis Kelamin'].isin(f_gender)]
    if f_kat: df_filtered = df_filtered[df_filtered['Kategori UMKM'].isin(f_kat)]
    if f_peny: df_filtered = df_filtered[df_filtered['Penyelenggara'].isin(f_peny)]

    st.markdown("---")

    total_peserta = len(df_filtered)
    if total_peserta > 0:
        m1, m2 = st.columns(2)
        m1.metric("Total Peserta (Terfilter)", f"{total_peserta} Orang")
        
        proyeksi = int(total_peserta * 1.15)
        m2.metric("Proyeksi Target (+15%)", f"{proyeksi} Orang")

        st.write("##")

        def buat_pie_chart(kolom, judul):
            if kolom in df_filtered.columns:
                counts = df_filtered[kolom].value_counts().reset_index()
                counts.columns = ['Label', 'Jumlah']
                if not counts.empty:
                    fig = px.pie(counts, names='Label', values='Jumlah', hole=0.4, title=judul)
                    # Menampilkan angka murni (raw values)
                    fig.update_traces(textinfo='value', textfont_size=14)
                    return fig
            return None

        c1, c2 = st.columns(2)
        with c1:
            fig1 = buat_pie_chart('Sektor UMKM', "📊 Sektor UMKM")
            if fig1: st.plotly_chart(fig1, use_container_width=True)
        with c2:
            fig2 = buat_pie_chart('Provinsi', "🌍 Sebaran Provinsi")
            if fig2: st.plotly_chart(fig2, use_container_width=True)

        c3, c4 = st.columns(2)
        with c3:
            fig3 = buat_pie_chart('Rentang Usia', "🎂 Rentang Usia")
            if fig3: st.plotly_chart(fig3, use_container_width=True)
        with c4:
            fig4 = buat_pie_chart('Jenis Kelamin', "🚻 Jenis Kelamin")
            if fig4: st.plotly_chart(fig4, use_container_width=True)

        c5, c6 = st.columns(2)
        with c5:
            fig5 = buat_pie_chart('Kategori UMKM', "💼 Kategori UMKM")
            if fig5: st.plotly_chart(fig5, use_container_width=True)
        with c6:
            fig6 = buat_pie_chart('Penyelenggara', "🏢 Penyelenggara")
            if fig6: st.plotly_chart(fig6, use_container_width=True)

    else:
        st.warning("⚠️ Tidak ada data ditemukan untuk filter tersebut.")
else:
    st.error("❌ File default tidak ditemukan atau formatnya salah. Silakan upload file Excel secara manual di atas.")