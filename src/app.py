"""Dash App para Mapas: colonias de abejas afectadas en EE. UU. (versión dockerizada)."""
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

RUTA_DATOS = Path(__file__).parent / "data" / "intro_bees.csv"
PCT = "Pct of Colonies Impacted"
ETIQUETA_PCT = "% de colonias afectadas"
TEMPLATE = "plotly_dark"
ESCALA = px.colors.sequential.YlOrRd

FACTORES = {
    "Disease": "Enfermedades",
    "Other": "Otros",
    "Pesticides": "Pesticidas",
    "Pests_excl_Varroa": "Plagas (sin Varroa)",
    "Unknown": "Desconocido",
    "Varroa_mites": "Ácaros Varroa",
}

ext_style = "https://cdn.jsdelivr.net/npm/bootswatch@4.5.2/dist/darkly/bootstrap.min.css"
app = Dash(__name__, external_stylesheets=[ext_style], title="Colonias de abejas | EE. UU.")
server = app.server

# --------------------------------------------------------------------------- datos
df = pd.read_csv(RUTA_DATOS)

df = df.groupby(["State", "ANSI", "Affected by", "Year", "state_code"])[[PCT]].mean()
df.reset_index(inplace=True)
df["Factor"] = df["Affected by"].map(FACTORES)

# Agrupación por State, Affected by, Year
df_sya = df.groupby(["State", "Affected by", "Year"], as_index=False)[PCT].mean()
df_sya["Factor"] = df_sya["Affected by"].map(FACTORES)

ANIOS = sorted(int(a) for a in df["Year"].unique())
ESTADOS = sorted(df["State"].unique())


# --------------------------------------------------------------------------- figuras
def estilo(fig, alto=360):
    fig.update_layout(
        template=TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=alto,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig


def tipo_de_dato(serie):
    if pd.api.types.is_integer_dtype(serie):
        return "entero"
    if pd.api.types.is_float_dtype(serie):
        return "decimal"
    return "texto"


def descripcion(columna):
    serie = df[columna]
    texto = f"Tipo: {tipo_de_dato(serie)} · {serie.nunique()} valores distintos"
    if pd.api.types.is_numeric_dtype(serie):
        texto += f" · rango {serie.min():.1f} a {serie.max():.1f}"
    return texto


def figuras_por_columna():
    """Un diagrama descriptivo por cada columna del dataframe agrupado."""
    media_estado = df.groupby("State")[PCT].mean().nlargest(15).sort_values()
    f_state = px.bar(x=media_estado.values, y=media_estado.index, orientation="h",
                     color=media_estado.values, color_continuous_scale=ESCALA,
                     labels={"x": ETIQUETA_PCT, "y": "Estado", "color": ETIQUETA_PCT})

    por_ansi = df.groupby(["ANSI", "State"], as_index=False)[PCT].mean()
    f_ansi = px.scatter(por_ansi, x="ANSI", y=PCT, hover_name="State",
                        color=PCT, color_continuous_scale=ESCALA,
                        labels={PCT: ETIQUETA_PCT})

    f_factor = px.box(df, x="Factor", y=PCT, color="Factor", points="outliers",
                      labels={PCT: ETIQUETA_PCT, "Factor": "Factor (Affected by)"})
    f_factor.update_layout(showlegend=False)

    por_anio = df.groupby("Year", as_index=False)[PCT].mean()
    f_year = px.bar(por_anio, x="Year", y=PCT, text_auto=".1f",
                    labels={PCT: ETIQUETA_PCT, "Year": "Año"})
    f_year.update_xaxes(type="category")
    f_year.update_traces(marker_color="#F5B301")

    por_codigo = df.groupby("state_code", as_index=False)[PCT].mean()
    f_code = px.treemap(por_codigo, path=[px.Constant("EE. UU."), "state_code"], values=PCT,
                        color=PCT, color_continuous_scale=ESCALA,
                        labels={PCT: ETIQUETA_PCT})

    f_pct = px.histogram(df, x=PCT, nbins=40, marginal="box",
                         labels={PCT: ETIQUETA_PCT}, color_discrete_sequence=["#F5B301"])

    return [
        ("State", f_state, "Los 15 estados con mayor porcentaje medio"),
        ("ANSI", f_ansi, "Código ANSI contra porcentaje medio (un punto por estado)"),
        ("Affected by", f_factor, "Distribución del porcentaje según el factor"),
        ("Year", f_year, "Porcentaje medio por año"),
        ("state_code", f_code, "Peso de cada estado en el porcentaje medio"),
        (PCT, f_pct, "Distribución del porcentaje de colonias afectadas"),
    ]


def tarjeta(titulo, subtitulo, figura, alto=340, columnas="col-lg-4 col-md-6"):
    return html.Div(className=f"{columnas} mb-4", children=[
        html.Div(className="card tarjeta h-100", children=[
            html.Div(className="card-header", children=[
                html.Span(titulo, className="titulo-tarjeta"),
                html.Small(subtitulo, className="d-block text-muted"),
            ]),
            html.Div(className="card-body p-2", children=[
                dcc.Graph(figure=estilo(figura, alto), config={"displayModeBar": False}),
            ]),
        ]),
    ])


def tarjeta_columna(columna, figura, resumen):
    return tarjeta(f"Columna: {columna}", f"{descripcion(columna)} · {resumen}", figura)


def etiqueta_control(texto):
    return html.Label(texto, className="etiqueta-control")


# --------------------------------------------------------------------------- layout
app.layout = html.Div(className="fondo-app", children=[
    html.Div(className="encabezado", children=[
        html.Img(src=app.get_asset_url("logo_abejas.svg"), className="logo"),
        html.Div([
            html.H1("Colmenas en Riesgo", className="titulo-app"),
            html.P("Colonias de abejas afectadas por estado, factor y año en EE. UU.",
                   className="subtitulo-app"),
        ]),
    ]),

    html.Div(className="container-fluid px-4", children=[
        html.Div(className="row panel-controles", children=[
            html.Div(className="col-md-4 mb-2", children=[
                etiqueta_control("Año"),
                dcc.Dropdown(id="slct_year",
                             options=[{"label": str(a), "value": a} for a in ANIOS],
                             multi=False, value=ANIOS[0], clearable=False),
            ]),
            html.Div(className="col-md-4 mb-2", children=[
                etiqueta_control("Afectadas por (Affected by)"),
                dcc.Dropdown(id="slct_affected",
                             options=[{"label": n, "value": c} for c, n in FACTORES.items()],
                             multi=False, value="Varroa_mites", clearable=False),
            ]),
            html.Div(className="col-md-4 mb-2", children=[
                etiqueta_control("Estado (para la serie temporal)"),
                dcc.Dropdown(id="slct_state",
                             options=[{"label": e, "value": e} for e in ESTADOS],
                             multi=False, value="California", clearable=False),
            ]),
        ]),

        html.Div(id="output_container", className="resumen", children=[]),

        html.Div(className="card tarjeta mb-4", children=[
            html.Div(className="card-body p-2", children=[
                dcc.Graph(id="my_bee_map", figure={}, config={"displayModeBar": False}),
            ]),
        ]),

        html.H3("Agrupación por State, Affected by y Year", className="titulo-seccion"),
        html.Div(className="row", children=[
            html.Div(className="col-lg-4 col-md-6 mb-4", children=[
                html.Div(className="card tarjeta h-100", children=[
                    html.Div(className="card-header", children=[
                        html.Span("Estado × año", className="titulo-tarjeta"),
                        html.Small("Mapa de calor de los 15 estados más afectados por el factor elegido",
                                   className="d-block text-muted"),
                    ]),
                    html.Div(className="card-body p-2", children=[
                        dcc.Graph(id="heatmap_estado_anio", figure={}, config={"displayModeBar": False}),
                    ]),
                ]),
            ]),
            html.Div(className="col-lg-4 col-md-6 mb-4", children=[
                html.Div(className="card tarjeta h-100", children=[
                    html.Div(className="card-header", children=[
                        html.Span("Factor × año en el estado elegido", className="titulo-tarjeta"),
                        html.Small("Evolución del porcentaje medio de cada factor",
                                   className="d-block text-muted"),
                    ]),
                    html.Div(className="card-body p-2", children=[
                        dcc.Graph(id="linea_estado", figure={}, config={"displayModeBar": False}),
                    ]),
                ]),
            ]),
            html.Div(className="col-lg-4 col-md-12 mb-4", children=[
                html.Div(className="card tarjeta h-100", children=[
                    html.Div(className="card-header", children=[
                        html.Span("Ranking del año y factor elegidos", className="titulo-tarjeta"),
                        html.Small("Los 10 estados con mayor porcentaje", className="d-block text-muted"),
                    ]),
                    html.Div(className="card-body p-2", children=[
                        dcc.Graph(id="ranking_estados", figure={}, config={"displayModeBar": False}),
                    ]),
                ]),
            ]),
        ]),

        html.H3("Descripción de cada columna del dataframe", className="titulo-seccion"),
        html.Div(className="row", children=[
            tarjeta_columna(columna, figura, resumen)
            for columna, figura, resumen in figuras_por_columna()
        ]),

        html.P("Datos: intro_bees.csv · Dash + Plotly · contenedor Docker",
               className="pie-pagina"),
    ]),
])


# --------------------------------------------------------------------------- callbacks
@app.callback(
    [Output(component_id="output_container", component_property="children"),
     Output(component_id="my_bee_map", component_property="figure"),
     Output(component_id="heatmap_estado_anio", component_property="figure"),
     Output(component_id="linea_estado", component_property="figure"),
     Output(component_id="ranking_estados", component_property="figure")],
    [Input(component_id="slct_year", component_property="value"),
     Input(component_id="slct_affected", component_property="value"),
     Input(component_id="slct_state", component_property="value")]
)
def update_graph(anio, factor, estado):
    nombre = FACTORES[factor]

    dff = df[(df["Year"] == anio) & (df["Affected by"] == factor)]
    mayor = dff.loc[dff[PCT].idxmax()]
    container = (f"Año elegido: {anio} · Factor: {nombre} · "
                 f"Promedio nacional: {dff[PCT].mean():.1f} % · "
                 f"Mayor impacto: {mayor['State']} ({mayor[PCT]:.1f} %)")

    tope = df.loc[df["Affected by"] == factor, PCT].max()
    mapa = px.choropleth(
        data_frame=dff,
        locationmode="USA-states",
        locations="state_code",
        scope="usa",
        color=PCT,
        hover_data=["State", PCT],
        color_continuous_scale=ESCALA,
        range_color=(0, tope),
        labels={PCT: ETIQUETA_PCT},
        template=TEMPLATE,
    )
    mapa.update_layout(geo=dict(bgcolor="rgba(0,0,0,0)"))
    estilo(mapa, alto=520)

    sub = df_sya[df_sya["Affected by"] == factor]
    top = sub.groupby("State")[PCT].mean().nlargest(15).index
    tabla = sub[sub["State"].isin(top)].pivot(index="State", columns="Year", values=PCT).loc[top]
    heatmap = px.imshow(tabla, aspect="auto", text_auto=".1f", color_continuous_scale=ESCALA,
                        labels=dict(x="Año", y="Estado", color=ETIQUETA_PCT))
    heatmap.update_xaxes(type="category")

    del_estado = df_sya[df_sya["State"] == estado]
    lineas = px.line(del_estado, x="Year", y=PCT, color="Factor", markers=True,
                     labels={PCT: ETIQUETA_PCT, "Year": "Año"})
    lineas.update_xaxes(dtick=1)
    lineas.update_layout(legend=dict(orientation="h", y=-0.25, title_text=""))

    ranking = dff.nlargest(10, PCT).sort_values(PCT)
    barras = px.bar(ranking, x=PCT, y="State", orientation="h", text_auto=".1f",
                    color=PCT, color_continuous_scale=ESCALA, labels={PCT: ETIQUETA_PCT, "State": ""})

    return (container, mapa, estilo(heatmap), estilo(lineas), estilo(barras))


if __name__ == "__main__":
    app.run_server(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 9000)))  # Render define PORT
