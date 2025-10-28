"""
Minimal Dash server mirroring core Streamlit views (upload, overview, suggestions, simple charts).
Run: python dash_app.py (serves on http://127.0.0.1:8050)
"""
from __future__ import annotations

import base64
import io
import pandas as pd
import numpy as np
from dash import Dash, html, dcc, dash_table, Input, Output, State
import plotly.express as px

from utils.data_analyzer import DataAnalyzer


app = Dash(__name__)
app.title = "AI Data Cleaning Assistant (Dash)"

app.layout = html.Div([
    html.H2("AI Data Cleaning Assistant – Dash"),
    dcc.Tabs(id="tabs", value="tab-upload", children=[
        dcc.Tab(label="Upload & Overview", value="tab-upload"),
        dcc.Tab(label="Suggestions", value="tab-suggest"),
        dcc.Tab(label="Visuals", value="tab-visuals"),
    ]),
    html.Div(id="tab-content")
])


def parse_contents(contents: str, filename: str) -> pd.DataFrame | None:
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if filename.lower().endswith('.csv'):
            return pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        if filename.lower().endswith(('.xlsx', '.xls')):
            return pd.read_excel(io.BytesIO(decoded))
        if filename.lower().endswith('.json'):
            return pd.read_json(io.BytesIO(decoded))
    except Exception:
        return None
    return None


upload_layout = html.Div([
    dcc.Upload(
        id='file-upload',
        children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
        style={'width': '100%', 'height': '60px', 'lineHeight': '60px', 'borderWidth': '1px',
               'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px 0'},
        multiple=False
    ),
    html.Div(id='upload-status'),
    html.Div(id='overview'),
])

suggestions_layout = html.Div([
    html.Div(id='suggestions-view')
])

visuals_layout = html.Div([
    html.Div([
        html.Label("Numeric column"),
        dcc.Dropdown(id='numeric-col'),
    ]),
    dcc.Graph(id='hist-plot'),
    dcc.Graph(id='corr-plot')
])


@app.callback(Output('tab-content', 'children'), Input('tabs', 'value'))
def render_tab(tab):
    if tab == 'tab-upload':
        return upload_layout
    if tab == 'tab-suggest':
        return suggestions_layout
    if tab == 'tab-visuals':
        return visuals_layout
    return html.Div()


# Store df in dcc.Store
app.layout.children.append(dcc.Store(id='df-store'))


@app.callback(
    Output('upload-status', 'children'),
    Output('df-store', 'data'),
    Input('file-upload', 'contents'),
    State('file-upload', 'filename'),
)
def on_upload(contents, filename):
    if not contents:
        return "", None
    df = parse_contents(contents, filename)
    if df is None or df.empty:
        return html.Div("Failed to read file."), None
    head = dash_table.DataTable(
        data=df.head(10).to_dict('records'),
        columns=[{"name": c, "id": c} for c in df.columns],
        style_table={'overflowX': 'auto'}
    )
    return html.Div([
        html.Div(f"Loaded: {filename} – {df.shape[0]} rows x {df.shape[1]} cols"),
        head
    ]), df.to_json(date_format='iso', orient='split')


@app.callback(Output('overview', 'children'), Input('df-store', 'data'))
def on_overview(df_json):
    if not df_json:
        return html.Div()
    df = pd.read_json(df_json, orient='split')
    analyzer = DataAnalyzer(df)
    quality = analyzer.get_data_quality_score()
    summary = analyzer.generate_natural_language_summary()

    metrics = html.Div([
        html.Div(f"Rows: {df.shape[0]:,}"),
        html.Div(f"Columns: {df.shape[1]}"),
        html.Div(f"Missing: {int(df.isnull().sum().sum())}"),
        html.Div(f"Duplicates: {int(df.duplicated().sum())}"),
        html.Div(f"Quality: {quality}/100"),
    ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(5, 1fr)', 'gap': '10px', 'marginTop': '10px'})

    return html.Div([
        html.H4('AI Summary'),
        html.P(summary),
        html.Hr(),
        metrics
    ])


@app.callback(Output('suggestions-view', 'children'), Input('df-store', 'data'))
def on_suggestions(df_json):
    if not df_json:
        return html.Div("Upload data to see suggestions.")
    df = pd.read_json(df_json, orient='split')
    analyzer = DataAnalyzer(df)
    sugs = analyzer.generate_suggestions()
    if not sugs:
        return html.Div("No issues detected.")
    items = []
    for key, s in sugs.items():
        items.append(html.Li([html.Strong(key+": "), s.get('issue'), html.Br(), html.Em(s.get('action'))]))
    return html.Div([
        html.H4('Priority Action List'),
        html.Ul(items)
    ])


@app.callback(
    Output('numeric-col', 'options'),
    Output('hist-plot', 'figure'),
    Output('corr-plot', 'figure'),
    Input('df-store', 'data'),
    Input('numeric-col', 'value'),
)
def on_visuals(df_json, col):
    if not df_json:
        return [], px.scatter(), px.imshow(np.array([[0]]))
    df = pd.read_json(df_json, orient='split')
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    hist_fig = px.histogram() if not col else px.histogram(df, x=col, nbins=30)
    corr_fig = px.imshow(df.select_dtypes(include=[np.number]).corr(), color_continuous_scale='RdBu', zmin=-1, zmax=1)
    return [{'label': c, 'value': c} for c in numeric_cols], hist_fig, corr_fig


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
