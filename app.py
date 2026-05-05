import streamlit as st
import pandas as pd
import random
import os

# Configuración de la página
st.set_page_config(page_title="Quiz Relaciones Públicas", layout="centered")

# --- ESTILOS CSS PARA MEJORAR LA INTERFAZ ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    .justificacion { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #6c757d; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZACIÓN DEL ESTADO (MEMORIA) ---
if 'step' not in st.session_state:
    st.session_state.step = 'MENU_ASIGNATURAS'
    st.session_state.preguntas = []
    st.session_state.indice_actual = 0
    st.session_state.puntuacion = 0
    st.session_state.archivo_sel = None
    st.session_state.validado = False
    st.session_state.feedback = ""
    st.session_state.es_correcta = False
    st.session_state.mapa_relacion = {}

# --- FUNCIONES DE LÓGICA ---
def iniciar_examen(archivo, hoja):
    try:
        df = pd.read_excel(archivo, sheet_name=hoja)
        # Convertimos a lista de diccionarios para mantener la lógica original
        preguntas = df.to_dict('records')
        # Limpieza de datos (quitar NaNs)
        for p in preguntas:
            for k, v in p.items():
                if pd.isna(v): p[k] = ""
        
        random.shuffle(preguntas)
        st.session_state.preguntas = preguntas
        st.session_state.indice_actual = 0
        st.session_state.puntuacion = 0
        st.session_state.step = 'QUIZ'
        st.session_state.validado = False
    except Exception as e:
        st.error(f"Error al cargar: {e}")

def siguiente_pregunta():
    st.session_state.indice_actual += 1
    st.session_state.validado = False
    st.session_state.mapa_relacion = {}
    if st.session_state.indice_actual >= len(st.session_state.preguntas):
        st.session_state.step = 'RESULTADOS'

# --- INTERFAZ: MENÚ DE ASIGNATURAS ---
if st.session_state.step == 'MENU_ASIGNATURAS':
    st.title("📚 Elige una Asignatura")
    archivos = [f for f in os.listdir('.') if f.endswith('.xlsx') and not f.startswith('~')]
    
    if not archivos:
        st.error("No se encontraron archivos .xlsx")
    else:
        for arc in archivos:
            if st.button(os.path.splitext(arc)[0]):
                st.session_state.archivo_sel = arc
                st.session_state.step = 'MENU_TEMAS'
                st.rerun()

# --- INTERFAZ: MENÚ DE TEMAS ---
elif st.session_state.step == 'MENU_TEMAS':
    st.title(f"📂 Temas: {os.path.splitext(st.session_state.archivo_sel)[0]}")
    try:
        xls = pd.ExcelFile(st.session_state.archivo_sel)
        for hoja in xls.sheet_names:
            if st.button(hoja):
                iniciar_examen(st.session_state.archivo_sel, hoja)
                st.rerun()
    except:
        st.session_state.step = 'MENU_ASIGNATURAS'
        st.rerun()
    
    if st.button("← Volver"):
        st.session_state.step = 'MENU_ASIGNATURAS'
        st.rerun()

# --- INTERFAZ: EXAMEN (QUIZ) ---
elif st.session_state.step == 'QUIZ':
    p = st.session_state.preguntas[st.session_state.indice_actual]
    tipo = str(p.get('TIPO', 'individual')).lower()
    total = len(st.session_state.preguntas)

    st.caption(f"Pregunta {st.session_state.indice_actual + 1} de {total}")
    st.subheader(p['PREGUNTA'])

    # --- LÓGICA DE OPCIONES ---
    correcta_raw = str(p['CORRECTA']).strip()
    opciones = [p[f'OPCION {l}'] for l in ['A','B','C','D','E','F','G'] if p.get(f'OPCION {l}')]
    
    if not st.session_state.validado:
        # MODO SELECCIÓN
        if tipo == 'relacionar':
            st.info("Asocia los elementos de la izquierda con su pareja:")
            pares_obj = [par.split(' - ') for par in correcta_raw.split(';') if ' - ' in par]
            izq_items = [par[0].strip() for par in pares_obj]
            der_items = sorted(list(set(par[1].strip() for par in pares_obj)))
            
            for item in izq_items:
                st.session_state.mapa_relacion[item] = st.selectbox(
                    f"Pareja de: {item}", 
                    ["Selecciona..."] + der_items, 
                    key=f"rel_{item}_{st.session_state.indice_actual}"
                )
        
        elif tipo == 'multiple':
            st.session_state.seleccion = []
            for opt in opciones:
                if st.checkbox(opt, key=f"check_{opt}"):
                    st.session_state.seleccion.append(opt)
        
        else: # individual
            st.session_state.seleccion = st.radio("Selecciona una respuesta:", opciones, index=None)

        if st.button("Validar Respuesta"):
            # Lógica de validación
            if tipo == 'relacionar':
                resp_usuario = set(f"{k} - {v}" for k,v in st.session_state.mapa_relacion.items() if v != "Selecciona...")
                resp_correcta = set(par.strip() for par in correcta_raw.split(';'))
                st.session_state.es_correcta = (resp_usuario == resp_correcta)
            elif tipo == 'multiple':
                st.session_state.es_correcta = (set(st.session_state.seleccion) == set(par.strip() for par in correcta_raw.split(';')))
            else:
                st.session_state.es_correcta = (st.session_state.seleccion == correcta_raw)
            
            if st.session_state.es_correcta:
                st.session_state.puntuacion += 1
            st.session_state.validado = True
            st.rerun()

    else:
        # MODO FEEDBACK
        if st.session_state.es_correcta:
            st.success("✓ ¡CORRECTO!")
        else:
            st.error(f"✗ INCORRECTO\n\nLa respuesta correcta era:\n{correcta_raw}")
        
        if p.get('JUSTIFICACION'):
            st.markdown(f'<div class="justificacion"><b>💡 Justificación:</b><br>{p["JUSTIFICACION"]}</div>', unsafe_allow_html=True)
        
        if st.button("Siguiente Pregunta →"):
            siguiente_pregunta()
            st.rerun()

# --- INTERFAZ: RESULTADOS ---
elif st.session_state.step == 'RESULTADOS':
    st.title("Examen Finalizado")
    total = len(st.session_state.preguntas)
    nota = (st.session_state.puntuacion / total) * 100 if total > 0 else 0
    
    # Imagen según nota
    img_final = "1.png" if nota >= 70 else "2.png"
    if os.path.exists(img_final):
        st.image(img_final, use_container_width=True)
    
    st.metric("Puntuación Final", f"{nota:.1f}%", f"{st.session_state.puntuacion} de {total} aciertos")
    
    if st.button("Volver al Inicio"):
        st.session_state.step = 'MENU_ASIGNATURAS'
        st.session_state.preguntas = []
        st.rerun()
