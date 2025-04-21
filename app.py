# app.py

import os
from dotenv import load_dotenv
import pandas as pd
from dash import Dash, dcc, html, callback_context
from dash.dependencies import Input, Output
import pycountry
import plotly.graph_objs as go
from fetch_wb import fetch_indicator_data, INDICATOR_NAME_MAP

# ─── Load .env ─────────────────────────────────────────────────────────────
load_dotenv()
START_YEAR = int(os.getenv("START_YEAR", 2004))
END_YEAR   = int(os.getenv("END_YEAR", 2023))

# ─── Country map ────────────────────────────────────────────────────────────
COUNTRY_NAME_MAP = {
    "ARG":"Argentina", "BHS":"Bahamas",   "BRB":"Barbados", "BLZ":"Belize",
    "BOL":"Bolivia",   "BRA":"Brazil",    "CHL":"Chile",    "COL":"Colombia",
    "CRI":"Costa Rica","DOM":"Dominican Republic","ECU":"Ecuador","SLV":"El Salvador",
    "GTM":"Guatemala","GUY":"Guyana",      "HTI":"Haiti",    "HND":"Honduras",
    "JAM":"Jamaica",   "MEX":"Mexico",    "NIC":"Nicaragua","PAN":"Panama",
    "PRY":"Paraguay",  "PER":"Peru",      "SUR":"Suriname","TTO":"Trinidad and Tobago",
    "URY":"Uruguay",   "VEN":"Venezuela"
}

# ─── Build country dropdown  -------------───────────────────────────────────
country_options = [
    {"label": name, "value": code}
    for code, name in COUNTRY_NAME_MAP.items()
]

# ─── Indicator dropdown options ─────────────────────────────────────────────
indicator_options = [
    {"label": name, "value": name}
    for name in INDICATOR_NAME_MAP.values()
]

# ─── Build DataFrame for one country ────────────────────────────────────────
def build_country_df(country_code: str) -> pd.DataFrame:
    data = {}
    missing = {}  # track missing years per indicator
    for code, name in INDICATOR_NAME_MAP.items():
        raw = fetch_indicator_data(country_code, code)
        # year→value
        series = {int(dp["date"]): dp["value"] for dp in raw}
        s = pd.Series(series, name=name)
        s = s.reindex(range(START_YEAR, END_YEAR+1)).astype(float)
        # record which years were missing
        missing[name] = set(s[s.isna()].index)
        # interpolate
        s.interpolate(method="linear", limit_direction="both", inplace=True)
        data[name] = s

    df = pd.DataFrame(data)
    return df, missing

# ─── Dash app ───────────────────────────────────────────────────────────────
app = Dash(__name__, suppress_callback_exceptions=True)

app.layout = html.Div(
    style={"font-family":"Arial, sans-serif","margin":"20px"},
    children=[
        # Title & subtitle
        html.H1(
            "Prototype Dashboard with Key Indicators for the International Development Bank (IDB)",
            style={"margin-bottom":"4px", "font-size":"24px", "color":"var(--text-color)"}
        ),
        html.H2(
            "In the context of the application for the OVE's \"Data Scientist - Senior Associate\" open position",
            style={"margin-top":"0","margin-bottom":"20px","font-size":"16px","font-weight":"bold","color":"var(--text-color)"}
        ),
        
        html.H2(
            "By Fabián A. Araneda-Baltierra",
            style={"margin-top":"0","margin-bottom":"20px","font-size":"16px","font-weight":"normal","color":"var(--text-color)"}
        ),
        
        dcc.Store(id="theme-store", data="light"),  # for light/dark

        # Info banner
        html.Div(
            "✅ This dashboard pulls data on-the-fly from the World Bank API. "
            "Once fetched, results are cached for the session, so you won't see "
            "re-downloads as long as this page stays open.",
            className="info-banner",
            style={"padding":"10px","background":"#e8f5e9","border-radius":"5px",
                "margin-bottom":"20px"}
        ),

        # Country selector
        html.Div([
            html.Label("Choose a country:", style={"font-weight":"bold"}),
            dcc.Dropdown(
                id="country-dropdown",
                options=country_options,
                placeholder="Select a country…",
                style={"width":"360px", "color":"var(--text-color)", "background":"var(--page-bg)"}
            )
        ], style={"margin-bottom":"30px"}),

        # Container for dynamic dashboard
        html.Div(id="dashboard-content")
    ]
)

# ─── Detect OS theme client‑side ────────────────────────────────────────────
app.clientside_callback(
    """
    function(_opts) {
        return window.matchMedia('(prefers-color-scheme: dark)').matches
            ? 'dark' : 'light';
    }
    """,
    Output("theme-store","data"),
    Input("country-dropdown","options")  # fires once at init
)

# ─── Render dashboard when country chosen ───────────────────────────────────
@app.callback(
    Output("dashboard-content", "children"),
    Input("country-dropdown", "value")
)
def render_dashboard(country_code):
    if not country_code:
        return html.Div(), None

    # Build df + missing map once
    df, missing = build_country_df(country_code)

    # ─── Indicator selector ────────────────────────────────────────────────
    indicator_dropdown = html.Div([
        html.Label("Choose an indicator to plot [2004-2023]:", style={"font-weight":"bold","margin-bottom":"4px"}),
        dcc.Dropdown(
            id="indicator-dropdown",
            options=[{"label":n,"value":n} for n in INDICATOR_NAME_MAP.values()],
            value=list(INDICATOR_NAME_MAP.values())[0],
            style={"width":"360px","color":"var(--text-color)","background":"var(--page-bg)"}
        )
    ], style={"margin-bottom":"20px"})

    # ─── Main plot ─────────────────────────────────────────────────────────
    # ─── Responsive side‑by‑side layout ────────────────────────────────────
    chart_box = html.Div(
        dcc.Graph(id="indicator-graph", style={"width":"100%"}),
        style={
            "flex": "3 1 300px",    # grow 3x, shrink, min‑width 300px
            "min-width": "300px"
        }
    )

    years_desc = list(range(START_YEAR, END_YEAR+1))[::-1]
    year_selector = dcc.Dropdown(
        id="year-dropdown",
        options=[{"label":str(y),"value":y} for y in years_desc],
        value=END_YEAR,
        style={
            "width":"100%",
            "margin-bottom":"10px",
            "color":"var(--text-color)",
            "background":"var(--page-bg)"
        }
    )
    table_box = html.Div(
        [
            # New title above the table
            html.H4("Data Table for Indicators", style={"margin":"0 0 8px 0"}),
            year_selector,
            html.Div(id="table-container", style={"width":"100%"})
        ],
        style={
            "flex": "1 1 300px",     # allow grow/shrink, but min‑width now 300px
            "min-width": "300px",    # bumped up so it wraps earlier
            "display":"flex",
            "flex-direction":"column"
        }
    )

    side_by_side = html.Div(
        [ chart_box, table_box ],
        style={
            "display":"flex",
            "flex-wrap":"wrap",     # allow table to wrap below on narrow screens
            "gap":"20px",
            "margin-bottom":"30px"
        }
    )

    # ─── Static tiles (latest values) ───────────────────────────────────────
    latest_tiles = html.Div(style={"display":"flex","flex-wrap":"wrap","gap":"10px"}, children=[
        html.Div([
            html.Div(col, style={"font-size":"14px","font-weight":"bold","text-align":"left"}),
            html.Br(),
            html.Div(f"[{df[col].dropna().index[-1]}]" if not df[col].dropna().empty else "N/A",
                     style={"text-align":"center","font-size":"12px"}),
            html.Div(f"{df[col].dropna().iloc[-1]:,.2f}" if not df[col].dropna().empty else "N/A",
                     style={"text-align":"center","font-size":"18px","font-weight":"bold"})
        ], style={
            "flex":"1 0 150px",
            "padding":"10px",
            "border":"1px solid var(--tile-border)",
            "border-radius":"6px",
            "box-shadow":"1px 1px 3px var(--tile-shadow)",
            "background-color":"var(--tile-bg)"
        })
        for col in df.columns
    ])
    
    # Build a flag URL via the ISO2 code
    iso2 = pycountry.countries.get(alpha_3=country_code).alpha_2.lower()
    flag_url = f"https://flagcdn.com/32x24/{iso2}.png"

    # Header with flag instead of the 📊 emoji
    header = html.H3([
        html.Img(src=flag_url,
                 style={"margin-right":"8px","vertical-align":"middle"}),
        COUNTRY_NAME_MAP[country_code]
    ])

    children = html.Div([
        header,
        indicator_dropdown,
        side_by_side,
        html.H4("Latest values on record"),
        latest_tiles
    ])

    return children

# ─── Update graph when indicator or theme changes ──────────────────────────
@app.callback(
    Output("indicator-graph","figure"),
    Input("country-dropdown","value"),
    Input("indicator-dropdown","value"),
    Input("theme-store","data")
)
def update_graph(country_code, indicator_name, theme):
    if not country_code or not indicator_name:
        return {}

    df, missing = build_country_df(country_code)
    years = df.index.tolist()
    values = df[indicator_name].tolist()

    # Build custom hover text:
    hover_text = []
    for y, v in zip(years, values):
        if y in missing[indicator_name]:
            hover_text.append(
                f"{indicator_name}<br>{y}: interpolated<br>"
                "No data recorded for this year"
            )
        else:
            hover_text.append(f"{indicator_name}<br>{y}: {v:,.2f}")

    # Choose template
    tpl = "plotly_dark" if theme == "dark" else "plotly_white"

    trace = go.Scatter(
        x=years, y=values,
        mode="lines",
        line={"shape":"spline"},       # smooth
        fill="tozeroy",                # area under curve
        hoverinfo="text",
        hovertext=hover_text
    )

    layout = go.Layout(
        template=tpl,
        title=f"{indicator_name} ({country_code})",
        xaxis={"title":"Year"},
        yaxis={"title":indicator_name},
        margin=dict(l=40, r=20, t=50, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    return {"data":[trace], "layout":layout}

# ─── NEW CALLBACK: populate the HTML table ───────────────────────────────
@app.callback(
    Output("table-container", "children"),
    [
      Input("country-dropdown", "value"),
      Input("year-dropdown",    "value")
    ]
)
def update_table(country_code, selected_year):
    if not country_code or selected_year is None:
        return ""

    # rebuild the DF
    df, _ = build_country_df(country_code)

    # collect indicator & value pairs
    rows = [
        {"Indicator": col, "Value": df[col].get(selected_year)}
        for col in df.columns
    ]

    # build the HTML table
    header = html.Tr([
        html.Th("Indicator", style={"border":"1px solid var(--tile-border)",
                                    "padding":"6px","background":"var(--tile-bg)",
                                    "color":"var(--text-color)"}),
        html.Th("Value",     style={"border":"1px solid var(--tile-border)",
                                    "padding":"6px","background":"var(--tile-bg)",
                                    "color":"var(--text-color)"})
    ])

    body = []
    for r in rows:
        val = r["Value"]
        # Use pandas to catch NaN as well as None
        if val is None or pd.isna(val):
            disp = "N/A"
        else:
            disp = f"{val:,.2f}"
            
        body.append(html.Tr([
            html.Td(r["Indicator"],
                    style={"border":"1px solid var(--tile-border)",
                           "padding":"6px","color":"var(--text-color)"}),
            html.Td(disp,
                    style={"border":"1px solid var(--tile-border)",
                           "padding":"6px","color":"var(--text-color)"})
        ]))

    table = html.Table([header] + body,
        style={
            "width":"100%",
            "border-collapse":"collapse",
            "margin-top":"0px"
        }
    )

    # wrap in a styled box like your tiles
    return html.Div(table, style={
        "border":"1px solid var(--tile-border)",
        "border-radius":"6px",
        "box-shadow":"1px 1px 3px var(--tile-shadow)",
        "background-color":"var(--tile-bg)",
        "padding":"10px"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)