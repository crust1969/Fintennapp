import streamlit as st
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Apple Health Dashboard", layout="wide")
st.title("Apple Health Digital Twin (leichtgewichtige Version)")

uploaded_file = st.file_uploader("Lade dein export.zip hoch", type="zip")
MAX_RECORDS = 50000  # Limit reduziert für schnelle Verarbeitung

if uploaded_file is not None:
with zipfile.ZipFile(uploaded_file, "r") as z:
export_files = [f for f in z.namelist() if f.endswith("export.xml")]
if export_files:
xml_path = export_files[0]
st.info(f"{xml_path} gefunden. Verarbeitung läuft ...")

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
                        "HKQuantityTypeIdentifierHeartRate",
                    ]:
                        try:
                            record_date = datetime.fromisoformat(r.get("startDate"))
                        except:
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
            st.success(f"{len(df)} Datensätze verarbeitet.")

            # BMI & Alter berechnen
            height_df = df[df["Typ"] == "HKQuantityTypeIdentifierHeight"].copy()
            weight_df = df[df["Typ"] == "HKQuantityTypeIdentifierBodyMass"].copy()
            if not height_df.empty and not weight_df.empty:
                latest_height = height_df.sort_values("Datum").iloc[-1]["Wert"] / 100
                latest_weight = weight_df.sort_values("Datum").iloc[-1]["Wert"]
                bmi = latest_weight / (latest_height ** 2)
                age = datetime.now().year - df["Datum"].dt.year.min()
                st.metric("BMI", f"{bmi:.1f}")
                st.metric("Geschätztes Alter", f"{age} Jahre")

            # Letzte 30 Tage Schritte & Herzfrequenz
            df_recent = df[df["Datum"] >= thirty_days_ago]
            if not df_recent.empty:
                df_daily = df_recent.groupby(["Datum", "Typ"])["Wert"].mean().unstack()
                st.subheader("Letzte 30 Tage: Aktivität und Herzfrequenz")
                st.line_chart(df_daily)
    else:
        st.error("Keine export.xml in ZIP gefunden.")
```
