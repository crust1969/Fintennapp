#!/usr/bin/env python3
import streamlit as st
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime, timedelta, timezone

# --- Streamlit App Setup ---
st.set_page_config(page_title="Apple Health Dashboard", layout="wide")
st.title("📊 Apple Health Digital Twin – Vollständige Analyse")

MAX_RECORDS = 100000  # Verarbeitungslimit (mehr = länger)
uploaded_file = st.file_uploader("Lade dein export.zip hoch", type="zip")

if uploaded_file is not None:
    try:
        with zipfile.ZipFile(uploaded_file, "r") as z:
            export_files = [f for f in z.namelist() if f.lower().endswith("export.xml")]

            if not export_files:
                st.error("Keine export.xml in der ZIP-Datei gefunden.")
            else:
                xml_path = export_files[0]
                st.info(f"{xml_path} gefunden. Verarbeitung läuft ...")

                # --- Auswahl der Datentypen ---
                st.sidebar.header("⚙️ Analyseoptionen")
                types_to_load = st.sidebar.multiselect(
                    "Wähle Datentypen zur Anzeige:",
                    [
                        "HKQuantityTypeIdentifierBodyMass",
                        "HKQuantityTypeIdentifierHeight",
                        "HKQuantityTypeIdentifierStepCount",
                        "HKQuantityTypeIdentifierHeartRate",
                        "HKQuantityTypeIdentifierDistanceWalkingRunning",
                    ],
                    default=[
                        "HKQuantityTypeIdentifierBodyMass",
                        "HKQuantityTypeIdentifierStepCount",
                        "HKQuantityTypeIdentifierHeartRate",
                    ]
                )

                days_back = st.sidebar.slider("Zeitraum (Tage zurück)", 7, 365, 90)
                time_limit = datetime.now(timezone.utc) - timedelta(days=days_back)

                with z.open(xml_path) as f:
                    records = []
                    count = 0
                    progress_bar = st.progress(0.0)

                    for event, elem in ET.iterparse(f, events=("end",)):
                        if elem.tag == "Record":
                            r = elem.attrib
                            typ = r.get("type")

                            if typ in types_to_load:
                                try:
                                    record_date = datetime.fromisoformat(
                                        r.get("startDate").replace("Z", "+00:00")
                                    )
                                except Exception:
                                    elem.clear()
                                    count += 1
                                    continue

                                if record_date >= time_limit or typ in [
                                    "HKQuantityTypeIdentifierBodyMass",
                                    "HKQuantityTypeIdentifierHeight",
                                ]:
                                    records.append({
                                        "Datum": record_date,
                                        "Typ": typ,
                                        "Wert": r.get("value")
                                    })

                            elem.clear()
                            count += 1
                            if count % 5000 == 0:
                                progress_bar.progress(min(count / MAX_RECORDS, 1.0))
                            if count >= MAX_RECORDS:
                                break

                    progress_bar.progress(1.0)

                    # --- DataFrame-Erstellung ---
                    if not records:
                        st.warning("Keine passenden Daten gefunden. Ändere Filter oder Zeitraum.")
                    else:
                        df = pd.DataFrame(records)
                        df["Wert"] = pd.to_numeric(df["Wert"], errors="coerce")
                        df = df.dropna(subset=["Wert"])
                        st.success(f"{len(df)} Datensätze verarbeitet.")

                        # --- Rohdatenanzeige ---
                        with st.expander("📋 Rohdaten anzeigen"):
                            st.dataframe(df)

                        # --- BMI-Berechnung ---
                        height_df = df[df["Typ"] == "HKQuantityTypeIdentifierHeight"]
                        weight_df = df[df["Typ"] == "HKQuantityTypeIdentifierBodyMass"]
                        if not height_df.empty and not weight_df.empty:
                            latest_height = height_df.sort_values("Datum").iloc[-1]["Wert"] / 100
                            latest_weight = weight_df.sort_values("Datum").iloc[-1]["Wert"]
                            bmi = latest_weight / (latest_height ** 2)
                            st.metric("BMI", f"{bmi:.1f}")

                        # --- Durchschnittswerte ---
                        avg_vals = df.groupby("Typ")["Wert"].mean().round(2)
                        st.subheader("Durchschnittswerte im Zeitraum")
                        st.dataframe(avg_vals)

                        # --- Zeitverlauf ---
                        st.subheader("📈 Verlauf über Zeit")
                        df_chart = df.groupby(["Datum", "Typ"])["Wert"].mean().unstack()
                        st.line_chart(df_chart)

    except zipfile.BadZipFile:
        st.error("Die hochgeladene Datei ist kein gültiges ZIP-Archiv.")
