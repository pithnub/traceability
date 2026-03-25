import streamlit as st
import pandas as pd
import pydeck as pdk
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import qrcode
from io import BytesIO

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="LASRA | KinetiCore Traceability", layout="wide", page_icon="🇳🇿")

# --- 2. THE PDF ENGINE (WITH MULTI-PAGE AUTO-FLOW) ---
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

    # Header Logic
    pdf.set_fill_color(0, 74, 153)
    pdf.rect(0, 0, 210, 45, 'F')
    
    pdf.set_font("Helvetica", 'B', 22)
    pdf.set_text_color(255, 255, 255)
    pdf.set_y(15)
    pdf.cell(0, 10, "TRACEABILITY PASSPORT", align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.image(qr_buffer, x=165, y=5, w=35)
    
    # Summary Details
    pdf.set_y(55)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, f"Batch Reference: {batch_id}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", '', 11)
    pdf.cell(0, 8, f"Total Volume: {total_hides:,} Hides", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.line(10, 80, 200, 80)
    pdf.set_y(85)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "Verified Origin Points (Biological Data Set):", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # Farm List with Auto-Page Break
    pdf.set_font("Courier", '', 9) # Courier for better alignment
    for _, row in farm_df.iterrows():
        # Check if we are near the bottom of the page (270mm)
        if pdf.get_y() > 270:
            pdf.add_page()
            pdf.set_y(20) # Start fresh on new page
            
        origin_str = f"- Farm: {row['farm_id']:<15} | GPS: {row['latitude']:>9.4f}, {row['longitude']:>9.4f}"
        pdf.cell(0, 6, origin_str, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    return bytes(pdf.output())

# --- 3. DATA LOADING ---
def load_complex_data():
    st.session_state.lims_data = pd.DataFrame({
        "batch_id": ["BATCH-2026-NZ-CORE"],
        "meatworks_ref": ["MW-MIXED-NZ"],
        "hide_count": [2450]
    })
    # Simulated 20 farms to test the page-flow
    st.session_state.farm_data = pd.DataFrame({
        "meatworks_ref": ["MW-MIXED-NZ"] * 20,
        "farm_id": [f"NZ-FARM-{i:02d}" for i in range(1, 21)],
        "latitude": [-37.8 - (i*0.1) for i in range(20)],
        "longitude": [175.2 + (i*0.05) for i in range(20)]
    })

# --- 4. APP UI ---
st.title("🛰️ LASRA KinetiCore: Traceability Builder")

if st.button("✨ Load Multi-Farm Test Data"):
    load_complex_data()

# Session State Init
if 'lims_data' not in st.session_state:
    st.session_state.lims_data = pd.DataFrame({"batch_id": ["WB-01"], "meatworks_ref": ["MW-01"], "hide_count": [1000]})
if 'farm_data' not in st.session_state:
    st.session_state.farm_data = pd.DataFrame({"meatworks_ref": ["MW-01"], "farm_id": ["F-01"], "latitude": [-40.3], "longitude": [175.6]})

col1, col2 = st.columns(2)
with col1:
    df_lims = st.data_editor(st.session_state.lims_data, num_rows="dynamic", key="lims_v6")
with col2:
    df_manifest = st.data_editor(st.session_state.farm_data, num_rows="dynamic", key="farm_v6")

if st.button("🚀 EXECUTE FORENSIC CHECK"):
    # Clean Data
    df_lims['meatworks_ref'] = df_lims['meatworks_ref'].astype(str).str.strip()
    df_manifest['meatworks_ref'] = df_manifest['meatworks_ref'].astype(str).str.strip()
    
    # Merge
    enriched = pd.merge(df_lims, df_manifest, on="meatworks_ref", how="left")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Verified Hides", f"{enriched['hide_count'].sum():,}")
    m2.metric("Biological Origins", enriched['farm_id'].nunique())
    m3.metric("KinetiCore Status", "READY")

    # THE 3D MAP (COLUMN LAYER)
    view_state = pdk.ViewState(latitude=-41, longitude=174, zoom=5.5, pitch=45)
    
    st.pydeck_chart(pdk.Deck(
        initial_view_state=view_state,
        layers=[
            pdk.Layer(
                "ColumnLayer",
                enriched,
                get_position='[longitude, latitude]',
                get_elevation='hide_count',
                elevation_scale=100,
                radius=12000,
                get_fill_color=[0, 74, 153, 180],
                pickable=True,
                extruded=True,
            )
        ],
        tooltip={"text": "Farm: {farm_id}\nVolume: {hide_count}"}
    ))

    # PDF Download
    pdf_bytes = generate_eudr_passport(enriched['batch_id'].iloc[0], enriched['hide_count'].sum(), enriched)
    st.download_button("📄 DOWNLOAD TRACEABILITY PASSPORT", data=pdf_bytes, file_name="LASRA_KinetiCore_Passport.pdf", mime="application/pdf")
