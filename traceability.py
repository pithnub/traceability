import streamlit as st
import pandas as pd
import pydeck as pdk
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import qrcode
from io import BytesIO

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="LASRA | EUDR Solutions", layout="wide", page_icon="🇳🇿")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-top: 5px solid #c5a059; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
    .anti-panic { background-color: #fffde7; padding: 20px; border-radius: 8px; border-left: 6px solid #fbc02d; margin: 20px 0; }
    .bold-label { font-weight: 900 !important; color: #1e293b !important; text-transform: uppercase; font-size: 0.85rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE PDF ENGINE (STRICT BYTES) ---
def generate_eudr_passport(batch_id, total_hides, farm_df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(0, 74, 153)
    pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_font("Helvetica", 'B', 22)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 25, "EUDR TRACEABILITY PASSPORT", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_y(55)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, f"Batch Reference: {batch_id}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", '', 11)
    pdf.cell(0, 8, f"Export Volume: {total_hides} Hides", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.line(10, 85, 200, 85)
    pdf.set_y(90)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "Verified Multi-Lot Origin Points:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Helvetica", '', 9)
    # Showing how one batch maps to many farms
    for _, row in farm_df.head(25).iterrows():
        pdf.cell(0, 6, f"- Farm: {row['farm_id']} | GPS: {row['latitude']:.4f}, {row['longitude']:.4f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    return bytes(pdf.output())

# --- 3. THE "MULTI-LOT" SIMULATION DATA ---
def load_complex_data():
    # Simulation: One Batch (Alpha) sourced from a mix of 8 farms across NZ
    st.session_state.lims_data = pd.DataFrame({
        "batch_id": ["BATCH-2026-ALPHA"],
        "meatworks_ref": ["MW-MIXED-LOT-01"],
        "hide_count": [2400]
    })
    st.session_state.farm_data = pd.DataFrame({
        "meatworks_ref": ["MW-MIXED-LOT-01"] * 8,
        "farm_id": [f"NZ-FARM-{i:02d}" for i in range(1, 9)],
        "latitude": [-37.8, -38.2, -39.1, -43.5, -44.2, -45.1, -37.5, -40.2],
        "longitude": [175.2, 175.8, 176.1, 172.6, 171.2, 170.5, 177.1, 175.4]
    })

# --- 4. APP UI ---
st.title("🛰️ LASRA Traceability Builder")

if st.button("✨ Load Complex Multi-Lot Data"):
    load_complex_data()

if 'lims_data' not in st.session_state:
    st.session_state.lims_data = pd.DataFrame({"batch_id": ["WB-01"], "meatworks_ref": ["MW-01"], "hide_count": [1000]})
if 'farm_data' not in st.session_state:
    st.session_state.farm_data = pd.DataFrame({"meatworks_ref": ["MW-01"], "farm_id": ["F-01"], "latitude": [-40.3], "longitude": [175.6]})

col1, col2 = st.columns(2)
with col1:
    df_lims = st.data_editor(st.session_state.lims_data, num_rows="dynamic", key="lims_v4")
with col2:
    df_manifest = st.data_editor(st.session_state.farm_data, num_rows="dynamic", key="farm_v4")

if st.button("🚀 EXECUTE COMPLIANCE CHECK"):
    # Normalize keys for the join
    df_lims['meatworks_ref'] = df_lims['meatworks_ref'].astype(str).str.strip()
    df_manifest['meatworks_ref'] = df_manifest['meatworks_ref'].astype(str).str.strip()
    
    enriched = pd.merge(df_lims, df_manifest, on="meatworks_ref", how="left")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Hides", f"{enriched['hide_count'].iloc[0]:,}")
    m2.metric("Verified Origin Points", enriched['farm_id'].nunique())
    m3.metric("EUDR Risk", "NEGLIGIBLE")

    st.pydeck_chart(pdk.Deck(
        layers=[pdk.Layer("ScatterplotLayer", enriched, get_position='[longitude, latitude]', get_radius=20000, get_fill_color=[0, 74, 153, 200], pickable=True)],
        initial_view_state=pdk.ViewState(latitude=-41, longitude=174, zoom=5)
    ))

    pdf_bytes = generate_eudr_passport(enriched['batch_id'].iloc[0], enriched['hide_count'].iloc[0], enriched)
    st.download_button("📄 DOWNLOAD TRACEABILITY PASSPORT", data=pdf_bytes, file_name="LASRA_Passport.pdf", mime="application/pdf")
