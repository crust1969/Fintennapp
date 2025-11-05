import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# === Einstellungen ===
FILE_PATH = "export.xml"  # Pfad zur entpackten Datei aus export.zip

# === XML einlesen ===
print("📥 Lade Apple Health Daten...")
tree = ET.parse(FILE_PATH)
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
    gewicht = letzter_tag["Gewicht (kg)"].values[0] if "Gewicht (kg)" in letzter_tag else None
    puls = letzter_tag["Herzfrequenz (bpm)"].values[0] if "Herzfrequenz (bpm)" in letzter_tag else None
    schritte = letzter_tag["Schritte"].values[0] if "Schritte" in letzter_tag else None

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



