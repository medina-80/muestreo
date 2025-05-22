import streamlit as st
import pandas as pd
import numpy as np
import random
import io
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime

try:
    df = pd.read_csv("aleat.csv", header=None)
except FileNotFoundError:
    st.error("No se encontró el archivo aleat.csv. Por favor, asegúrate de que está en la misma carpeta.")
    st.stop()

st.title("Localización aleatoria para muestreo")

nombre_obra = st.text_input("Nombre de la obra", "")

st.subheader("Kilómetro inicial del tramo")
col1, col2, col3 = st.columns([2, 1, 3])
with col1:
    km_ini_cerrado = st.number_input("Km", min_value=0, value=110)
with col2:
    st.markdown("<h3 style='text-align: center;'>+</h3>", unsafe_allow_html=True)
with col3:
    metros_ini = st.number_input("m", min_value=0.0, max_value=999.999, value=850.3)

st.subheader("Kilómetro final del tramo")
col4, col5, col6 = st.columns([2, 1, 3])
with col4:
    km_fin_cerrado = st.number_input("Km ", min_value=0, value=110)
with col5:
    st.markdown("<h3 style='text-align: center;'>+</h3>", unsafe_allow_html=True)
with col6:
    metros_fin = st.number_input("m ", min_value=0.0, max_value=999.999, value=900.0)

st.subheader("Parámetros del muestreo")
num_muestras = st.number_input("Número de muestras (M)", min_value=1, max_value=30, value=5)
ancho_franja = st.number_input("Ancho de la franja (m)", min_value=1.0, value=11.0)

km_ini = km_ini_cerrado + metros_ini / 1000
km_fin = km_fin_cerrado + metros_fin / 1000
if km_fin <= km_ini:
    st.warning("El kilómetro final debe ser mayor al kilómetro inicial.")
    st.stop()

long_tramo = (km_fin - km_ini) * 1000

if st.button("Generar muestras"):
    if nombre_obra.strip() == "":
        st.warning("Por favor, ingresa el nombre de la obra antes de generar muestras.")
        st.stop()

    N = random.randint(1, 28)
    st.success(f"Número aleatorio N = {N}")

    col_inicial = (N - 1) * 3
    columnas_visitadas = [col_inicial]
    muestras = []
    col = col_inicial

    while len(muestras) < num_muestras:
        for fila in range(df.shape[0]):
            valor = int(df.iloc[fila, col])
            valores_existentes = [v[0] for v in muestras]
            if valor <= num_muestras and valor not in valores_existentes:
                muestras.append((valor, fila, col))
                if len(muestras) == num_muestras:
                    break
        if len(muestras) < num_muestras:
            col += 3
            if col >= df.shape[1]:
                col = 0
            if col in columnas_visitadas:
                break
            columnas_visitadas.append(col)

    muestras.sort(key=lambda x: x[0])
    resultados = []
    for valor, fila, col in muestras:
        a = float(df.iloc[fila, col + 1])
        b = float(df.iloc[fila, col + 2])

        d1 = round(a * long_tramo, 1)
        d4 = round(b * ancho_franja, 2)
        km_selec = km_ini + d1 / 1000
        d4_p = round(d4 - ancho_franja / 2, 2)
        lado = "Izquierdo" if d4_p > 0 else "Derecho"

        resultados.append({
            "N°": f"{valor:02d}",
            "A": round(a, 3),
            "B": round(b, 3),
            "D.Long(m)": d1,
            "D.Transv(m)": d4,
            "Cad (km)": f"{int(km_selec):.0f}+{(km_selec % 1) * 1000:.1f}",
            "Dist. al eje (m)": d4_p,
            "Lado": lado
        })

    df_resultado = pd.DataFrame(resultados)

    st.subheader("Resultados de las muestras")
    st.dataframe(df_resultado, use_container_width=True)

    st.subheader("Gráfico de ubicación de las muestras")
    fig, ax = plt.subplots(figsize=(10, 6))

    x_vals = [res["D.Long(m)"] for res in resultados]
    y_vals = [res["Dist. al eje (m)"] for res in resultados]
    etiquetas = [res["N°"] for res in resultados]
    distancias_eje = [res["Dist. al eje (m)"] for res in resultados]
    colores = ['red' if res["Lado"] == "Izquierdo" else 'blue' for res in resultados]

    ax.axhline(0, color='black', linestyle='--', linewidth=1)
    ax.scatter(x_vals, y_vals, color=colores, s=50)

    for x, y, num, dist in zip(x_vals, y_vals, etiquetas, distancias_eje):
        ax.text(x, y + 0.4, f"{num}", ha='center', fontsize=9, fontweight='bold')
        ax.text(x, y - 0.6, f"{dist:+.2f} m", ha='center', fontsize=8, color='gray')

    cad_labels = [res["Cad (km)"] for res in resultados]
    ax.set_xticks(x_vals)
    ax.set_xticklabels(cad_labels, rotation=45)

    ax.set_ylim(-ancho_franja / 2 - 1.5, ancho_franja / 2 + 1.5)
    ax.set_ylabel("Distancia transversal al eje (m)")
    ax.set_xlabel("Cadenamiento")
    ax.set_title("Ubicación de las muestras (vista esquemática)")
    ax.grid(True, linestyle='--', alpha=0.5)

    st.pyplot(fig)

    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    pdf_buffer = io.BytesIO()
    with PdfPages(pdf_buffer) as pdf:
        # Figura para tabla + título
        fig_tabla_pdf, ax_tabla_pdf = plt.subplots(figsize=(10, 0.6 + 0.4 * len(df_resultado)))
        ax_tabla_pdf.axis('off')

        # Añadir título con nombre de la obra arriba centrado, en grande
        fig_tabla_pdf.text(0.5, 0.95, nombre_obra, ha='center', fontsize=16, fontweight='bold')

        # Añadir la tabla debajo del título
        tabla = ax_tabla_pdf.table(cellText=df_resultado.values, colLabels=df_resultado.columns,
                                   loc='center', cellLoc='center')
        tabla.scale(1, 1.5)

        # Añadir texto con fecha y hora en pie de página
        fig_tabla_pdf.text(0.5, 0.02, f"App desarrollada por Martín Olvera Corona. Fecha de muestreo: {fecha_hora}",
                           ha='center', fontsize=8, style='italic', color='gray')

        pdf.savefig(fig_tabla_pdf, bbox_inches='tight')
        plt.close(fig_tabla_pdf)

        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

    st.download_button("📄 Descargar tabla + gráfica en PDF", pdf_buffer.getvalue(), "muestras_y_grafica.pdf", "application/pdf")

