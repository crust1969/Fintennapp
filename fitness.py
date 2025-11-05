import zipfile
import os
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# === Einstellungen ===
ZIP_FILE = "export.zip"
XML_FILE = "export.xml"

# === ZIP entpacken ===
if not os.path.exists(XML_FILE):
    print(f"📦 Entpacke {ZIP_FILE} ...")
    with zipfile.ZipFile(ZIP_FILE, "r") as zip_ref:
        for file in zip_ref.namelist():
            if file.endswith("export.xml"):
                zip_ref.extract(file, ".")
                os.rename(file, XML_FILE)
                print(f"✅ {XML_FILE} extrahiert")
                break
else:
    print("✅ export.xml bereits vorhanden")

# === XML einlesen ===
print("📥 Lade Apple Health Daten...")
tree = ET.parse(XML_FILE)
root = tree.getroot()

records = []
for record in root.findall('Record'):
    rec = record.attrib
    records.append(rec)

df = pd.DataFrame(records)
print(f"✅ {len(df)} Datensätze geladen")

# === Nur relevante Typen auswählen ===
relevant_types = {
    "HKQuantityTypeIdentifierBodyMass": "Gewicht (kg)",
    "HKQuantityTypeIdentifierHeartRate": "Herzfrequenz (bpm)",
    "HKQuantityTypeIdentifierStepCount": "Schritte",
    "HKQuantityTypeIdentifierSleepAnalysis": "Schlaf (min)",
    "HKQuantityTypeIdentifierBloodPressureSystolic": "Blutdruck sys",
    "HKQuantityTypeIdentifierBloodPressureDiastolic": "Blutdruck dia"
}

df = df[df["type"].isin(relevant_types.keys())]
df["Datum"] = pd.to_datetime(df["startDate"]).dt.date
df["Wert"] = pd.to_numeric(df["value"], errors="coerce")
df["Messung"] = df["type"].map(relevant_types)

# === Tägliche Durchschnittswerte ===
daily = df.groupby(["Datum", "Messung"])["Wert"].mean().unstack()
daily = daily.sort_index()

print("\n📊 Gesundheits-Zusammenfassung (letzte 7 Tage):")
print(daily.tail(7).round(2))

# === Beispielhafte Kennzahlen ===
letzter_tag = daily.tail(1)
if not letzter_tag.empty:
    gewicht = letzter_tag.get("Gewicht (kg)", [None])[0]
    puls = letzter_tag.get("Herzfrequenz (bpm)", [None])[0]
    schritte = letzter_tag.get("Schritte", [None])[0]

    print("\n🧠 Gesundheitsprofil:")
    if gewicht:
        print(f"- Gewicht: {gewicht:.1f} kg")
    if puls:
        print(f"- Ruhepuls: {puls:.0f} bpm")
    if schritte:
        print(f"- Schritte: {schritte:.0f}")

# === Beispielgrafik ===
plt.figure(figsize=(10,5))
if "Herzfrequenz (bpm)" in daily.columns:
    plt.plot(daily.index, daily["Herzfrequenz (bpm)"], label="Herzfrequenz")
if "Gewicht (kg)" in daily.columns:
    plt.plot(daily.index, daily["Gewicht (kg)"], label="Gewicht")
if "Schritte" in daily.columns:
    plt.plot(daily.index, daily["Schritte"]/1000, label="Schritte (x1000)")

plt.legend()
plt.title("Verlauf – Gewicht, Puls & Schritte")
plt.xlabel("Datum")
plt.ylabel("Wert")
plt.grid(True)
plt.tight_layout()
plt.show()
