import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Digitaler Zwilling – Gesundheit & Fitness")

gewicht = st.number_input("Gewicht (kg)", 50, 120, 88)
blutdruck = st.slider("Blutdruck (mmHg)", 90, 180, 130)
puls = st.slider("Ruhepuls", 50, 100, 70)

# KI-Modell (vereinfacht)
fitness_index = 100 - (gewicht/2 + (blutdruck-120)/2 + (puls-60)/2)
st.metric("Fitness Score", round(fitness_index, 1))

st.write("Prognose: ", "Gut in Form!" if fitness_index > 60 else "Mehr Bewegung empfohlen.")
