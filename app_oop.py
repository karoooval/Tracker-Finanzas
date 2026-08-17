import streamlit as st #como un sobrenombre
import pandas as pd
import datetime

ARCHIVO_DATOS = "transacciones.csv"

categorias = ["Comida", "Transporte", "Entretenimiento", "Salud", "Educación", "Otros"]


class Transaccion:
    def __init__(self, descripcion, monto, fecha, categoria, tipo):
        self.descripcion = descripcion
        self.monto = monto
        self.fecha = fecha
        self.categoria = categoria
        self.tipo = tipo

    def es_gasto(self):
        return self.tipo == "Gasto"

    def es_ingreso(self):
        return self.tipo == "Ingreso"

    def to_dict(self):
        return {
            "descripcion": self.descripcion,
            "monto": self.monto,
            "fecha": self.fecha,
            "categoria": self.categoria,
            "tipo": self.tipo
        }


class Cartera:
    def __init__(self, transacciones=None):
        self.transacciones = transacciones if transacciones is not None else []

    def agregar_transaccion(self, transaccion):
        self.transacciones.append(transaccion)

    def filtrar(self, categorias_seleccionadas, fecha_desde, fecha_hasta):
        transacciones_filtradas = [
            t for t in self.transacciones
            if t.categoria in categorias_seleccionadas and fecha_desde <= t.fecha <= fecha_hasta
        ]
        return Cartera(transacciones_filtradas)

    def calcular_resumen(self):
        montos_gastos = [t.monto for t in self.transacciones if t.es_gasto()]
        montos_ingresos = [t.monto for t in self.transacciones if t.es_ingreso()]

        ingresos = sum(montos_ingresos)
        gastos = sum(montos_gastos)
        balance = ingresos - gastos
        gasto_promedio = sum(montos_gastos) / len(montos_gastos) if montos_gastos else 0

        return {
            "ingresos": ingresos,
            "gastos": gastos,
            "balance": balance,
            "gasto_promedio": gasto_promedio
        }

    def gastos_por_categoria(self):
        resultado = {}
        for t in self.transacciones:
            if t.es_gasto():
                resultado[t.categoria] = resultado.get(t.categoria, 0) + t.monto
        return resultado

    def gastos_por_fecha(self):
        resultado = {}
        for t in self.transacciones:
            if t.es_gasto():
                resultado[t.fecha] = resultado.get(t.fecha, 0) + t.monto
        return dict(sorted(resultado.items()))

    def to_dataframe(self):
        return pd.DataFrame([t.to_dict() for t in self.transacciones])

    def guardar(self, archivo=ARCHIVO_DATOS):
        df = self.to_dataframe()
        df.to_csv(archivo, index=False)

    @classmethod
    def cargar(cls, archivo=ARCHIVO_DATOS):
        try:
            df = pd.read_csv(archivo)
        except Exception:
            return cls()

        transacciones = []
        for _, fila in df.iterrows():
            transacciones.append(Transaccion(
                descripcion=fila["descripcion"],
                monto=float(fila["monto"]),
                fecha=datetime.date.fromisoformat(str(fila["fecha"])),
                categoria=fila["categoria"],
                tipo=fila["tipo"]
            ))
        return cls(transacciones)


def mostrar_titulos():
    st.title("Tracker de Finanzas Personales")
    st.write("Lleva el control de tus gastos e ingresos de manera sencilla y efectiva ;D.")
    st.caption("Desarrollado por Carolina - 2026 *Versión 1.0*")

def inicializar_estado():
    if "cartera" not in st.session_state:
        st.session_state.cartera = Cartera.cargar(ARCHIVO_DATOS)

def mostrar_formulario():
    with st.form("nueva_transaccion"):
        descripcion = st.text_input("Descripción del gasto o ingreso: ", placeholder="Escribe la descripción de la operación")
        monto = st.number_input("Monto: ", step=100.00, min_value=100.00, format="%0.2f")
        fecha = st.date_input("Fecha: ")
        categoria = st.selectbox("Categoría: ", categorias)
        tipo = st.radio("Tipo de operación: ", ("Gasto", "Ingreso"), horizontal=True)
        enviar = st.form_submit_button("Confirmar")

    if enviar:
        transaccion = Transaccion(
            descripcion=descripcion,
            monto=monto,
            fecha=fecha,
            categoria=categoria,
            tipo=tipo
        )
        st.session_state.cartera.agregar_transaccion(transaccion)
        st.success("¡Transacción registrada con éxito!")

def importar_csv():
    with st.expander("Importar desde csv"):
        archivo = st.file_uploader("Selecciona un archivo CSV", type="csv")
        importar = st.button("importar transacciones")

        if importar:
            if archivo is None:
                st.warning("Primero debes subir un archivo CSV.")
                return

            try:
                df_csv = pd.read_csv(archivo)
            except Exception:
                st.error("El archivo no es un CSV válido.")
                return

            columnas_esperadas = ["descripción", "monto", "fecha", "categoría", "tipo"]
            if not all(columna in df_csv.columns for columna in columnas_esperadas):
                st.error(
                    "El CSV no tiene las columnas esperadas. Columnas requeridas: "
                    + ", ".join(columnas_esperadas)
                )
                return

            nuevas_transacciones = []
            for _, fila in df_csv.iterrows():
                transaccion = Transaccion(
                    descripcion=fila["descripción"],
                    monto=float(fila["monto"]),
                    fecha=datetime.date.fromisoformat(str(fila["fecha"])),
                    categoria=fila["categoría"],
                    tipo=fila["tipo"]
                )
                nuevas_transacciones.append(transaccion)

            for transaccion in nuevas_transacciones:
                st.session_state.cartera.agregar_transaccion(transaccion)
            st.success(f"Se importaron {len(nuevas_transacciones)} transacciones.")

def mostrar_filtros():
    categorias_seleccionadas = st.multiselect("Categorías: ", categorias, default=categorias)

    if st.session_state.cartera.transacciones:
        fechas = [t.fecha for t in st.session_state.cartera.transacciones]
        fecha_min = min(fechas)
        fecha_max = max(fechas)
    else:
        fecha_min = datetime.date.today()
        fecha_max = datetime.date.today()

    fecha_desde = st.date_input("Desde: ", value=fecha_min)
    fecha_hasta = st.date_input("Hasta: ", value=fecha_max)

    return categorias_seleccionadas, fecha_desde, fecha_hasta

def mostrar_transacciones(cartera):
    st.subheader("Transacciones registradas:")
    if cartera.transacciones:
        df = cartera.to_dataframe()
        st.dataframe(df)
        csv_datos = df.to_csv(index=False)
        st.download_button(
            "descargar transacciones",
            data=csv_datos,
            file_name="mis_transacciones.csv",
            mime="text/csv"
        )
    else:
        st.info("No hay transacciones registradas aún. ¡Agrega una nueva transacción para comenzar! :D")

def mostrar_resumen(cartera):
    if not cartera.transacciones:
        st.info("Todavía no hay transacciones para calcular el resumen.")
        return

    resumen = cartera.calcular_resumen()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ingresos", f"${resumen['ingresos']:.2f}")
    col2.metric("Gastos", f"${resumen['gastos']:.2f}")
    col3.metric("Balance", f"${resumen['balance']:.2f}")
    col4.metric("Gasto promedio", f"${resumen['gasto_promedio']:.2f}")

def mostrar_analisis(cartera):
    gastos_por_categoria = cartera.gastos_por_categoria()

    if not gastos_por_categoria:
        st.info("No hay gastos registrados para analizar.")
        return

    gastos_por_fecha = cartera.gastos_por_fecha()

    st.subheader("Gastos por categoría")
    st.bar_chart(gastos_por_categoria)

    st.subheader("Gastos por fecha")
    st.line_chart(gastos_por_fecha)

mostrar_titulos()
inicializar_estado()

with st.sidebar:
    mostrar_formulario()
    importar_csv()
    categorias_seleccionadas, fecha_desde, fecha_hasta = mostrar_filtros()

cartera_filtrada = st.session_state.cartera.filtrar(categorias_seleccionadas, fecha_desde, fecha_hasta)

tab_resumen, tab_movimientos, tab_analisis = st.tabs(["resumen", "movimientos", "análisis"])

with tab_resumen:
    mostrar_resumen(cartera_filtrada)

with tab_movimientos:
    mostrar_transacciones(cartera_filtrada)

with tab_analisis:
    mostrar_analisis(cartera_filtrada)

st.session_state.cartera.guardar()

# st.table es una tabla estática, mientras que st.dataframe es una tabla interactiva. 
# st.data_editor permite al usuario editar la tabla en la aplicación.