import streamlit as st
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime, timedelta

# Page setup

st.set_page_config(page_title="Apple Health Dashboard", layout="wide")
st.title("Apple Health Digital Twin")

MAX_RECORDS = 50000  # Limit for faster processing

# File upload

uploaded_file = st.file_uploader("Upload your export.zip", type="zip")

if uploaded_file is not None:
try:
with zipfile.ZipFile(uploaded_file, "r") as z:
export_files = [f for f in z.namelist() if f.endswith("export.xml")]
if not export_files:
st.error("No export.xml found in ZIP.")
else:
xml_path = export_files[0]
st.info(f"{xml_path} found. Processing...")

```
            with z.open(xml_path) as f:
                records = []
                count = 0
                progress_bar = st.progress(0.0)
                thirty_days_ago = datetime.now() - timedelta(days=30)

                for event, elem in ET.iterparse(f, events=("end",)):
                    if elem.tag == "Record":
                        r = elem.attrib
                        if r.get("type") in [
                            "HKQuantityTypeIdentifierBodyMass",
                            "HKQuantityTypeIdentifierHeight",
                            "HKQuantityTypeIdentifierStepCount",
                            "HKQuantityTypeIdentifierHeartRate"
                        ]:
                            try:
                                record_date = datetime.fromisoformat(r.get("startDate"))
                            except Exception:
                                continue
                            if record_date >= thirty_days_ago or r.get("type") in [
                                "HKQuantityTypeIdentifierBodyMass",
                                "HKQuantityTypeIdentifierHeight"
                            ]:
                                records.append({
                                    "Datum": r.get("startDate"),
                                    "Typ": r.get("type"),
                                    "Wert": r.get("value")
                                })
                        elem.clear()
                        count += 1
                        if count % 5000 == 0:
                            progress_bar.progress(min(count / MAX_RECORDS, 1.0))
                        if count >= MAX_RECORDS:
                            break

                @st.cache_data
                def process_records(records):
                    df = pd.DataFrame(records)
                    df["Datum"] = pd.to_datetime(df["Datum"], errors="coerce")
                    df["Wert"] = pd.to_numeric(df["Wert"], errors="coerce")
                    return df.dropna(subset=["Datum", "Wert"])

                df = process_records(records)
                st.success(f"{len(df)} records processed.")

                # Calculate BMI and age
                height_df = df[df["Typ"] == "HKQuantityTypeIdentifierHeight"].copy()
                weight_df = df[df["Typ"] == "HKQuantityTypeIdentifierBodyMass"].copy()
                if not height_df.empty and not weight_df.empty:
                    latest_height = height_df.sort_values("Datum").iloc[-1]["Wert"] / 100
                    latest_weight = weight_df.sort_values("Datum").iloc[-1]["Wert"]
                    bmi = latest_weight / (latest_height ** 2)
                    age = datetime.now().year - df["Datum"].dt.year.min()
                    st.metric("BMI", f"{bmi:.1f}")
                    st.metric("Estimated Data Span (Years)", f"{age}")

                # Steps and heart rate for last 30 days
                df_recent = df[df["Datum"] >= thirty_days_ago]
                if not df_recent.empty:
                    df_daily = df_recent.groupby(["Datum", "Typ"])["Wert"].mean().unstack()
                    st.subheader("Last 30 Days: Activity and Heart Rate")
                    st.line_chart(df_daily)

except zipfile.BadZipFile:
    st.error("Uploaded file is not a valid ZIP archive.")
```
