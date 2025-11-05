import streamlit as st
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
import tempfile
import os

st.set_page_config(page_title="Apple Health Digital Twin", layout="wide")
st.title("🏃‍♂️ Apple Health Digital Twin")
st.write("Upload your Apple Health `Export.zip` to analyze Weight, Heart Rate, Steps, and BMI.")

# --- Upload ZIP file ---
uploaded_file = st.file_uploader("📦 Upload Export.zip", type="zip")

if uploaded_file:
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "export.zip")
        with open(zip_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Extract ZIP
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(tmpdir)

        # Find export.xml
        xml_path = None
        for root_dir, _, files in os.walk(tmpdir):
            for f in files:
                if f == "export.xml":
                    xml_path = os.path.join(root_dir, f)
                    break
        if not xml_path:
            st.error("❌ No export.xml found inside the ZIP file.")
            st.stop()

        st.success("✅ Export.zip extracted successfully")

        # --- Parse XML ---
        records = []
        tree = ET.parse(xml_path)
        root = tree.getroot()
        for record in root.findall("Record"):
            r = record.attrib
            if r["type"] in [
                "HKQuantityTypeIdentifierBodyMass",
                "HKQuantityTypeIdentifierHeartRate",
                "HKQuantityTypeIdentifierStepCount"
            ]:
                records.append({
                    "Datum": r["startDate"],
                    "Typ": r["type"],
                    "Wert": r["value"]
                })

        df = pd.DataFrame(records)
        df["Datum"] = pd.to_datetime(df["Datum"]).dt.date
        df["Wert"] = pd.to_numeric(df["Wert"], errors="coerce")

        # --- Pivot table ---
        daily = df.groupby(["Datum", "Typ"])["Wert"].mean().unstack()

        # Rename columns
        rename_map = {
            "HKQuantityTypeIdentifierBodyMass": "Gewicht (kg)",
            "HKQuantityTypeIdentifierHeartRate": "Herzfrequenz (bpm)",
            "HKQuantityTypeIdentifierStepCount": "Schritte"
        }
        daily.rename(columns=rename_map, inplace=True)

        # --- User info ---
        st.sidebar.header("👤 Personal Data")
        birth_year = st.sidebar.number_input("Birth year", min_value=1900, max_value=2025, value=1969)
        birth_month = st.sidebar.number_input("Birth month", 1, 12, 7)
        birth_day = st.sidebar.number_input("Birth day", 1, 31, 15)
        height = st.sidebar.number_input("Height (m)", min_value=1.0, max_value=2.5, value=1.83)

        age_years = (date.today() - date(birth_year, birth_month, birth_day)).days / 365.25
        st.sidebar.write(f"🎂 Age: **{age_years:.1f} years**")

        # --- BMI Calculation ---
        if "Gewicht (kg)" in daily.columns:
            daily["BMI"] = daily["Gewicht (kg)"] / (height ** 2)

        st.subheader("📊 Summary (last 7 days)")
        st.dataframe(daily.tail(7).round(2))

        # --- Plot ---
        st.subheader(f"📈 Health Trends — Age {age_years:.1f} years")
        fig, ax = plt.subplots(figsize=(12, 6))

        if "Gewicht (kg)" in daily.columns:
            ax.plot(daily.index, daily["Gewicht (kg)"], label="Gewicht (kg)", linewidth=2)
        if "Herzfrequenz (bpm)" in daily.columns:
            ax.plot(daily.index, daily["Herzfrequenz (bpm)"], label="Puls (bpm)", alpha=0.7)
        if "Schritte" in daily.columns:
            ax.plot(daily.index, daily["Schritte"]/1000, label="Schritte (x1000)", alpha=0.6)
        if "BMI" in daily.columns:
            ax.plot(daily.index, daily["BMI"], label="BMI", linestyle="--", color="purple")

        ax.set_xlabel("Datum")
        ax.set_ylabel("Wert")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)
else:
    st.info("Please upload your `Export.zip` file to start.")

