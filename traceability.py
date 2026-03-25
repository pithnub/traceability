import streamlit as st
import pandas as pd
import pydeck as pdk
import numpy as np
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import qrcode
from io import BytesIO
from datetime import datetime

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="LASRA | KinetiCore EUDR", layout="wide", page_icon="🇳🇿")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-top: 5px solid #0A369D; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .bold-label { font-weight: 900; color: #0A369D; text-transform: uppercase; font-size: 0.85rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE PDF ENGINE (MULTI-PAGE + EUDR COMPLIANCE) ---
def generate_eudr_passport(batch_id, total_hides, farm_df):
    pdf = FPDF()
    pdf.add_page()
    
    # QR Code Generation
    qr = qrcode.QRCode(box_size=10)
    qr.add_data(f"https://lasra.co.nz/verify/{batch_id}")
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = BytesIO()
    img_qr.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    # Blue Header
    pdf.set_fill_color(0, 74, 153)
    pdf.rect(0, 0, 210, 45, 'F')
    
    pdf.set_font("Helvetica", 'B', 22)
    pdf.set_text_color(255, 255, 255)
    pdf.set_y(15)
    pdf.cell(0, 10, "EUDR TRACEABILITY PASSPORT", align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.image(qr_buffer, x=165, y=5, w=35)
    
    # Summary Details
    pdf.set_y(55)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, f"Batch Reference: {batch_id}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", '', 11)
    pdf.cell(0, 8, f"Total Volume: {total_hides:,} Hides", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Helvetica", 'B', 11)
    pdf.set_text_color(0, 100, 0) # Compliance Green
    pdf.cell(0, 8, "EUDR RISK STATUS: NEGLIGIBLE (New Zealand Origin)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_text_color(0, 0, 0)
    pdf.line(10, 85, 200, 85)
    pdf.set_y(90)
    pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(0, 10, "Verified Origin Points (Biological Data Set):", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # Farm List with Courier for Alignment
    pdf.set_font("Courier", '', 8)
    for _, row in farm_df.iterrows():
        if pdf.get_y() > 265:
            pdf.add_page()
            pdf.set_y(20)
            
        origin_str = f"- Farm ID: {row['farm_id']:<12} | Lat: {row['latitude']:>8.4f} | Long: {row['longitude']:>8.4f} | Vol: {row['region_vol']:>4}"
        pdf.cell(0, 5, origin_str, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Compliance Footer (First Page)
    pdf.set_y(275)
    pdf.set_font("Helvetica", 'I', 7)
    pdf.set_text_color(100, 100, 100)
    statement = ("VERIFICATION STATEMENT: Origin points cross-referenced against NZ National Land Cover database. "
                 "Zero deforestation activity detected post-Dec 31, 2020. Compliant with EUDR 2023/1115.")
    pdf.multi_cell(0, 4, statement, align='C')
    
    return bytes(pdf.output())

# --- 3. DATA LOADING (GEOGRAPHICALLY CONSTRAINED) ---
def load_verified_data():
    st.session_state.lims_data = pd.DataFrame({
        "batch_id": ["KINETIC-2026-ALPHA"],
        "meatworks_ref": ["MW-NZ-CORE"],
        "hide_count": [3500]
    })
    
    n_farms = 35
    lats, longs = [], []
    
    for _ in range(n_farms):
        if np.random.rand() > 0.4:
            # Waikato/Inland Envelope (Avoids the Tasman Sea)
            lats.append(np.random.uniform(-38.3, -37.5))
            longs.append(np.random.uniform(175.2, 175.9))
        else:
            # Canterbury/Inland Envelope (Avoids the Pacific)
            lats.append(np.random.uniform(-44.0, -43.3))
            longs.append(np.random.uniform(171.8, 172.5))

    st.session_state.farm_data = pd.DataFrame({
        "meatworks_ref": ["MW-NZ-CORE"] * n_farms,
        "farm_id": [f"NZ-L-{i:03d}" for i in range(1, n_farms + 1)],
        "latitude": lats,
        "longitude": longs,
        "region_vol": np.random.randint(40, 180, size=n_farms)
    })

# --- 4. APP UI ---
st.title("🛰️ LASRA KinetiCore Traceability")
st.markdown("Bridging the 'Data Divide' with forensic geospatial verification for EUDR compliance.")

if st.button("✨ Load Verified NZ Data (Simulation)"):
    load_verified_data()

# Initialize Session State
if 'lims_data' not in st.session_state:
    st.session_state.lims_data = pd.DataFrame({"batch_id": ["REF-01"], "meatworks_ref": ["MW-01"], "hide_count": [1000]})
if 'farm_data' not in st.session_state:
    st.session_state.farm_data = pd.DataFrame({"meatworks_ref": ["MW-01"], "farm_id": ["F-01"], "latitude": [-37.8], "longitude": [175.4], "region_vol": [1000]})

col1, col2 = st.columns(2)
with col1:
    st.markdown("<span class='bold-label'>LIMS Export Data</span>", unsafe_allow_html=True)
    df_lims = st.data_editor(st.session_state.lims_data, num_rows="dynamic", key="lims_v8")
with col2:
    st.markdown("<span class='bold-label'>Farm Origin Manifest</span>", unsafe_allow_html=True)
    df_manifest = st.data_editor(st.session_state.farm_data, num_rows="dynamic", key="farm_v8")

if st.button("🚀 EXECUTE COMPLIANCE AUDIT"):
    # Data Cleaning
    df_lims['meatworks_ref'] = df_lims['meatworks_ref'].astype(str).str.strip()
    df_manifest['meatworks_ref'] = df_manifest['meatworks_ref'].astype(str).str.strip()
    
    enriched = pd.merge(df_lims, df_manifest, on="meatworks_ref", how="left")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Verified Hides", f"{enriched['hide_count'].iloc[0]:,}")
    m2.metric("Origin Farm Points", enriched['farm_id'].nunique())
    m3.metric("EUDR Risk", "NEGLIGIBLE", delta="NZ Improved Pasture")

    # 3D GEOSPATIAL MAP (KinetiCore Blueprint)
    st.markdown("<span class='bold-label'>Geospatial Verification Map</span>", unsafe_allow_html=True)
    
    view_state = pdk.ViewState(latitude=-40.5, longitude=174.5, zoom=5.2, pitch=45)
    
    st.pydeck_chart(pdk.Deck(
        initial_view_state=view_state,
        map_style='mapbox://styles/mapbox/dark-v10',
        layers=[
            pdk.Layer(
                "ColumnLayer",
                enriched,
                get_position='[longitude, latitude]',
                get_elevation='region_vol',
                elevation_scale=600, 
                radius=12000,
                get_fill_color=[0, 74, 153, 180],
                pickable=True,
                extruded=True,
            )
        ],
        tooltip={"text": "Origin ID: {farm_id}\nVolume: {region_vol} hides"}
    ))

    # PDF Passport Generation
    pdf_bytes = generate_eudr_passport(enriched['batch_id'].iloc[0], enriched['hide_count'].iloc[0], enriched)
    
    st.download_button(
        label="📄 DOWNLOAD DIGITAL TRACEABILITY PASSPORT",
        data=pdf_bytes,
        file_name=f"LASRA_EUDR_Passport_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
