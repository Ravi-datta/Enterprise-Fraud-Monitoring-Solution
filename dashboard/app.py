from __future__ import annotations

import os
import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, State, dash_table, dcc, html

from src.utils import get_settings, read_sql


cfg = get_settings()
app = Dash(__name__)


def load_kpis():
    return read_sql("SELECT * FROM vw_daily_kpis ORDER BY date DESC LIMIT 30")


def load_suspicious(limit: int = 200):
    return read_sql("SELECT * FROM vw_suspicious_latest LIMIT :n", {"n": limit})


app.layout = html.Div(
    [
        html.H2("Fraud Analytics Dashboard"),
        html.Div(
            [
                html.Button("Refresh", id="refresh"),
                dcc.Dropdown(
                    id="channel_filter",
                    options=[{"label": c, "value": c} for c in ["POS", "ECOM", "ATM"]],
                    multi=True,
                    placeholder="Filter by channel",
                ),
            ],
            style={"display": "flex", "gap": "1rem"},
        ),
        dcc.Graph(id="kpi_trend"),
        dcc.Graph(id="alerts_trend"),
        html.H3("Suspicious Transactions (latest)"),
        dash_table.DataTable(
            id="suspicious_table",
            page_size=10,
            filter_action="native",
            sort_action="native",
            columns=[
                {"name": c, "id": c}
                for c in [
                    "tx_id",
                    "ts",
                    "amount",
                    "channel",
                    "merchant_name",
                    "mcc",
                    "rule_name",
                    "proba",
                    "predicted_label",
                ]
            ],
        ),
    ],
    style={"margin": "2rem"},
)


@app.callback(
    Output("kpi_trend", "figure"),
    Output("alerts_trend", "figure"),
    Output("suspicious_table", "data"),
    Input("refresh", "n_clicks"),
    Input("channel_filter", "value"),
)
def refresh_dashboard(n_clicks, channels):
    kpis = load_kpis()
    susp = load_suspicious()
    if channels:
        susp = susp[susp["channel"].isin(channels)]
    fig1 = px.line(kpis.sort_values("date"), x="date", y="tx_count", title="Transactions per Day")
    fig2 = px.line(kpis.sort_values("date"), x="date", y="alerts_count", title="Alerts per Day")
    return fig1, fig2, susp.to_dict("records")


if __name__ == "__main__":
    port = int(cfg["app"]["dashboard_port"])
    app.run_server(debug=False, host="0.0.0.0", port=port)

