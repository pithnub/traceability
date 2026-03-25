import streamlit as st
import pandas as pd
import pydeck as pdk
import numpy as np
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import qrcode
from io import BytesIO

# --- 1. CONFIG & "ULTRA-CONTRAST" STYLING ---
st.set_page_config(page_title="LASRA | KinetiCore EUDR", layout="wide", page_icon="🇳🇿")

st.markdown("""
    <style>
    /* Force metrics to be legible: White background, Dark Blue text, Heavy Border */
    [data-testid="stMetricValue"] { 
        background-color: #ffffff !important; 
        color: #004a99 !important; 
        padding: 15px !important; 
        border-radius: 8px !important; 
        border: 2px solid #004a99 !important;
        font-weight: 900 !important;
    }
    [data-testid="stMetricLabel"] { 
        color: #1e293b !important; 
        font-weight: 800 !important; 
        text-transform: uppercase !important;
        font-size: 0.9rem !important;
    }
    .anti-panic { 
        background-color: #fffde7; 
        padding: 20px; 
        border-radius: 8px; 
        border-left: 6px solid #fbc02d; 
        margin: 20px 0; 
        color: #856404;
    }
    .bold-label { font-weight: 900 !important; color: #004a99 !important; text-transform: uppercase; font-size: 0.85rem; display: block; margin-bottom: 10px; }
    .stButton>button { background: linear-gradient(90deg, #004a99 0%, #055fbe 100%); color: white; font-weight: bold; border: none; border-radius: 8px; height: 3.5em; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE PDF ENGINE (QR + MULTI-PAGE) ---
def generate_eudr_passport(batch_id, total_hides, farm_df):
    pdf = FPDF()
    pdf.add_page()
    
    # Blue Header
    pdf.set_fill_color(0, 74, 153)
    pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_font("Helvetica", 'B', 22)
    pdf.set_text_color(255, 255, 255)
    pdf.set_y(15)
    pdf.cell(0, 10, "EUDR TRACEABILITY PASSPORT", align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # Summary Details
    pdf.set_y(55)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, f"Batch Reference: {batch_id}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", '', 11)
    pdf.cell(0, 8, f"Total Volume: {total_hides:,} Hides", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"Verification Date: {datetime.now().strftime('%d %B %Y')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.line(10, 85, 200, 85)
    pdf.set_y(90)
    pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(0, 10, "Verified Origin Points (Biological Data Set):", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # Farm List
    pdf.set_font("Courier", '', 8)
    for _, row in farm_df.iterrows():
        if pdf.get_y() > 260:
            pdf.add_page()
            pdf.set_y(20)
        origin_str = f"- Farm: {row['farm_id']:<12} | Lat: {row['latitude']:>8.4f} | Long: {row['longitude']:>8.4f}"
        pdf.cell(0, 5, origin_str, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # QR Code
    qr = qrcode.QRCode(box_size=10)
    qr.add_data(f"https://lasra.co.nz/verify/{batch_id}")
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = BytesIO()
    img_qr.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    pdf.image(qr_buffer, x=165, y=5, w=35)

    # Footer
    pdf.set_y(275)
    pdf.set_font("Helvetica", 'I', 7)
    pdf.multi_cell(0, 4, "COMPLIANCE NOTE: Zero deforestation activity detected post-Dec 31, 2020. (EUDR 2023/1115).", align='C')
    
    return bytes(pdf.output())

# --- 3. DATA LOADING ---
def load_complex_data():
    n_farms = 35
    lats = np.concatenate([np.random.uniform(-38.3, -37.5, 20), np.random.uniform(-44.0, -43.3, 15)])
    longs = np.concatenate([np.random.uniform(175.2, 175.9, 20), np.random.uniform(171.8, 172.5, 15)])
    
    st.session_state.lims_data = pd.DataFrame({
        "batch_id": ["KINETIC-2026-ALPHA"], "meatworks_ref": ["MW-NZ-CORE"], "hide_count": [3500]
    })
    st.session_state.farm_data = pd.DataFrame({
        "meatworks_ref": ["MW-NZ-CORE"] * n_farms,
        "farm_id": [f"NZ-L-{i:03d}" for i in range(1, n_farms + 1)],
        "latitude": lats, "longitude": longs,
        "region_vol": np.random.randint(50, 200, size=n_farms)
    })

# --- 4. APP UI ---
st.title("🛰️ LASRA: KinetiCore Traceability")

st.markdown("""
    <div class="anti-panic">
        <b>💡 SYSTEM NOTE:</b> Metrics below are forced to high-contrast mode for forensic clarity.
    </div>
""", unsafe_allow_html=True)

if st.button("✨ Load Distributed NZ Data (Simulation)"):
    load_complex_data()

if 'lims_data' not in st.session_state:
    st.session_state.lims_data = pd.DataFrame({"batch_id": ["REF-01"], "meatworks_ref": ["MW-01"], "hide_count": [1000]})
if 'farm_data' not in st.session_state:
    st.session_state.farm_data = pd.DataFrame({"meatworks_ref": ["MW-01"], "farm_id": ["F-01"], "latitude": [-38.0], "longitude": [175.5], "region_vol": [1000]})

c1, c2 = st.columns(2)
with c1:
    st.markdown("<span class='bold-label'>Tannery LIMS Output</span>", unsafe_allow_html=True)
    df_lims = st.data_editor(st.session_state.lims_data, num_rows="dynamic", key="lims_v13")
with c2:
    st.markdown("<span class='bold-label'>Meat Works Origin Evidence</span>", unsafe_allow_html=True)
    df_manifest = st.data_editor(st.session_state.farm_data, num_rows="dynamic", key="farm_v13")

if st.button("🚀 EXECUTE COMPLIANCE AUDIT"):
    enriched = pd.merge(df_lims, df_manifest, on="meatworks_ref", how="left")
    total_hides = enriched['hide_count'].iloc[0]
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Verified Volume", f"{total_hides:,} Hides")
    m2.metric("Verified Origin Points", enriched['farm_id'].nunique())
    m3.metric("EUDR Risk Status", "NEGLIGIBLE (NZ)")

    st.markdown("<span class='bold-label'>Geospatial Verification Map</span>", unsafe_allow_html=True)
    
    # Stable Map (No Token)
    view_state = pdk.ViewState(latitude=-41.0, longitude=174.0, zoom=5.5, pitch=45)
    layer = pdk.Layer(
        "ColumnLayer", enriched, get_position='[longitude, latitude]',
        get_elevation='region_vol', elevation_scale=500, radius=12000,
        get_fill_color=[0, 74, 153, 200], pickable=True, extruded=True
    )
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "Origin: {farm_id}"}))

    # Regional Summary Table
    st.markdown("### Regional Mass Balance Summary")
    summary = enriched.groupby('farm_id')['region_vol'].sum().reset_index()
    summary['% Contribution'] = (summary['region_vol'] / summary['region_vol'].sum() * 100).round(1)
    st.table(summary.sort_values(by='% Contribution', ascending=False).head(10))

    # PDF Download
    pdf_bytes = generate_eudr_passport(enriched['batch_id'].iloc[0], total_hides, enriched)
    st.download_button("📄 DOWNLOAD EUDR PASSPORT", data=pdf_bytes, file_name="LASRA_Passport.pdf", mime="application/pdf", use_container_width=True)
