import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("💪 Digitaler Zwilling – Gesundheit & Fitness")

# Eingaben
alter = st.number_input("Alter (Jahre)", 18, 100, 56)
gewicht = st.number_input("Gewicht (kg)", 40, 150, 88)
groesse = st.number_input("Größe (cm)", 140, 210, 180)
blutdruck = st.slider("Blutdruck (mmHg)", 90, 180, 130)
puls = st.slider("Ruhepuls", 40, 120, 70)

# Berechnung BMI
bmi = gewicht / ((groesse / 100) ** 2)
st.metric("BMI", f"{bmi:.1f}")

# Einfaches Fitnessmodell (Beispiel)
fitness_index = (
    100 
    - (bmi - 22) * 2.5   # Abweichung vom Ideal-BMI
    - (blutdruck - 120) / 2 
    - (puls - 60) / 2 
    - (alter - 30) / 3
)

# Score begrenzen
fitness_index = max(0, min(100, fitness_index))

# Anzeige
st.metric("Fitness Score", f"{fitness_index:.1f}")

# Bewertungstext
if fitness_index > 75:
    st.success("🏆 Hervorragende Fitness! Weiter so!")
elif fitness_index > 50:
    st.info("💪 Gute Fitness, mit etwas Potenzial nach oben.")
else:
    st.warning("⚠️ Zeit für mehr Bewegung und Erholung.")

# Optional: Verlauf simulieren
if st.checkbox("Zeige Beispielverlauf der Fitness über 12 Wochen"):
    wochen = list(range(1, 13))
    fitness_verlauf = [max(0, fitness_index + i*0.5 - 3) for i in range(12)]
    plt.plot(wochen, fitness_verlauf, marker="o")
    plt.title("Fitnessentwicklung (simuliert)")
    plt.xlabel("Woche")
    plt.ylabel("Fitness Score")
    st.pyplot(plt)
