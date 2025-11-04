import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


# Cargar el archivo Excel
file_path = "Norma_ISO_42001.xlsx"  # Ajustar según la ruta real del archivo
df_activos = pd.read_excel(file_path, sheet_name="2. Identificación de Activos")

# Título general
st.title("Dashboard ISO 42001")

# Crear pestañas
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Anexo A", 
    "Identificación de Activos", 
    "Identificación de riesgos", 
    "Matriz de evaluación de riesgos", 
    "Plan de tratamiento del riesgo",
    "Informe ISO 42001"
])

# Cargar hoja para la cuarta pestaña
df_tratamiento = pd.read_excel(file_path, sheet_name="Anexo A")

with tab1:
    st.title("Plan de Tratamiento del Riesgo")

    df_tratamiento.columns = df_tratamiento.columns.str.strip()

    st.dataframe(df_tratamiento, use_container_width=True)

with tab2:
    st.header("Identificación de Activos")

    # Selector de categoría
    categorias = df_activos["Categoría del Activo"].unique()
    categoria_seleccionada = st.selectbox("Seleccione la categoría del activo", categorias)

    # Filtrar según la categoría elegida
    filtro = df_activos[df_activos["Categoría del Activo"] == categoria_seleccionada]

    # Eliminar la columna "Categoría del Activo"
    filtro = filtro.drop(columns=["Categoría del Activo"])

    # Mostrar tabla sin la columna de índices
    st.dataframe(filtro.reset_index(drop=True), width='stretch')

# Cargar hoja de identificación de riesgos
df_riesgos = pd.read_excel(file_path, sheet_name="3. Identificación de Riesgos")

with tab3:
    st.header("Identificación de Riesgos")

    # Selector del activo relacionado
    activos_relacionados = df_riesgos["Activo relacionado"].unique()
    activo_seleccionado = st.selectbox("Seleccione el activo relacionado", activos_relacionados)

    # Filtrado por activo
    filtro_riesgos = df_riesgos[df_riesgos["Activo relacionado"] == activo_seleccionado]

    # Eliminar columna luego de filtrar para evitar repetición
    filtro_riesgos = filtro_riesgos.drop(columns=["Activo relacionado"])

    # Mostrar tabla sin índice
    st.dataframe(filtro_riesgos.reset_index(drop=True), width="stretch")

# Cargar hoja para la tercera pestaña
df_matriz = pd.read_excel(file_path, sheet_name="4 MATRIZ DE EVALUACIÓN RIESGOS")

with tab4:
    st.title("Matriz de Evaluación de Riesgos")

    df_matriz.columns = (
        df_matriz.columns
        .str.strip()
        .str.replace("–", "-", regex=False)
        .str.replace("—", "-", regex=False)
    )

    columnas_requeridas = [
        "Impacto (1-5)", "Probabilidad (1-5)", "Activo relacionado",
        "Control ISO 42001", "Descripción del riesgo",
        "Medida de mitigación", "Responsable"
    ]

    faltantes = [c for c in columnas_requeridas if c not in df_matriz.columns]
    if faltantes:
        st.error(f"Faltan columnas en el archivo: {', '.join(faltantes)}")
        st.stop()

    df_matriz["Impacto (1-5)"] = pd.to_numeric(df_matriz["Impacto (1-5)"], errors="coerce").clip(1, 5)
    df_matriz["Probabilidad (1-5)"] = pd.to_numeric(df_matriz["Probabilidad (1-5)"], errors="coerce").clip(1, 5)
    df_matriz["Nivel de riesgo (I×P)"] = df_matriz["Impacto (1-5)"] * df_matriz["Probabilidad (1-5)"]
    df_matriz.dropna(subset=["Impacto (1-5)", "Probabilidad (1-5)", "Activo relacionado"], inplace=True)

    def clasificar_riesgo(valor):
        if valor <= 5:
            return "Bajo"
        elif valor <= 10:
            return "Medio"
        elif valor <= 15:
            return "Alto"
        return "Crítico"

    activos = df_matriz["Activo relacionado"].dropna().unique()
    activo_seleccionado = st.selectbox("Seleccionar Activo relacionado", activos)

    # Inicializar df_filtrado base
    df_base = df_matriz[df_matriz["Activo relacionado"] == activo_seleccionado].copy()
    df_base["Clasificación"] = df_base["Nivel de riesgo (I×P)"].apply(clasificar_riesgo)

    # Persistencia en session_state por activo
    key_estado = f"df_editado_{activo_seleccionado}"
    if key_estado not in st.session_state:
        st.session_state[key_estado] = df_base.copy()

    # Usar el estado persistido como base
    df_editado = st.session_state[key_estado].copy()

    # Orden y numeración inicial (o re-aplicar si cambió)
    if "Riesgo" in df_editado.columns:
        df_editado.drop(columns=["Riesgo"], inplace=True)
    df_editado = df_editado.sort_values(by="Nivel de riesgo (I×P)", ascending=False).reset_index(drop=True)
    df_editado.insert(0, "Riesgo", range(1, len(df_editado) + 1))

    columnas_visibles = [
        "Riesgo",
        "Control ISO 42001",
        "Descripción del riesgo",
        "Impacto (1-5)",
        "Probabilidad (1-5)",
        "Medida de mitigación",
        "Responsable"
    ]

    st.subheader(f"Riesgos asociados a: {activo_seleccionado}")

    # Configuración de columnas: deshabilitar ID
    column_config = {
        "Riesgo": st.column_config.NumberColumn("Riesgo", disabled=True),
    }

    # Mostrar editor con datos persistidos
    df_para_editor = df_editado[columnas_visibles].copy()
    df_editado_editor = st.data_editor(df_para_editor, num_rows="dynamic", column_config=column_config)

    # Detectar cambios y actualizar estado
    if not df_editado_editor.equals(df_para_editor):
        # Agregar columnas derivadas ausentes al editor para consistencia
        df_editado_editor = df_editado_editor.join(df_editado.drop(columns=columnas_visibles))
        st.session_state[key_estado] = df_editado_editor

    # Recalcular dinámicamente (siempre, para reflejar ediciones)
    df_editado = st.session_state[key_estado].copy()
    df_editado["Impacto (1-5)"] = pd.to_numeric(df_editado["Impacto (1-5)"], errors="coerce").clip(1, 5)
    df_editado["Probabilidad (1-5)"] = pd.to_numeric(df_editado["Probabilidad (1-5)"], errors="coerce").clip(1, 5)
    df_editado["Nivel de riesgo (I×P)"] = df_editado["Impacto (1-5)"] * df_editado["Probabilidad (1-5)"]
    df_editado["Clasificación"] = df_editado["Nivel de riesgo (I×P)"].apply(clasificar_riesgo)

    # Re-ordenar y re-numerar después de cambios
    if "Riesgo" in df_editado.columns:
        df_editado.drop(columns=["Riesgo"], inplace=True)
    df_editado = df_editado.sort_values(by="Nivel de riesgo (I×P)", ascending=False).reset_index(drop=True)
    df_editado.insert(0, "Riesgo", range(1, len(df_editado) + 1))

    # Guardar el df actualizado en session_state
    st.session_state[key_estado] = df_editado

    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.patches import Patch

    st.subheader("Nivel de Riesgo por Riesgo")
    colores_map = {
        "Bajo": "green",
        "Medio": "yellow",
        "Alto": "orange",
        "Crítico": "red"
    }
    colores = df_editado["Clasificación"].map(colores_map)

    fig_bar, ax_bar = plt.subplots()
    bars = ax_bar.bar(df_editado["Riesgo"], df_editado["Nivel de riesgo (I×P)"], color=colores)
    ax_bar.set_xlabel("ID Riesgo")
    ax_bar.set_ylabel("Nivel de riesgo (I×P)")
    ax_bar.set_title("Nivel de Riesgo por Riesgo")

    # Añadir leyenda de colores
    legend_elements = [Patch(facecolor=color, label=label) for label, color in colores_map.items()]
    ax_bar.legend(handles=legend_elements, loc="upper right")

    st.pyplot(fig_bar)

    st.subheader("Resumen de Riesgo Promedio por Activo")
    labels = ["Impacto (1-5)", "Probabilidad (1-5)", "Nivel de riesgo (I×P)"]
    valores = df_editado[labels].mean().values.tolist()
    valores += valores[:1]

    num_vars = len(labels)
    angulos = [n / float(num_vars) * 2 * np.pi for n in range(num_vars)]
    angulos += angulos[:1]

    fig2 = plt.figure()
    ax = fig2.add_subplot(111, polar=True)
    ax.plot(angulos, valores, marker="o")
    ax.fill(angulos, valores, alpha=0.25)
    ax.set_thetagrids([a * 180 / np.pi for a in angulos[:-1]], labels)
    plt.title(f"Resumen de Riesgo Promedio para {activo_seleccionado}")
    st.pyplot(fig2)

# Cargar hoja para la cuarta pestaña
df_tratamiento = pd.read_excel(file_path, sheet_name="5.Plan de Tratamiento del Riesg")

with tab5:
    st.title("Plan de Tratamiento del Riesgo")

    df_tratamiento.columns = df_tratamiento.columns.str.strip()

    st.dataframe(df_tratamiento, use_container_width=True)

# Sexta pestaña: visor del informe PDF
with tab6:
    st.title("Informe ISO/IEC 42001:2023")

    pdf_path = "Informe ISO 42001.pdf"  # Ruta del informe PDF

    try:
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        # Mostrar visor PDF incrustado
        import base64
        base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

        # Botón para descargar
        st.download_button(
            label="📄 Descargar Informe ISO 42001",
            data=pdf_bytes,
            file_name="Informe_ISO_42001.pdf",
            mime="application/pdf"
        )

    except FileNotFoundError:
        st.error("No se encontró el archivo PDF del informe. Verifica la ruta o nombre del archivo.")
