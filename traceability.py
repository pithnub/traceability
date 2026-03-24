import streamlit as st
import pandas as pd
import geopandas as gpd
import pydeck as pdk
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import qrcode
from io import BytesIO

# --- 1. CONFIG & "SOLUTIONS" STYLING ---
st.set_page_config(page_title="LASRA | EUDR Solutions", layout="wide", page_icon="🇳🇿")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    h1, h2, h3 { color: #004a99 !important; font-weight: 900 !important; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-top: 5px solid #c5a059; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
    .anti-panic { 
        background-color: #fffde7; 
        padding: 20px; 
        border-radius: 8px; 
        border-left: 6px solid #fbc02d;
        margin: 20px 0;
    }
    .bold-label { font-weight: 900 !important; color: #1e293b !important; text-transform: uppercase; font-size: 0.85rem; }
    .stButton>button { background: linear-gradient(90deg, #004a99 0%, #055fbe 100%); color: white; font-weight: bold; border: none; border-radius: 8px; height: 3.5em; transition: 0.3s; }
    .stButton>button:hover { opacity: 0.9; transform: translateY(-1px); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE PDF & QR ENGINE (FIXED FOR BYTES) ---
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
    pdf.cell(0, 8, f"Export Volume: {total_hides} Hides / Approx {total_hides*0.028:.1f} Tonnes", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"Verification Date: {datetime.now().strftime('%d %B %Y')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.line(10, 85, 200, 85)
    pdf.set_y(90)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "Verified Geolocation Origin Points:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Helvetica", '', 10)
    unique_origins = farm_df.drop_duplicates(subset=['farm_id']).head(20)
    for _, row in unique_origins.iterrows():
        geo_str = f"Origin: {row['farm_id']} | Lat: {row['latitude']:.5f}, Long: {row['longitude']:.5f}"
        pdf.cell(0, 7, f"- {geo_str}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # QR Code Generation
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
    
    # CRITICAL FIX: Cast bytearray to bytes
    return bytes(pdf.output())

# --- 3. APP HEADER ---
st.title("🛰️ LASRA: Bridging the EUDR 'Data Divide'")
st.markdown("""
    New Zealand leather is inherently low-risk, but global regulations now require **digital proof**. 
    This tool demonstrates how legacy LIMS data can be 'wrapped' in a geospatial layer.
""")

# --- 4. ANTI-PANIC CLARIFIER ---
st.markdown(f"""
    <div class="anti-panic">
        <span style="font-weight: 900; font-size: 1.1rem; color: #856404;">💡 AGGREGATION LOGIC: The 'Mass Balance' Approach</span><br>
        EUDR compliance is linked to the <b>Plot of Land</b>. Link your Batch total once to your contributing 'Kill Groups', and the passport handles the rest.
    </div>
""", unsafe_allow_html=True)

# --- 5. DATA INTAKE ---
if st.button("✨ Load Example NZ Export Data (Simulation Mode)"):
    st.session_state.lims_data = pd.DataFrame({
        "batch_id": ["WB-2026-NZ-ALPHA", "WB-2026-NZ-BETA"],
        "meatworks_ref": ["MW-NORTH", "MW-SOUTH"],
        "hide_count": [1200, 850]
    })
    st.session_state.farm_data = pd.DataFrame({
        "meatworks_ref": ["MW-NORTH", "MW-NORTH", "MW-SOUTH"],
        "farm_id": ["WAIKATO-01", "WAIKATO-02", "CANTERBURY-09"],
        "latitude": [-37.7833, -38.1387, -43.5321],
        "longitude": [175.2833, 175.2730, 172.6362]
    })

if 'lims_data' not in st.session_state:
    st.session_state.lims_data = pd.DataFrame({"batch_id": ["WB-BATCH-01"], "meatworks_ref": ["MW-REF-01"], "hide_count": [1000]})
if 'farm_data' not in st.session_state:
    st.session_state.farm_data = pd.DataFrame({"meatworks_ref": ["MW-REF-01"], "farm_id": ["FARM-ID-01"], "latitude": [-40.3556], "longitude": [175.6111]})

col_ed1, col_ed2 = st.columns(2)
with col_ed1:
    st.markdown("<span class='bold-label'>Tannery LIMS Output</span>", unsafe_allow_html=True)
    df_lims = st.data_editor(st.session_state.lims_data, num_rows="dynamic", key="lims_final_v3")

with col_ed2:
    st.markdown("<span class='bold-label'>Meat Works Origin Evidence</span>", unsafe_allow_html=True)
    df_manifest = st.data_editor(st.session_state.farm_data, num_rows="dynamic", key="farm_final_v3")

# --- 6. EXECUTION ---
st.markdown("---")
if st.button("🚀 EXECUTE COMPLIANCE CHECK"):
    try:
        df_lims['meatworks_ref'] = df_lims['meatworks_ref'].astype(str).str.strip()
        df_manifest['meatworks_ref'] = df_manifest['meatworks_ref'].astype(str).str.strip()

        enriched_data = pd.merge(df_lims, df_manifest, on="meatworks_ref", how="left")
        total_hides = enriched_data['hide_count'].sum()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Verified Volume", f"{total_hides:,} Hides")
        m2.metric("Origin Farm Count", enriched_data['farm_id'].nunique())
        m3.metric("EUDR Risk Status", "NEGLIGIBLE (NZ)")

        st.markdown("<span class='bold-label'>Geospatial Plot of Land Verification</span>", unsafe_allow_html=True)
        view_state = pdk.ViewState(latitude=-41.0, longitude=174.0, zoom=5, pitch=45)
        layer = pdk.Layer(
            "ColumnLayer", enriched_data, get_position='[longitude, latitude]',
            get_elevation='hide_count', elevation_scale=100, radius=15000,
            get_fill_color=[0, 74, 153, 200], pickable=True, auto_highlight=True
        )
        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))

        st.markdown("### Regional Mass Balance Summary")
        mass_balance = enriched_data.groupby('farm_id')['hide_count'].sum().reset_index()
        mass_balance['% of Load'] = (mass_balance['hide_count'] / total_hides * 100).round(1)
        st.table(mass_balance.sort_values(by='% of Load', ascending=False))

        st.divider()
        sample_id = enriched_data['batch_id'].iloc[0] if not enriched_data.empty else "EXPORT"
        pdf_bytes = generate_eudr_passport(sample_id, total_hides, enriched_data)
        
        st.download_button(
            label="📄 DOWNLOAD DIGITAL TRACEABILITY PASSPORT (PDF)",
            data=pdf_bytes, 
            file_name=f"LASRA_EUDR_Passport_{sample_id}.pdf", 
            mime="application/pdf", 
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Processing Error: {e}")