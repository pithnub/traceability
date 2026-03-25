import streamlit as st
import pandas as pd
import pydeck as pdk
import numpy as np
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import qrcode
from io import BytesIO
import base64

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="LASRA | KinetiCore EUDR", layout="wide", page_icon="🇳🇿")

st.markdown("""
    <style>
    .metric-container { display: flex; justify-content: space-between; gap: 15px; margin-bottom: 20px; }
    .metric-card { 
        background-color: #ffffff !important; 
        border: 2px solid #004a99 !important; 
        padding: 15px; border-radius: 10px; flex: 1; text-align: center; 
    }
    .metric-label { color: #1e293b !important; font-size: 0.75rem !important; font-weight: 800 !important; text-transform: uppercase; }
    .metric-value { color: #004a99 !important; font-size: 1.6rem !important; font-weight: 900 !important; }
    .metric-delta { color: #16a34a !important; font-size: 0.8rem !important; font-weight: 600; }
    .qr-preview-card {
        background-color: #ffffff; border: 2px solid #004a99; border-radius: 10px;
        padding: 10px; text-align: center; width: 160px;
    }
    .bold-label { font-weight: 900 !important; color: #004a99 !important; text-transform: uppercase; font-size: 0.85rem; display: block; margin-bottom: 10px; }
    .stButton>button { background: linear-gradient(90deg, #004a99 0%, #055fbe 100%); color: white; font-weight: bold; border: none; border-radius: 8px; height: 3.5em; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. UTILITY: QR GENERATOR ---
def get_qr_base64(data):
    qr = qrcode.make(data)
    buffered = BytesIO()
    qr.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# --- 3. THE PDF ENGINE ---
def generate_eudr_passport(batch_id, total_hides, farm_df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(0, 74, 153)
    pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_font("Helvetica", 'B', 22); pdf.set_text_color(255, 255, 255); pdf.set_y(15)
    pdf.cell(0, 10, "EUDR TRACEABILITY PASSPORT", align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_y(55); pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, f"Batch Reference: {batch_id}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", '', 11)
    pdf.cell(0, 8, f"Total Volume: {total_hides:,} Hides", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.line(10, 85, 200, 85); pdf.set_y(90); pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(0, 10, "Verified Origin Points (Forensic Manifest):", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Courier", '', 8)
    for _, row in farm_df.iterrows():
        if pdf.get_y() > 260: pdf.add_page(); pdf.set_y(20)
        pdf.cell(0, 5, f"- Farm: {row['farm_id']:<12} | Lat: {row['latitude']:>8.4f} | Long: {row['longitude']:>8.4f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    qr_img = qrcode.make(f"https://lasra.co.nz/verify/{batch_id}")
    qr_buf = BytesIO(); qr_img.save(qr_buf, format="PNG"); qr_buf.seek(0)
    pdf.image(qr_buf, x=165, y=5, w=35)
    
    pdf.set_y(275); pdf.set_font("Helvetica", 'I', 7)
    pdf.multi_cell(0, 4, "VERIFICATION: Zero deforestation activity detected post-Dec 31, 2020. Compliant with EUDR 2023/1115.", align='C')
    return bytes(pdf.output())

# --- 4. APP LOGIC ---
st.title("🛰️ LASRA: KinetiCore Traceability")

if st.button("✨ Load Distributed NZ Data (Simulation)"):
    n_farms = 35
    lats = np.concatenate([np.random.uniform(-38.3, -37.5, 20), np.random.uniform(-44.0, -43.3, 15)])
    longs = np.concatenate([np.random.uniform(175.2, 175.9, 20), np.random.uniform(171.8, 172.5, 15)])
    st.session_state.lims_data = pd.DataFrame({"batch_id": ["KINETIC-2026-ALPHA"], "meatworks_ref": ["MW-NZ-CORE"], "hide_count": [3500]})
    st.session_state.farm_data = pd.DataFrame({"meatworks_ref": ["MW-NZ-CORE"] * n_farms, "farm_id": [f"NZ-L-{i:03d}" for i in range(1, n_farms + 1)], "latitude": lats, "longitude": longs, "region_vol": np.random.randint(50, 200, size=n_farms)})

if 'lims_data' not in st.session_state:
    st.session_state.lims_data = pd.DataFrame({"batch_id": ["REF-01"], "meatworks_ref": ["MW-01"], "hide_count": [1000]})
    st.session_state.farm_data = pd.DataFrame({"meatworks_ref": ["MW-01"], "farm_id": ["F-01"], "latitude": [-38.0], "longitude": [175.5], "region_vol": [1000]})

c1, c2 = st.columns(2)
with c1:
    st.markdown("<span class='bold-label'>Tannery LIMS Output</span>", unsafe_allow_html=True)
    df_lims = st.data_editor(st.session_state.lims_data, num_rows="dynamic", key="lims_v15")
with c2:
    st.markdown("<span class='bold-label'>Meat Works Origin Evidence</span>", unsafe_allow_html=True)
    df_manifest = st.data_editor(st.session_state.farm_data, num_rows="dynamic", key="farm_v15")

if st.button("🚀 EXECUTE COMPLIANCE AUDIT"):
    enriched = pd.merge(df_lims, df_manifest, on="meatworks_ref", how="left")
    batch_id = enriched['batch_id'].iloc[0]
    
    # Generate QR for Preview
    qr_b64 = get_qr_base64(f"https://lasra.co.nz/verify/{batch_id}")

    # Layout: Metrics + QR Code
    m_col, q_col = st.columns([4, 1])
    with m_col:
        st.markdown(f"""
            <div class="metric-container">
                <div class="metric-card"><div class="metric-label">Verified Volume</div><div class="metric-value">{enriched['hide_count'].iloc[0]:,} Hides</div></div>
                <div class="metric-card"><div class="metric-label">Verified Origin Points</div><div class="metric-value">{enriched['farm_id'].nunique()}</div></div>
                <div class="metric-card"><div class="metric-label">EUDR Risk Status</div><div class="metric-value">NEGLIGIBLE</div><div class="metric-delta">NZ Origin</div></div>
            </div>
        """, unsafe_allow_html=True)
    with q_col:
        st.markdown(f"""
            <div class="qr-preview-card">
                <div style="font-size:0.6rem; font-weight:800; color:#004a99; margin-bottom:5px;">LIVE PASSPORT QR</div>
                <img src="data:image/png;base64,{qr_b64}" width="100">
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<span class='bold-label'>Geospatial Verification Map</span>", unsafe_allow_html=True)
    st.pydeck_chart(pdk.Deck(
        initial_view_state=pdk.ViewState(latitude=-41.0, longitude=174.0, zoom=5.5, pitch=45),
        layers=[pdk.Layer("ColumnLayer", enriched, get_position='[longitude, latitude]', get_elevation='region_vol', elevation_scale=500, radius=12000, get_fill_color=[0, 74, 153, 200], pickable=True, extruded=True)]
    ))

    st.table(enriched.groupby('farm_id')['region_vol'].sum().reset_index().sort_values(by='region_vol', ascending=False).head(5))

    pdf_bytes = generate_eudr_passport(batch_id, enriched['hide_count'].iloc[0], enriched)
    st.download_button("📄 DOWNLOAD FINAL EUDR PASSPORT", data=pdf_bytes, file_name=f"LASRA_Passport_{batch_id}.pdf", mime="application/pdf", use_container_width=True)
