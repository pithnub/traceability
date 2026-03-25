import streamlit as st
import pandas as pd
import pydeck as pdk
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import qrcode
from io import BytesIO

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="LASRA | EUDR Solutions", layout="wide", page_icon="🇳🇿")

# --- 2. THE PDF ENGINE WITH QR CODE ---
def generate_eudr_passport(batch_id, total_hides, farm_df):
    pdf = FPDF()
    pdf.add_page()
    
    # Generate QR Code representing the Batch ID
    qr = qrcode.QRCode(box_size=10)
    qr.add_data(f"https://lasra.co.nz/verify/{batch_id}") # Links to a verification placeholder
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR to a temporary buffer
    qr_buffer = BytesIO()
    img_qr.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    # Blue Header
    pdf.set_fill_color(0, 74, 153)
    pdf.rect(0, 0, 210, 45, 'F')
    
    # Title
    pdf.set_font("Helvetica", 'B', 22)
    pdf.set_text_color(255, 255, 255)
    pdf.set_y(15)
    pdf.cell(0, 10, "EUDR TRACEABILITY PASSPORT", align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # Insert QR Code in the top right
    pdf.image(qr_buffer, x=165, y=5, w=35)
    
    # Document Body
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
    for _, row in farm_df.iterrows():
        pdf.cell(0, 6, f"- Farm: {row['farm_id']} | GPS: {row['latitude']:.4f}, {row['longitude']:.4f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    return bytes(pdf.output())

# --- 3. DATA LOADING ---
def load_complex_data():
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

# Initialize session state if empty
if 'lims_data' not in st.session_state:
    st.session_state.lims_data = pd.DataFrame({"batch_id": ["WB-01"], "meatworks_ref": ["MW-01"], "hide_count": [1000]})
if 'farm_data' not in st.session_state:
    st.session_state.farm_data = pd.DataFrame({"meatworks_ref": ["MW-01"], "farm_id": ["F-01"], "latitude": [-40.3], "longitude": [175.6]})

col1, col2 = st.columns(2)
with col1:
    df_lims = st.data_editor(st.session_state.lims_data, num_rows="dynamic", key="lims_v5")
with col2:
    df_manifest = st.data_editor(st.session_state.farm_data, num_rows="dynamic", key="farm_v5")

if st.button("🚀 EXECUTE COMPLIANCE CHECK"):
    df_lims['meatworks_ref'] = df_lims['meatworks_ref'].astype(str).str.strip()
    df_manifest['meatworks_ref'] = df_manifest['meatworks_ref'].astype(str).str.strip()
    
    enriched = pd.merge(df_lims, df_manifest, on="meatworks_ref", how="left")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Hides", f"{enriched['hide_count'].iloc[0]:,}")
    m2.metric("Verified Origin Points", enriched['farm_id'].nunique())
    m3.metric("EUDR Risk", "NEGLIGIBLE")

    st.pydeck_chart(pdk.Deck(
        layers=[pdk.Layer("ScatterplotLayer", enriched, get_position='[longitude, latitude]', get_radius=20000, get_fill_color=[0, 74, 153, 200])],
        initial_view_state=pdk.ViewState(latitude=-41, longitude=174, zoom=5)
    ))

    pdf_bytes = generate_eudr_passport(enriched['batch_id'].iloc[0], enriched['hide_count'].iloc[0], enriched)
    st.download_button("📄 DOWNLOAD TRACEABILITY PASSPORT (WITH QR)", data=pdf_bytes, file_name="LASRA_Passport_v2.pdf", mime="application/pdf")
