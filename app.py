import streamlit as st
import pandas as pd
import random
import os

# --- CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="Quiz Master RRPP", layout="centered")

# CSS Modificado para asegurar que el texto sea visible (Negro sobre Gris claro)
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: bold; }
    .justificacion { 
        background-color: #f8f9fa; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid #007bff; 
        margin-top: 10px;
        color: #1c1c1e !important; /* Fuerza el color de texto a negro/oscuro */
    }
    /* Asegurar visibilidad en mensajes de éxito/error si el tema falla */
    .stAlert p { color: #1c1c1e !important; } 
    </style>
    """, unsafe_allow_html=True)

# --- GESTIÓN DE ESTADO (MEMORIA DE LA APP) ---
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

# --- PANTALLA 2: SELECCIÓN DE TEMA (HOJA) ---
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
        st.error(f"Error al leer temas: {e}")
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
            st.info("Empareja los elementos correctamente:")
            pares = [par.split(' - ') for par in correcta_raw.split(';') if ' - ' in par]
            izq_items = [par[0].strip() for par in pares]
            der_items = sorted(list(set(par[1].strip() for par in pares)))
            
            for izq in izq_items:
                st.session_state.mapa_relacion[izq] = st.selectbox(
                    f"¿Con qué va: {izq}?", ["Selecciona..."] + der_items, key=f"r_{izq}"
                )
        
        elif tipo == 'multiple':
            st.session_state.seleccion_multiple = []
            for opt in opciones:
                if st.checkbox(opt, key=f"c_{opt}"):
                    st.session_state.seleccion_multiple.append(opt)
        
        else: # Individual
            st.session_state.seleccion_unica = st.radio("Elige una opción:", opciones, index=None)

        if st.button("Validar"):
            if tipo == 'relacionar':
                res_u = set(f"{k} - {v}" for k,v in st.session_state.mapa_relacion.items() if v != "Selecciona...")
                res_c = set(par.strip() for par in correcta_raw.split(';'))
                st.session_state.es_correcta = (res_u == res_c)
            elif tipo == 'multiple':
                res_c = set(par.strip() for par in correcta_raw.split(';'))
                st.session_state.es_correcta = (set(st.session_state.seleccion_multiple) == res_c)
            else:
                st.session_state.es_correcta = (st.session_state.seleccion_unica == correcta_raw)
            
            if st.session_state.es_correcta:
                st.session_state.puntuacion += 1
            
            st.session_state.respondido = True
            st.rerun()

    else:
        if st.session_state.es_correcta:
            st.success("✅ ¡CORRECTO!")
        else:
            st.error(f"❌ INCORRECTO\n\nRespuesta correcta:\n{correcta_raw}")
        
        if p.get('JUSTIFICACION'):
            # El CSS de arriba asegura que este texto sea oscuro
            st.markdown(f'<div class="justificacion"><b>📖 Justificación:</b><br>{p["JUSTIFICACION"]}</div>', unsafe_allow_html=True)
        
        if st.button("Siguiente Pregunta →"):
            st.session_state.indice += 1
            st.session_state.respondido = False
            st.session_state.mapa_relacion = {}
            if st.session_state.indice >= len(st.session_state.preguntas):
                st.session_state.pagina = 'RESULTADOS'
            st.rerun()

# --- PANTALLA 4: RESULTADOS FINALES ---
elif st.session_state.pagina == 'RESULTADOS':
    st.title("🏁 Resultados del Examen")
    total = len(st.session_state.preguntas)
    nota = (st.session_state.puntuacion / total) * 100 if total > 0 else 0
    
    # --- LÓGICA DE AUDIO Y MÚSICA SEGÚN NOTA ---
    archivo_musica = "aprobado.mp3" if nota >= 70 else "suspendido.mp3"
    
    if os.path.exists(archivo_musica):
        st.audio(archivo_musica, format="audio/mp3", autoplay=True)
    
    # Lógica de imagen (se mantiene igual)
    img = "1.png" if nota >= 70 else "2.png"
    if os.path.exists(img):
        st.image(img, use_container_width=True)
    
    st.write(f"### Nota Final: {nota:.1f}%")
    st.write(f"Has acertado **{st.session_state.puntuacion}** de **{total}** preguntas.")
    
    if st.button("Volver al Inicio"):
        reiniciar_quiz()
        st.rerun()
