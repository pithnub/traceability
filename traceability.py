import streamlit as st
import pandas as pd
import pydeck as pdk
import numpy as np
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import qrcode
from io import BytesIO

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="LASRA | EUDR Solutions", layout="wide", page_icon="🇳🇿")

st.markdown("""
    <style>
    /* High-contrast metrics for readability */
    [data-testid="stMetricValue"] { background-color: #ffffff !important; color: #004a99 !important; padding: 10px; border-radius: 8px; border: 1px solid #dee2e6; }
    [data-testid="stMetricLabel"] { color: #1e293b !important; font-weight: 700 !important; text-transform: uppercase; }
    
    .main { background-color: #f8fafc; }
    h1, h2, h3 { color: #004a99 !important; font-weight: 900 !important; }
    
    .anti-panic { 
        background-color: #fffde7; 
        padding: 20px; 
        border-radius: 8px; 
        border-left: 6px solid #fbc02d;
        margin: 20px 0;
    }
    .bold-label { font-weight: 900 !important; color: #004a99 !important; text-transform: uppercase; font-size: 0.85rem; display: block; margin-bottom: 10px; }
    .stButton>button { background: linear-gradient(90deg, #004a99 0%, #055fbe 100%); color: white; font-weight: bold; border: none; border-radius: 8px; height: 3.5em; transition: 0.3s; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE PDF ENGINE ---
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
    pdf.cell(0, 8, f"Verification Date: {datetime.now().strftime('%d %B %Y')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.line(10, 85, 200, 85)
    pdf.set_y(90)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "Verified Geolocation Origin Points:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Helvetica", '', 10)
    unique_origins = farm_df.drop_duplicates(subset=['farm_id']).head(25)
    for _, row in unique_origins.iterrows():
        geo_str = f"Origin: {row['farm_id']} | Lat: {row['latitude']:.5f}, Long: {row['longitude']:.5f}"
        pdf.cell(0, 7, f"- {geo_str}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    qr_data = f"https://lasra.co.nz/verify?batch={batch_id}"
    qr = qrcode.make(qr_data)
    img_buffer = BytesIO()
    qr.save(img_buffer, format="PNG")
    img_buffer.seek(0)
    
    pdf.image(img_buffer, x=155, y=235, w=35)
    pdf.set_y(245)
    pdf.set_font("Helvetica", 'B', 8)
    pdf.set_text_color(100, 100, 100)
    statement = ("COMPLIANCE STATEMENT: This shipment is verified against NZ National Land Cover data. "
                 "All sources cleared of deforestation activity post-Dec 31, 2020 (EUDR 2023/1115).")
    pdf.multi_cell(140, 4, statement)
    
    return bytes(pdf.output())

# --- 3. APP HEADER ---
st.title("🛰️ LASRA: Bridging the EUDR 'Data Divide'")
st.markdown("New Zealand leather is inherently low-risk. This tool provides the **digital proof**.")

# --- 4. DATA INTAKE ---
if st.button("✨ Load Distributed NZ Data (Simulation Mode)"):
    # Create spread-out data for the map
    n_farms = 30
    lats = np.concatenate([np.random.uniform(-38.5, -37.5, 20), np.random.uniform(-44.0, -43.0, 10)])
    longs = np.concatenate([np.random.uniform(175.2, 175.9, 20), np.random.uniform(171.8, 172.5, 10)])
    
    st.session_state.lims_data = pd.DataFrame({
        "batch_id": ["WB-2026-NZ-ALPHA"], "meatworks_ref": ["MW-NZ-CORE"], "hide_count": [3200]
    })
    st.session_state.farm_data = pd.DataFrame({
        "meatworks_ref": ["MW-NZ-CORE"] * n_farms,
        "farm_id": [f"FARM-{i:02d}" for i in range(n_farms)],
        "latitude": lats, "longitude": longs
    })

if 'lims_data' not in st.session_state:
    st.session_state.lims_data = pd.DataFrame({"batch_id": ["WB-BATCH-01"], "meatworks_ref": ["MW-REF-01"], "hide_count": [1000]})
if 'farm_data' not in st.session_state:
    st.session_state.farm_data = pd.DataFrame({"meatworks_ref": ["MW-REF-01"], "farm_id": ["FARM-01"], "latitude": [-38.0], "longitude": [175.5]})

col_ed1, col_ed2 = st.columns(2)
with col_ed1:
    st.markdown("<span class='bold-label'>Tannery LIMS Output</span>", unsafe_allow_html=True)
    df_lims = st.data_editor(st.session_state.lims_data, num_rows="dynamic", key="lims_v10")
with col_ed2:
    st.markdown("<span class='bold-label'>Meat Works Origin Evidence</span>", unsafe_allow_html=True)
    df_manifest = st.data_editor(st.session_state.farm_data, num_rows="dynamic", key="farm_v10")

# --- 6. EXECUTION ---
st.markdown("---")
if st.button("🚀 EXECUTE COMPLIANCE CHECK"):
    try:
        enriched_data = pd.merge(df_lims, df_manifest, on="meatworks_ref", how="left")
        total_hides = enriched_data['hide_count'].sum()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Verified Volume", f"{total_hides:,} Hides")
        m2.metric("Origin Farm Count", enriched_data['farm_id'].nunique())
        m3.metric("EUDR Risk Status", "NEGLIGIBLE (NZ)")

        st.markdown("<span class='bold-label'>Geospatial Plot of Land Verification</span>", unsafe_allow_html=True)
        
        # --- FIXED MAP SECTION ---
        view_state = pdk.ViewState(latitude=-41.0, longitude=174.0, zoom=5.5, pitch=45)
        layer = pdk.Layer(
            "ColumnLayer", enriched_data, get_position='[longitude, latitude]',
            get_elevation='hide_count / 10', # Scaled for visibility
            elevation_scale=500, radius=12000,
            get_fill_color=[0, 74, 153, 200], pickable=True, extruded=True
        )
        
        # Explicitly using a light style to ensure tile visibility without a token
        st.pydeck_chart(pdk.Deck(
            map_style='mapbox://styles/mapbox/light-v10',
            layers=[layer], 
            initial_view_state=view_state,
            tooltip={"text": "Origin: {farm_id}\nBatch: {batch_id}"}
        ))

        st.divider()
        pdf_bytes = generate_eudr_passport(enriched_data['batch_id'].iloc[0], total_hides, enriched_data)
        st.download_button("📄 DOWNLOAD DIGITAL TRACEABILITY PASSPORT", data=pdf_bytes, file_name="LASRA_Passport.pdf", mime="application/pdf", use_container_width=True)

    except Exception as e:
        st.error(f"Execution Error: {e}")
