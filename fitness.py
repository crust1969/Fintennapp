import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import zipfile
import os
import io
from datetime import datetime
import matplotlib.pyplot as plt

# --- Streamlit App Setup ---
st.set_page_config(page_title="Digital Health Twin", page_icon="💪", layout="wide")
st.title("💪 Dein Digitaler Gesundheitszwilling")

st.write(
    """
    Lade hier deine **Apple Health Export.zip** hoch, um deine Gesundheitsdaten zu visualisieren:
    - Gewicht, Herzfrequenz, Schritte
    - Berechnung von Alter und BMI
    - Automatische Diagramme & CSV-Download
    """
)

# --- File Upload ---
uploaded_file = st.file_uploader("📦 Apple Health Export.zip hochladen", type="zip")

if uploaded_file:
    with st.spinner("📂 Entpacke deine Apple Health Daten..."):
        extract_dir = "apple_health_export"
        if os.path.exists(extract_dir):
            import shutil
            shutil.rmtree(extract_dir)

        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(uploaded_file, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        # 🔍 Suche export.xml (egal wo im ZIP)
        xml_path = None
        for root_dir, _, files in os.walk(extract_dir):
            for file in files:
                if file.lower() == "export.xml":
                    xml_path = os.path.join(root_dir, file)
                    break
            if xml_path:
                break

        if not xml_path:
            st.error("❌ Keine export.xml im ZIP gefunden.")
            st.code(
                "So geht's richtig:\n"
                "1️⃣ Öffne auf dem iPhone die Health-App\n"
                "2️⃣ Profilbild → 'Gesundheitsdaten exportieren'\n"
                "3️⃣ Airdrop oder Mail → die ZIP-Datei hier hochladen (nicht entpacken!)"
            )
            st.stop()
        else:
            st.success(f"✅ export.xml gefunden unter: {xml_path}")

    # --- XML Parsing (schnell & speichersparend) ---
    st.write("⏳ Lese Gesundheitsdaten ein (kann einige Sekunden dauern)...")
    progress_bar = st.progress(0)
    records = []
    count = 0

    for event, elem in ET.iterparse(xml_path, events=("end",)):
        if elem.tag == "Record":
            r = elem.attrib
            if r.get("type") in [
                "HKQuantityTypeIdentifierBodyMass",
                "HKQuantityTypeIdentifierHeartRate",
                "HKQuantityTypeIdentifierStepCount",
                "HKQuantityTypeIdentifierHeight",
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
    st.success(f"✅ {len(records):,} Datensätze erfolgreich eingelesen!")

    # --- DataFrame-Erstellung ---
    df = pd.DataFrame(records)
    df["Datum"] = pd.to_datetime(df["Datum"], errors="coerce")
    df["Wert"] = pd.to_numeric(df["Wert"], errors="coerce")
    df = df.dropna(subset=["Datum", "Wert"])

    # --- Persönliche Angaben ---
    st.subheader("👤 Persönliche Angaben")
    col1, col2 = st.columns(2)
    with col1:
        birth_year = st.number_input("Geburtsjahr", min_value=1940, max_value=datetime.now().year, value=1969)
    with col2:
        height_cm = st.number_input("Körpergröße (cm)", min_value=140, max_value=210, value=180)

    age = datetime.now().year - birth_year
    st.write(f"🧠 Alter: **{age} Jahre**")

    # --- BMI-Berechnung ---
    weight_records = df[df["Typ"] == "HKQuantityTypeIdentifierBodyMass"]
    if not weight_records.empty:
        latest_weight = weight_records.sort_values("Datum").iloc[-1]["Wert"]
        bmi = latest_weight / ((height_cm / 100) ** 2)
        st.metric(label="💡 Aktueller BMI", value=f"{bmi:.1f}")
    else:
        st.warning("⚠️ Keine Gewichtsdaten gefunden.")

    # --- Visualisierung ---
    st.subheader("📊 Überblick über deine Gesundheitsdaten")

    df_daily = df.groupby(["Datum", "Typ"])["Wert"].mean().unstack()
    st.line_chart(df_daily)

    # --- Optional: Zusammenfassung ---
    st.subheader("📈 Gesundheitszusammenfassung (letzte 30 Tage)")
    last30 = df[df["Datum"] > (datetime.now() - pd.Timedelta(days=30)).date()]
    summary = last30.groupby("Typ")["Wert"].mean().round(1)
    st.write(summary)

    # --- Download ---
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="💾 Daten als CSV herunterladen",
        data=csv,
        file_name="apple_health_data.csv",
        mime="text/csv",
    )

else:
    st.info("⬆️ Bitte lade deine Apple Health **Export.zip** Datei hoch, um zu starten.")

