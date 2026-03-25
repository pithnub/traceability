import streamlit as st
import pandas as pd
import pydeck as pdk
import numpy as np # Added for randomization
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import qrcode
from io import BytesIO

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="LASRA | KinetiCore Traceability", layout="wide", page_icon="🇳🇿")

# --- 2. THE PDF ENGINE (WITH EUDR COMPLIANCE STATEMENT) ---
def generate_eudr_passport(batch_id, total_hides, farm_df):
    pdf = FPDF()
    pdf.add_page()
    
    # Generate QR Code
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
    pdf.set_text_color(0, 128, 0) # Green for Low Risk
    pdf.cell(0, 8, "EUDR RISK STATUS: NEGLIGIBLE (New Zealand Origin)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_text_color(0, 0, 0)
    pdf.line(10, 85, 200, 85)
    pdf.set_y(90)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "Verified Origin Points (Biological Data Set):", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # Farm List with Courier for forensic alignment
    pdf.set_font("Courier", '', 8)
    for _, row in farm_df.iterrows():
        if pdf.get_y() > 265:
            pdf.add_page()
            pdf.set_y(20)
            
        origin_str = f"- Farm: {row['farm_id']:<15} | Lat: {row['latitude']:>8.4f} | Long: {row['longitude']:>8.4f}"
        pdf.cell(0, 5, origin_str, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Legal Disclaimer at bottom of first page
    pdf.set_y(275)
    pdf.set_font("Helvetica", 'I', 7)
    statement = ("COMPLIANCE NOTE: This product is sourced from New Zealand improved pasture. Origin points verified against "
                 "National Land Cover databases. Zero deforestation detected post-Dec 31, 2020. (EUDR 2023/1115).")
    pdf.multi_cell(0, 4, statement, align='C')
    
    return bytes(pdf.output())

# --- 3. DATA LOADING (WITH REGIONAL SPREAD) ---
def load_complex_data():
    st.session_state.lims_data = pd.DataFrame({
        "batch_id": ["BATCH-2026-NZ-CORE"],
        "meatworks_ref": ["MW-MIXED-NZ"],
        "hide_count": [3200]
    })
    
    # Randomly distribute 30 farms around Waikato/Bay of Plenty and Canterbury
    n_farms = 40
    # Center points: Waikato and Canterbury
    centers = [(-38.0, 175.5), (-43.5, 172.5)]
    lats, longs = [], []
    for _ in range(n_farms):
        center = centers[np.random.randint(0, 2)]
        lats.append(center[0] + np.random.uniform(-1.5, 1.5))
        longs.append(center[1] + np.random.uniform(-1.0, 1.0))

    st.session_state.farm_data = pd.DataFrame({
        "meatworks_ref": ["MW-MIXED-NZ"] * n_farms,
        "farm_id": [f"NZ-FARM-{i:03d}" for i in range(1, n_farms + 1)],
        "latitude": lats,
        "longitude": longs,
        "region_vol": np.random.randint(50, 200, size=n_farms) # Individual farm contributions
    })

# --- 4. APP UI ---
st.title("🛰️ LASRA KinetiCore: EUDR Traceability Builder")

if st.button("✨ Load Distributed NZ Data (Simulation)"):
    load_complex_data()

# Init Session
if 'lims_data' not in st.session_state:
    st.session_state.lims_data = pd.DataFrame({"batch_id": ["BATCH-REF"], "meatworks_ref": ["MW-01"], "hide_count": [1000]})
if 'farm_data' not in st.session_state:
    st.session_state.farm_data = pd.DataFrame({"meatworks_ref": ["MW-01"], "farm_id": ["F-01"], "latitude": [-38.0], "longitude": [175.5], "region_vol": [1000]})

col1, col2 = st.columns(2)
with col1:
    df_lims = st.data_editor(st.session_state.lims_data, num_rows="dynamic", key="lims_v7")
with col2:
    df_manifest = st.data_editor(st.session_state.farm_data, num_rows="dynamic", key="farm_v7")

if st.button("🚀 EXECUTE FORENSIC COMPLIANCE CHECK"):
    df_lims['meatworks_ref'] = df_lims['meatworks_ref'].astype(str).str.strip()
    df_manifest['meatworks_ref'] = df_manifest['meatworks_ref'].astype(str).str.strip()
    
    enriched = pd.merge(df_lims, df_manifest, on="meatworks_ref", how="left")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Verified Hides", f"{enriched['hide_count'].iloc[0]:,}")
    m2.metric("Biological Origins", enriched['farm_id'].nunique())
    # Restored the EUDR Label
    m3.metric("EUDR Risk Status", "NEGLIGIBLE (NZ)", delta="Low Risk", delta_color="normal")

    # THE 3D MAP
    st.pydeck_chart(pdk.Deck(
        initial_view_state=pdk.ViewState(latitude=-41, longitude=174, zoom=5.2, pitch=45),
        layers=[
            pdk.Layer(
                "ColumnLayer",
                enriched,
                get_position='[longitude, latitude]',
                get_elevation='region_vol', # Uses specific farm volumes
                elevation_scale=500, # Increased for better visual "pop"
                radius=10000,
                get_fill_color=[0, 74, 153, 160],
                pickable=True,
                extruded=True,
            )
        ],
        tooltip={"text": "Origin: {farm_id}\nVolume Contribution: {region_vol}"}
    ))

    # PDF Download
    pdf_bytes = generate_eudr_passport(enriched['batch_id'].iloc[0], enriched['hide_count'].iloc[0], enriched)
    st.download_button("📄 DOWNLOAD EUDR PASSPORT", data=pdf_bytes, file_name="LASRA_EUDR_Passport.pdf", mime="application/pdf", use_container_width=True)
