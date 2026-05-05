import streamlit as st
import pandas as pd
import random
import os

# Configuración de página
st.set_page_config(page_title="Quiz Relaciones Públicas", page_icon="🎓")

# Estilos personalizados para que se vea "chulón"
st.markdown("""
    <style>
    .main { background-color: #F5F5F7; }
    .stButton>button { width: 100%; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# Inicializar variables de estado (Session State)
if 'preguntas' not in st.session_state:
    st.session_state.preguntas = []
    st.session_state.indice = 0
    st.session_state.puntuacion = 0
    st.session_state.finalizado = False
    st.session_state.mapa_relacion = {}


def cargar_datos(archivo, hoja):
    df = pd.read_excel(archivo, sheet_name=hoja)
    lista = df.to_dict('records')
    random.shuffle(lista)
    st.session_state.preguntas = lista
    st.session_state.indice = 0
    st.session_state.puntuacion = 0
    st.session_state.finalizado = False


# --- MENU PRINCIPAL ---
st.title("🎓 Quiz de Relaciones Públicas")

if not st.session_state.preguntas:
    archivos = [f for f in os.listdir('.') if f.endswith('.xlsx') and not f.startswith('~')]
    if archivos:
        archivo_sel = st.selectbox("Selecciona Asignatura", archivos)
        # Usamos pandas para leer las hojas
        xls = pd.ExcelFile(archivo_sel)
        hoja_sel = st.selectbox("Selecciona Tema", xls.sheet_names)

        if st.button("Comenzar Examen"):
            cargar_datos(archivo_sel, hoja_sel)
            st.rerun()
    else:
        st.error("No se encontró el archivo 'RELACIONES PUBLICAS.xlsx'.")

# --- PANTALLA DE RESULTADOS ---
elif st.session_state.finalizado:
    total = len(st.session_state.preguntas)
    nota = (st.session_state.puntuacion / total) * 100

    st.header("¡Examen Finalizado!")
    st.subheader(f"Nota: {nota:.1f}% ({st.session_state.puntuacion}/{total})")

    # Lógica de imagen 70%
    img_path = "1.png" if nota >= 70 else "2.png"
    if os.path.exists(img_path):
        st.image(img_path, use_container_width=True)

    if st.button("Volver al Inicio"):
        st.session_state.preguntas = []
        st.rerun()

# --- PANTALLA DE PREGUNTA ---
else:
    p = st.session_state.preguntas[st.session_state.indice]
    tipo = str(p.get('TIPO', 'individual')).lower()

    st.write(f"**Pregunta {st.session_state.indice + 1} de {len(st.session_state.preguntas)}**")
    st.subheader(p['PREGUNTA'])

    # Opciones de respuesta
    correcta_raw = str(p['CORRECTA'])

    if tipo == 'relacionar':
        st.info("Escribe o selecciona el emparejamiento correcto")
        pares_correctos = [par.strip() for par in correcta_raw.split(';')]
        izq_items = [par.split(' - ')[0] for par in pares_correctos]
        der_items = sorted(list(set(par.split(' - ')[1] for par in pares_correctos)))

        respuestas_usuario = []
        for item in izq_items:
            sel = st.selectbox(f"Relaciona: **{item}**", ["---"] + der_items, key=f"{item}_{st.session_state.indice}")
            if sel != "---":
                respuestas_usuario.append(f"{item} - {sel}")

        if st.button("Validar Parejas"):
            if set(respuestas_usuario) == set(pares_correctos):
                st.success("✓ ¡Correcto!")
                st.session_state.puntuacion += 1
            else:
                st.error(f"✗ Incorrecto. Era: {correcta_raw}")

            if p.get('JUSTIFICACION'): st.write(f"*Justificación:* {p['JUSTIFICACION']}")
            if st.button("Siguiente"):
                st.session_state.indice += 1
                if st.session_state.indice >= len(st.session_state.preguntas):
                    st.session_state.finalizado = True
                st.rerun()

    elif tipo == 'multiple':
        opciones = [p[f'OPCION {l}'] for l in ['A', 'B', 'C', 'D', 'E', 'F', 'G'] if pd.notna(p.get(f'OPCION {l}'))]
        seleccion = []
        for opt in opciones:
            if st.checkbox(opt, key=f"{opt}_{st.session_state.indice}"):
                seleccion.append(opt)

        if st.button("Validar Múltiple"):
            correctas = [c.strip() for c in correcta_raw.split(';')]
            if set(seleccion) == set(correctas):
                st.success("✓ ¡Correcto!")
                st.session_state.puntuacion += 1
            else:
                st.error(f"✗ Incorrecto. Era: {correcta_raw}")

            if p.get('JUSTIFICACION'): st.write(f"*Justificación:* {p['JUSTIFICACION']}")
            if st.button("Siguiente"):
                st.session_state.indice += 1
                if st.session_state.indice >= len(st.session_state.preguntas):
                    st.session_state.finalizado = True
                st.rerun()

    else:  # Individual
        opciones = [p[f'OPCION {l}'] for l in ['A', 'B', 'C', 'D', 'E', 'F', 'G'] if pd.notna(p.get(f'OPCION {l}'))]
        seleccion = st.radio("Elige una opción:", opciones, index=None)

        if st.button("Validar"):
            if seleccion == correcta_raw:
                st.success("✓ ¡Correcto!")
                st.session_state.puntuacion += 1
            else:
                st.error(f"✗ Incorrecto. Era: {correcta_raw}")

            if p.get('JUSTIFICACION'): st.write(f"*Justificación:* {p['JUSTIFICACION']}")
            if st.button("Siguiente Pregunta"):
                st.session_state.indice += 1
                if st.session_state.indice >= len(st.session_state.preguntas):
                    st.session_state.finalizado = True
                st.rerun()