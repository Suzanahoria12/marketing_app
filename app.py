import streamlit as st
import pandas as pd
import random
import os

# --- CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="Quiz Master RRPP", layout="centered")

# CSS Avanzado para corregir la visibilidad y mejorar la fuente
st.markdown("""
    <style>
    /* Estilo de la fuente general */
    html, body, [class*="st-"] {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: bold; }
    
    /* Cuadro de Justificación */
    .justificacion { 
        background-color: #f0f2f6; 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 5px solid #6c757d; 
        margin-top: 15px;
        color: #1c1c1e !important; 
        line-height: 1.6;
    }
    
    /* Cuadros de Feedback (Respuesta correcta/incorrecta) */
    .res-correcta {
        background-color: #d4edda;
        color: #155724 !important;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #c3e6cb;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .res-incorrecta {
        background-color: #f8d7da;
        color: #721c24 !important;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #f5c6cb;
        font-weight: bold;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- GESTIÓN DE ESTADO ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'SELECCION_ARCHIVO'
    st.session_state.preguntas = []
    st.session_state.indice = 0
    st.session_state.puntuacion = 0
    st.session_state.respondido = False
    st.session_state.es_correcta = False
    st.session_state.archivo_actual = None
    st.session_state.mapa_relacion = {}

def reiniciar_quiz():
    st.session_state.pagina = 'SELECCION_ARCHIVO'
    st.session_state.preguntas = []
    st.session_state.indice = 0
    st.session_state.puntuacion = 0
    st.session_state.respondido = False

# --- PANTALLA 1: SELECCIÓN DE ASIGNATURA ---
if st.session_state.pagina == 'SELECCION_ARCHIVO':
    st.title("📚 Asignaturas disponibles")
    archivos = [f for f in os.listdir('.') if f.endswith('.xlsx') and not f.startswith('~')]
    
    if not archivos:
        st.error("No se han encontrado archivos .xlsx en la carpeta.")
    else:
        for arc in archivos:
            if st.button(os.path.splitext(arc)[0]):
                st.session_state.archivo_actual = arc
                st.session_state.pagina = 'SELECCION_TEMA'
                st.rerun()

# --- PANTALLA 2: SELECCIÓN DE TEMA ---
elif st.session_state.pagina == 'SELECCION_TEMA':
    st.title(f"📂 Temas: {os.path.splitext(st.session_state.archivo_actual)[0]}")
    try:
        xls = pd.ExcelFile(st.session_state.archivo_actual)
        for hoja in xls.sheet_names:
            if st.button(hoja):
                df = pd.read_excel(st.session_state.archivo_actual, sheet_name=hoja)
                preguntas = df.to_dict('records')
                for p in preguntas:
                    for k, v in p.items():
                        if pd.isna(v): p[k] = ""
                random.shuffle(preguntas)
                st.session_state.preguntas = preguntas
                st.session_state.pagina = 'QUIZ'
                st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")
        if st.button("Volver"): reiniciar_quiz(); st.rerun()
    
    if st.button("← Volver a Asignaturas"):
        reiniciar_quiz()
        st.rerun()

# --- PANTALLA 3: EL EXAMEN ---
elif st.session_state.pagina == 'QUIZ':
    p = st.session_state.preguntas[st.session_state.indice]
    tipo = str(p.get('TIPO', 'individual')).lower()
    
    st.caption(f"Pregunta {st.session_state.indice + 1} de {len(st.session_state.preguntas)}")
    st.subheader(p['PREGUNTA'])

    correcta_raw = str(p['CORRECTA']).strip()
    opciones = [p[f'OPCION {l}'] for l in ['A','B','C','D','E','F','G'] if p.get(f'OPCION {l}')]

    if not st.session_state.respondido:
        if tipo == 'relacionar':
            st.info("Empareja los elementos:")
            pares = [par.split(' - ') for par in correcta_raw.split(';') if ' - ' in par]
            izq_items = [par[0].strip() for par in pares]
            der_items = sorted(list(set(par[1].strip() for par in pares)))
            for izq in izq_items:
                st.session_state.mapa_relacion[izq] = st.selectbox(
                    f"¿Con qué va: {izq}?", ["Selecciona..."] + der_items, key=f"r_{izq}_{st.session_state.indice}"
                )
        elif tipo == 'multiple':
            st.session_state.sel_mul = []
            for opt in opciones:
                if st.checkbox(opt, key=f"c_{opt}_{st.session_state.indice}"):
                    st.session_state.sel_mul.append(opt)
        else:
            st.session_state.sel_uni = st.radio("Elige una opción:", opciones, index=None, key=f"u_{st.session_state.indice}")

        if st.button("Validar Respuesta"):
            if tipo == 'relacionar':
                res_u = set(f"{k} - {v}" for k,v in st.session_state.mapa_relacion.items() if v != "Selecciona...")
                res_c = set(par.strip() for par in correcta_raw.split(';'))
                st.session_state.es_correcta = (res_u == res_c)
            elif tipo == 'multiple':
                res_c = set(par.strip() for par in correcta_raw.split(';'))
                st.session_state.es_correcta = (set(st.session_state.sel_mul) == res_c)
            else:
                st.session_state.es_correcta = (st.session_state.sel_uni == correcta_raw)
            
            if st.session_state.es_correcta:
                st.session_state.puntuacion += 1
            st.session_state.respondido = True
            st.rerun()

    else:
        # FEEDBACK CON COLORES FIJOS (TEXTO NEGRO)
        if st.session_state.es_correcta:
            st.markdown('<div class="res-correcta">✅ ¡CORRECTO!</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="res-incorrecta">❌ INCORRECTO<br>La respuesta era: {correcta_raw}</div>', unsafe_allow_html=True)
        
        if p.get('JUSTIFICACION'):
            st.markdown(f'<div class="justificacion"><b>📖 Justificación:</b><br>{p["JUSTIFICACION"]}</div>', unsafe_allow_html=True)
        
        if st.button("Siguiente Pregunta →"):
            st.session_state.indice += 1
            st.session_state.respondido = False
            st.session_state.mapa_relacion = {}
            if st.session_state.indice >= len(st.session_state.preguntas):
                st.session_state.pagina = 'RESULTADOS'
            st.rerun()

# --- PANTALLA 4: RESULTADOS ---
elif st.session_state.pagina == 'RESULTADOS':
    st.title("🏁 Resultados Finales")
    total = len(st.session_state.preguntas)
    nota = (st.session_state.puntuacion / total) * 100 if total > 0 else 0
    
    # MUSICA AUTOMÁTICA
    archivo_musica = "aprobado.mp3" if nota >= 70 else "suspendido.mp3"
    if os.path.exists(archivo_musica):
        st.audio(archivo_musica, format="audio/mp3", autoplay=True)
    
    img = "1.png" if nota >= 70 else "2.png"
    if os.path.exists(img):
        st.image(img, use_container_width=True)
    
    st.write(f"### Tu nota: {nota:.1f}%")
    st.write(f"Aciertos: {st.session_state.puntuacion} de {total}")
    
    if st.button("Volver al Inicio"):
        reiniciar_quiz()
        st.rerun()
