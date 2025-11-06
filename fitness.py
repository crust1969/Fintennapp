#!/usr/bin/env python3
import streamlit as st
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime, timedelta

# --- Streamlit App Setup ---
st.set_page_config(page_title="Apple Health Dashboard", layout="wide")
st.title("Apple Health Digital Twin")

MAX_RECORDS = 50000  # Limit für schnelle Verarbeitung

# File uploader
uploaded_file = st.file_uploader("Lade dein export.zip hoch", type="zip")

if uploaded_file is not None:
    try:
        with zipfile.ZipFile(uploaded_file, "r") as z:
            # Suche nach export.xml (auch in Unterordnern)
            export_files = [f for f in z.namelist() if f.lower().endswith("export.xml")]

            if not export_files:
                st.error("Keine export.xml in der ZIP-Datei gefunden.")
            else:
                xml_path = export_files[0]
                st.info(f"{xml_path} gefunden. Verarbeitung läuft ...")

                with z.open(xml_path) as f:
                    records = []
                    count = 0
                    progress_bar = st.progress(0.0)
                    thirty_days_ago = datetime.now() - timedelta(days=30)

                    # iteratives Parsen (speichersparend)
                    for event, elem in ET.iterparse(f, events=("end",)):
                        if elem.tag == "Record":
                            r = elem.attrib
                            typ = r.get("type")
                            if typ in [
                                "HKQuantityTypeIdentifierBodyMass",
                                "HKQuantityTypeIdentifierHeight",
                                "HKQuantityTypeIdentifierStepCount",
                                "HKQuantityTypeIdentifierHeartRate",
                            ]:
                                # Datum parsen; falls fehlerhaft -> überspringen
                                try:
                                    record_date = datetime.fromisoformat(r.get("startDate"))
                                except Exception:
                                    elem.clear()
                                    count += 1
                                    continue

                                # Nur letzte 30 Tage für Aktivitätsplots, Gewicht/Höhe immer behalten
                                if (record_date >= thirty_days_ago) or (typ in [
                                    "HKQuantityTypeIdentifierBodyMass",
                                    "HKQuantityTypeIdentifierHeight",
                                ]):
                                    records.append({
                                        "Datum": r.get("startDate"),
                                        "Typ": typ,
                                        "Wert": r.get("value"),
                                    })

                            elem.clear()
                            count += 1
                            if count % 5000 == 0:
                                progress_bar.progress(min(count / MAX_RECORDS, 1.0))
                            if count >= MAX_RECORDS:
                                break

                    progress_bar.progress(1.0)

                    @st.cache_data
                    def process_records(records_list):
                        df_local = pd.DataFrame(records_list)
                        df_local["Datum"] = pd.to_datetime(df_local["Datum"], errors="coerce")
                        df_local["Wert"] = pd.to_numeric(df_local["Wert"], errors="coerce")
                        return df_local.dropna(subset=["Datum", "Wert"])

                    df = process_records(records)
                    st.success(f"{len(df)} Datensätze verarbeitet.")

                    # BMI & Datenzeitraum berechnen (falls vorhanden)
                    height_df = df[df["Typ"] == "HKQuantityTypeIdentifierHeight"].copy()
                    weight_df = df[df["Typ"] == "HKQuantityTypeIdentifierBodyMass"].copy()

                    if (not height_df.empty) and (not weight_df.empty):
                        latest_height = height_df.sort_values("Datum").iloc[-1]["Wert"] / 100.0
                        latest_weight = weight_df.sort_values("Datum").iloc[-1]["Wert"]
                        try:
                            bmi = latest_weight / (latest_height ** 2)
                        except Exception:
                            bmi = None
                        data_start = df["Datum"].min()
                        if pd.notna(data_start):
                            data_years = datetime.now().year - data_start.year
                        else:
                            data_years = "n/a"

                        if bmi is not None:
                            st.metric("Aktueller BMI", f"{bmi:.1f}")
                        st.metric("Datenzeitraum (Jahre)", f"{data_years}")

                    # Letzte 30 Tage: Schritte & Herzfrequenz
                    df_recent = df[df["Datum"] >= thirty_days_ago]
                    if not df_recent.empty:
                        df_daily = df_recent.groupby(["Datum", "Typ"])["Wert"].mean().unstack()
                        st.subheader("Letzte 30 Tage: Aktivität und Herzfrequenz")
                        st.line_chart(df_daily)
    except zipfile.BadZipFile:
        st.error("Die hochgeladene Datei ist kein gültiges ZIP-Archiv.")
