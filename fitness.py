import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import zipfile
import os
import io
from datetime import datetime
import matplotlib.pyplot as plt

# Streamlit App
st.set_page_config(page_title="Digital Health Twin", page_icon="💪", layout="wide")
st.title("💪 Your Digital Health Twin")

st.write("Upload your **Apple Health Export.zip** to visualize key metrics like weight, heart rate, and steps — plus calculate your BMI and trends.")

# --- File Upload ---
uploaded_file = st.file_uploader("📦 Upload Export.zip from your iPhone", type="zip")

if uploaded_file:
    with st.spinner("📂 Extracting your Apple Health data..."):
        extract_dir = "apple_health_export"
        if os.path.exists(extract_dir):
            import shutil
            shutil.rmtree(extract_dir)

        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(uploaded_file, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        # Find export.xml
       # Find export.xml anywhere inside the ZIP (even in nested folders)
xml_path = None
for root_dir, _, files in os.walk(extract_dir):
    for file in files:
        if file.lower() == "export.xml":
            xml_path = os.path.join(root_dir, file)
            break
    if xml_path:
        break

if not xml_path:
    st.error("❌ export.xml not found in your ZIP file. Please check the structure:")
    st.code(
        "How to fix:\n"
        "1️⃣ On your iPhone, open the Health app\n"
        "2️⃣ Tap your profile picture → Export All Health Data\n"
        "3️⃣ Airdrop or email the ZIP (don’t unzip it!)\n"
        "4️⃣ Upload the original ZIP file here"
    )
    st.stop()
else:
    st.success(f"✅ Found export.xml at: {xml_path}")


    # --- Parse XML incrementally ---
    st.write("⏳ Parsing XML data (this may take a few seconds)...")
    progress_bar = st.progress(0)
    records = []
    count = 0

    # Stream parse
    for event, elem in ET.iterparse(xml_path, events=("end",)):
        if elem.tag == "Record":
            r = elem.attrib
            if r.get("type") in [
                "HKQuantityTypeIdentifierBodyMass",
                "HKQuantityTypeIdentifierHeartRate",
                "HKQuantityTypeIdentifierStepCount",
                "HKQuantityTypeIdentifierHeight"
            ]:
                records.append({
                    "Datum": r.get("startDate"),
                    "Typ": r.get("type"),
                    "Wert": r.get("value")
                })
            elem.clear()
            count += 1
            if count % 10000 == 0:
                progress_bar.progress(min(count / 200000, 1.0))

    progress_bar.progress(1.0)
    st.success(f"✅ Parsed {len(records):,} records successfully!")

    # --- Convert to DataFrame ---
    df = pd.DataFrame(records)
    df["Datum"] = pd.to_datetime(df["Datum"], errors="coerce")
    df["Wert"] = pd.to_numeric(df["Wert"], errors="coerce")
    df = df.dropna(subset=["Datum", "Wert"])

    # --- User input for age ---
    st.subheader("👤 Personal Information")
    col1, col2 = st.columns(2)
    with col1:
        birth_year = st.number_input("Birth Year", min_value=1940, max_value=datetime.now().year, value=1969)
    with col2:
        height_cm = st.number_input("Height (cm)", min_value=140, max_value=210, value=180)

    age = datetime.now().year - birth_year
    st.write(f"🧠 Calculated Age: **{age} years**")

    # --- BMI Calculation (use last weight record) ---
    weight_records = df[df["Typ"] == "HKQuantityTypeIdentifierBodyMass"]
    if not weight_records.empty:
        latest_weight = weight_records.sort_values("Datum").iloc[-1]["Wert"]
        bmi = latest_weight / ((height_cm / 100) ** 2)
        st.metric(label="💡 Latest BMI", value=f"{bmi:.1f}")
    else:
        st.warning("⚠️ No weight data found in your export.")

    # --- Visualization ---
    st.subheader("📊 Health Data Overview")

    # Daily averages
    df_daily = df.groupby(["Datum", "Typ"])["Wert"].mean().unstack()
    st.line_chart(df_daily)

    # --- Data download option ---
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="💾 Download Processed Data (CSV)",
        data=csv,
        file_name="apple_health_data.csv",
        mime="text/csv",
    )

else:
    st.info("⬆️ Please upload your Apple Health **Export.zip** file to begin.")
