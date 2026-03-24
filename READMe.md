# 🛰️ LASRA EUDR Traceability Builder

### Bridging the 'Data Divide' for New Zealand Leather Exports

This Streamlit-based "Middleware" prototype demonstrates how the New Zealand leather industry can meet the **EU Deforestation Regulation (EUDR 2023/1115)** requirements using digital automation. 

## 📖 The Problem
EUDR mandates that every hide exported to the EU must be linked to a specific geolocation "Plot of Land." For many tanners, this data exists in disparate sources (Legacy LIMS exports, Meat Works manifests, and paper kill-sheets), creating a significant administrative burden.

## 💡 The Solution
The **LASRA Traceability Builder** acts as a digital wrapper. It allows tanners to:
- **Aggregate Data:** Group thousands of hides into manageable batches.
- **Normalize Inputs:** Automatically join legacy LIMS text data with geospatial coordinates.
- **Visualize Compliance:** View a 3D spatial verification of farm origins across New Zealand.
- **Export Proof:** Generate a QR-coded "Digital Passport" PDF for international customs agents.

## 🛠️ Tech Stack
- **Frontend:** [Streamlit](https://streamlit.io/)
- **Data Engine:** Pandas & Geopandas
- **Mapping:** PyDeck (3D Column Layers)
- **Export:** FPDF2 & QRCode

## 🚀 Deployment
This app is designed to be hosted on **Streamlit Community Cloud**. 

1. Ensure `requirements.txt` is present in the root directory.
2. Link this GitHub repository to your Streamlit Cloud account.
3. The app will automatically deploy and remain synced with this repository.

---
© 2026 New Zealand Leather & Shoe Research Association Inc. (LASRA)