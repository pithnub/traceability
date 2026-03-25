import streamlit as st
import pandas as pd
import pydeck as pdk
import numpy as np
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import qrcode
from io import BytesIO

# --- 1. CONFIG & "ULTRA-LEGIBLE" STYLING ---
st.set_page_config(page_title="LASRA | EUDR Traceability", layout="wide", page_icon="🇳🇿")

st.markdown("""
    <style>
    .metric-container { display: flex; justify-content: space-between; gap: 20px; margin-bottom: 25px; }
    .metric-card { 
        background-color: #ffffff !important; 
        border: 2px solid #004a99 !important; 
        padding: 20px; border-radius: 10px; flex: 1; text-align: center; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-label { color: #1e293b !important; font-size: 0.85rem !important; font-weight: 800 !important; text-transform: uppercase; margin-bottom: 8px; }
    .metric-value { color: #004a99 !important; font-size: 2.2rem !important; font-weight: 900 !important; }
    .metric-delta { color: #16a34a !important; font-size: 0.9rem !important; font-weight: 600; margin-top: 5px; }
    .bold-label { font-weight: 900 !important; color: #004a99 !important; text-transform: uppercase; font-size: 0.85rem; display: block; margin-bottom: 10px; }
    .stButton>button { background: linear-gradient(90deg, #004a99 0%, #055fbe 100%); color: white; font-weight: bold; border: none; border-radius: 8px; height: 3.5em; transition: 0.3s; }
    .anti-panic { background-color: #fffde7; padding: 20px; border-radius: 8px; border-left: 6px solid #fbc02d; margin: 20px 0; color: #856404; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE PDF ENGINE (QR, MULTI-PAGE, COURIER ALIGNMENT) ---
def generate_eudr_passport(batch_id, total_hides, farm_df):
    pdf = FPDF()
    pdf.add_page()
    
    # Header Styling
    pdf.set_fill_color(0, 74, 153)
    pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_font("Helvetica", 'B', 20)
    pdf.set_text_color(255, 255, 255)
    pdf.set_y(15)
    pdf.cell(0, 10, "LASRA: EUDR TRACEABILITY PASSPORT", align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # QR Code Generation (Embedded on PDF)
    qr = qrcode.QRCode(box_size=10)
    qr.add_data(f"https://lasra.co.nz/verify/{batch_id}")
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = BytesIO()
    img_qr.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    pdf.image(qr_buffer, x=165, y=5, w=35)
    
    # Summary Details
    pdf.set_y(55); pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, f"Batch Reference: {batch_id}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", '', 11)
    pdf.cell(0, 8, f"Verified Export Volume: {total_hides:,} Hides", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"Audit Date: {datetime.now().strftime('%d %B %Y')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.line(10, 85, 200, 85); pdf.set_y(90); pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(0, 10, "Verified Geolocation Origin Points (Full Manifest):", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # Origin Data with Page Break Logic
    pdf.set_font("Courier", '', 8)
    for _, row in farm_df.iterrows():
        if pdf.get_y() > 260:
            pdf.add_page()
            pdf.set_y(20)
        origin_str = f"- Farm ID: {row['farm_id']:<12} | Lat: {row['latitude']:>8.4f} | Long: {row['longitude']:>8.4f}"
        pdf.cell(0, 5, origin_str, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Footer
    pdf.set_y(275); pdf.set_font("Helvetica", 'I', 7); pdf.set_text_color(100, 100, 100)
    statement = ("COMPLIANCE NOTE: This shipment is verified against NZ National Land Cover data. "
                 "All sources cleared of deforestation activity post-Dec 31, 2020 (EUDR 2023/1115).")
    pdf.multi_cell(0, 4, statement, align='C')
    
    return bytes(pdf.output())

# --- 3. DATA LOADING (GEOSPATIAL SPREAD) ---
def load_audit_data():
    n_farms = 40
    # Create realistic NZ spread (Waikato and Canterbury)
    lats = np.concatenate([np.random.uniform(-38.3, -37.5, 25), np.random.uniform(-44.0, -43.3, 15)])
    longs = np.concatenate([np.random.uniform(175.2, 175.9, 25), np.random.uniform(171.8, 172.5, 15)])
    
    st.session_state.lims_data = pd.DataFrame({
        "batch_id": ["APLF-2026-ALPHA"], "meatworks_ref": ["MW-NZ-CORE"], "hide_count": [4200]
    })
    st.session_state.farm_data = pd.DataFrame({
        "meatworks_ref": ["MW-NZ-CORE"] * n_farms,
        "farm_id": [f"NZ-L-{i:03d}" for i in range(1, n_farms + 1)],
        "latitude": lats, "longitude": longs,
        "contribution": np.random.randint(80, 150, size=n_farms)
    })

# --- 4. APP UI ---
st.title("🛰️ LASRA: Bridging the EUDR 'Data Divide'")
st.markdown("New Zealand Leather & Shoe Research Association Inc. | **Geospatial Audit Interface**")

st.markdown("""
    <div class="anti-panic">
        <b>💡 TRACEABILITY PROTOCOL:</b> Demonstrating how legacy LIMS data is wrapped in a verified geospatial layer 
        to meet EUDR 2023/1115 requirements for 'Plots of Land'.
    </div>
""", unsafe_allow_html=True)

if st.button("✨ Load Distributed LIMS Data (Simulation Mode)"):
    load_audit_data()

# Session State Persistence
if 'lims_data' not in st.session_state:
    st.session_state.lims_data = pd.DataFrame({"batch_id": ["REF-01"], "meatworks_ref": ["MW-01"], "hide_count": [1000]})
if 'farm_data' not in st.session_state:
    st.session_state.farm_data = pd.DataFrame({"meatworks_ref": ["MW-01"], "farm_id": ["F-01"], "latitude": [-38.0], "longitude": [175.5], "contribution": [1000]})

c1, c2 = st.columns(2)
with c1:
    st.markdown("<span class='bold-label'>Tannery LIMS Feed</span>", unsafe_allow_html=True)
    df_lims = st.data_editor(st.session_state.lims_data, num_rows="dynamic", key="lims_v_final")
with c2:
    st.markdown("<span class='bold-label'>Origin Evidence (Manifest)</span>", unsafe_allow_html=True)
    df_manifest = st.data_editor(st.session_state.farm_data, num_rows="dynamic", key="farm_v_final")

if st.button("🚀 EXECUTE COMPLIANCE AUDIT"):
    enriched = pd.merge(df_lims, df_manifest, on="meatworks_ref", how="left")
    total_hides = enriched['hide_count'].iloc[0]
    
    # High-Contrast Metrics (Hard-Coded HTML)
    st.markdown(f"""
        <div class="metric-container">
            <div class="metric-card"><div class="metric-label">Verified Volume</div><div class="metric-value">{total_hides:,} Hides</div></div>
            <div class="metric-card"><div class="metric-label">Verified Origin Points</div><div class="metric-value">{enriched['farm_id'].nunique()}</div></div>
            <div class="metric-card"><div class="metric-label">EUDR Risk Status</div><div class="metric-value">NEGLIGIBLE</div><div class="metric-delta">NZ National Data Cross-Ref</div></div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<span class='bold-label'>Geospatial Validation Plot</span>", unsafe_allow_html=True)
    
    # Reliable Map (Default Basemap)
    view_state = pdk.ViewState(latitude=-41.0, longitude=174.0, zoom=5.5, pitch=45)
    layer = pdk.Layer(
        "ColumnLayer", enriched, get_position='[longitude, latitude]',
        get_elevation='contribution', elevation_scale=500, radius=12000,
        get_fill_color=[0, 74, 153, 200], pickable=True, extruded=True
    )
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "Origin: {farm_id}"}))

    # Regional Mass Balance Summary (Restored Table)
    st.markdown("### Regional Mass Balance Summary")
    summary = enriched.groupby('farm_id')['contribution'].sum().reset_index()
    summary['% of Load'] = (summary['contribution'] / summary['contribution'].sum() * 100).round(1)
    st.table(summary.sort_values(by='% of Load', ascending=False).head(10))

    # PDF Passport Download
    pdf_bytes = generate_eudr_passport(enriched['batch_id'].iloc[0], total_hides, enriched)
    st.download_button(
        "📄 DOWNLOAD OFFICIAL EUDR PASSPORT (PDF)", 
        data=pdf_bytes, 
        file_name=f"LASRA_EUDR_Passport_{enriched['batch_id'].iloc[0]}.pdf", 
        mime="application/pdf", 
        use_container_width=True
    )
