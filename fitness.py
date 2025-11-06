import streamlit as st
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
import io
from datetime import datetime

st.set_page_config(page_title="Apple Health Dashboard", layout="wide")

st.title("📱 Apple Health Dashboard")
st.write("Lade hier deine **Apple Health Export.zip** Datei hoch, um deine Gesundheitsdaten zu analysieren.")

uploaded_file = st.file_uploader("Wähle die Export.zip Datei", type=["zip"])

# Sidebar mit KPI-Infos
st.sidebar.header("ℹ️ KPI-Erklärungen")

kpi_info = {
    "Gewicht": "Körpergewicht in Kilogramm – Grundlage für BMI-Berechnung.",
    "Größe": "Körpergröße in Zentimetern – meist einmalig gemessen.",
    "BMI": "Body-Mass-Index: Gewicht in Relation zur Körpergröße (Gesund 18.5–24.9).",
    "Schritte": "Anzahl der Schritte pro Tag – ab 7.000 gilt als gesundheitsfördernd.",
    "Herzfrequenz": "Herzschläge pro Minute – Ruhepuls meist zwischen 60 und 75 BPM.",
    "Distanz": "Zurückgelegte Strecke beim Gehen oder Laufen in Kilometern."
}

selected_kpi = st.sidebar.radio("KPI auswählen", list(kpi_info.keys()))
st.sidebar.info(kpi_info[selected_kpi])

if uploaded_file is not None:
    try:
        with zipfile.ZipFile(uploaded_file, "r") as z:
            # Suche nach der XML-Datei im ZIP
            xml_name = [f for f in z.namelist() if f.endswith("export.xml")]
            if not xml_name:
                st.error("❌ Keine export.xml in der ZIP gefunden.")
            else:
                with z.open(xml_name[0]) as xml_file:
                    st.success("📦 Export-Datei erfolgreich geladen!")
                    # XML in DataFrame umwandeln
                    tree = ET.parse(xml_file)
                    root = tree.getroot()

                    records = []
                    for record in root.findall("Record"):
                        rtype = record.attrib.get("type")
                        value = record.attrib.get("value")
                        date = record.attrib.get("startDate")

                        if rtype and value and date:
                            records.append((rtype, float(value), date))

                    df = pd.DataFrame(records, columns=["type", "value", "date"])
                    df["date"] = pd.to_datetime(df["date"], errors="coerce")

                    # Mapping von Apple Health Datentypen
                    mapping = {
                        "HKQuantityTypeIdentifierBodyMass": "Gewicht",
                        "HKQuantityTypeIdentifierHeight": "Größe",
                        "HKQuantityTypeIdentifierStepCount": "Schritte",
                        "HKQuantityTypeIdentifierHeartRate": "Herzfrequenz",
                        "HKQuantityTypeIdentifierDistanceWalkingRunning": "Distanz"
                    }
                    df["label"] = df["type"].map(mapping)

                    # Nur bekannte Typen behalten
                    df = df[df["label"].notna()]

                    # Letzte Werte bestimmen
                    latest_values = df.sort_values("date").groupby("label")["value"].last()

                    # BMI berechnen, falls Gewicht & Größe vorhanden
                    if "Gewicht" in latest_values and "Größe" in latest_values:
                        gewicht = latest_values["Gewicht"]
                        groesse_m = latest_values["Größe"] / 100
                        bmi = gewicht / (groesse_m ** 2)
                        latest_values["BMI"] = round(bmi, 2)

                    st.subheader("📊 Aktuelle Werte")
                    st.dataframe(latest_values)

                    # Verlauf pro KPI
                    kpi_mapping = {
                        "Gewicht": "HKQuantityTypeIdentifierBodyMass",
                        "Größe": "HKQuantityTypeIdentifierHeight",
                        "BMI": None,
                        "Schritte": "HKQuantityTypeIdentifierStepCount",
                        "Herzfrequenz": "HKQuantityTypeIdentifierHeartRate",
                        "Distanz": "HKQuantityTypeIdentifierDistanceWalkingRunning"
                    }

                    if selected_kpi == "BMI":
                        if "Gewicht" in df["label"].values and "Größe" in df["label"].values:
                            df_g = df[df["label"] == "Größe"].sort_values("date")
                            df_w = df[df["label"] == "Gewicht"].sort_values("date")
                            if not df_g.empty and not df_w.empty:
                                merged = pd.merge_asof(df_w, df_g, on="date", suffixes=("_w", "_g"))
                                merged["BMI"] = merged["value_w"] / ((merged["value_g"] / 100) ** 2)
                                merged = merged.dropna(subset=["BMI"])
                                st.line_chart(merged[["date", "BMI"]].set_index("date"))
                            else:
                                st.warning("Nicht genug Daten für BMI-Berechnung.")
                        else:
                            st.warning("Gewicht und Größe fehlen für BMI.")
                    else:
                        kpi_type = kpi_mapping[selected_kpi]
                        df_sel = df[df["type"] == kpi_type]
                        if not df_sel.empty:
                            st.line_chart(df_sel.set_index("date")["value"])
                        else:
                            st.warning("Keine Daten für diese KPI gefunden.")

    except Exception as e:
        st.error(f"Fehler beim Verarbeiten: {e}")
else:
    st.info("⬆️ Bitte lade zuerst deine Export.zip Datei hoch.")
