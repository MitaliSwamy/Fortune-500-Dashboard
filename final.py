# final_dashboard_clean.py
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
from datetime import datetime
from sqlalchemy import create_engine

# ---------------- DB CONFIG ----------------
DB_USER = "root"
DB_PASS = "mits123456"   
DB_HOST = "localhost"
DB_NAME = "fort500"

# SQLAlchemy engine
engine = create_engine(f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}")

# ---------------- DB HELPERS ----------------
def fetch_companies():
    query = "SELECT * FROM companies ORDER BY sr_no"
    return pd.read_sql(query, con=engine)

def fetch_financials():
    query = """
        SELECT c.sr_no, c.name, f.revenue, f.profit, f.market_value, f.employees, f.run_timestamp
        FROM companies c
        JOIN financials f ON c.sr_no = f.sr_no
        ORDER BY f.run_timestamp
    """
    return pd.read_sql(query, con=engine)

def fetch_heatmap(top_n=20, year_min=None, year_max=None):
    """
    Build a clearer heatmap:
      - top_n: number of companies to show (by max revenue)
      - year_min/year_max: optional year filter (ints)
    Returns a Plotly figure.
    """
    query = """
        SELECT f.run_timestamp AS year, c.name AS company, f.revenue
        FROM companies c
        JOIN financials f ON c.sr_no = f.sr_no
    """
    df = pd.read_sql(query, con=engine)

    # Robust cleaning
    df['revenue'] = pd.to_numeric(df['revenue'].replace(r'[\$,]', '', regex=True),
                                  errors='coerce').fillna(0)

    # Convert timestamp to year
    df['year'] = pd.to_datetime(df['year'], errors='coerce').dt.year
    df = df.dropna(subset=['year'])
    df['year'] = df['year'].astype(int)

    # Optional year filters
    if year_min is not None:
        df = df[df['year'] >= int(year_min)]
    if year_max is not None:
        df = df[df['year'] <= int(year_max)]

    # Rank companies by max revenue across years
    company_rank = df.groupby('company')['revenue'].max().sort_values(ascending=False)
    top_companies = company_rank.head(top_n).index.tolist()

    # Filter only top companies
    df_filtered = df[df['company'].isin(top_companies)].copy()

    # Pivot to Company x Year
    heatmap_data = df_filtered.pivot_table(
        index="company",
        columns="year",
        values="revenue",
        aggfunc="mean"
    ).fillna(0)

    # Ensure sorted years
    heatmap_data = heatmap_data.reindex(sorted(heatmap_data.columns), axis=1)

    # Preserve ranking order
    heatmap_data = heatmap_data.reindex([c for c in company_rank.index if c in heatmap_data.index])

    # Plot
    fig = px.imshow(
        heatmap_data,
        labels=dict(x="Year", y="Company", color="Revenue"),
        x=heatmap_data.columns,
        y=heatmap_data.index,
        aspect="auto",
        color_continuous_scale="Viridis"
    )

    # Dynamic sizing
    row_height = 40
    computed_height = max(400, row_height * len(heatmap_data.index) + 150)
    fig.update_layout(
        title=f"Top {min(top_n, len(heatmap_data.index))} Companies by Revenue",
        width=1100,
        height=computed_height,
        margin=dict(l=220, r=80, t=80, b=80)
    )

    # Axis & hover improvements
    fig.update_yaxes(tickfont=dict(size=12), automargin=True)
    fig.update_xaxes(tickangle=45, tickfont=dict(size=12))
    fig.update_coloraxes(colorbar=dict(title='Revenue', tickformat=',.0f'))
    fig.data[0].hovertemplate = 'Company: %{y}<br>Year: %{x}<br>Revenue: %{z:$,.0f}<extra></extra>'

    return fig

# ---------------- DASH APP ----------------
app = dash.Dash(__name__)
app.title = "Fortune 500 Dashboard"

app.layout = html.Div([
    html.H1("Fortune 500 Dashboard"),

    html.Div([
        html.Label("Select Company:"),
        dcc.Dropdown(id='company-dropdown', options=[], value=None)
    ]),

    html.Br(),
    dcc.Graph(id='revenue-trend'),
    dcc.Graph(id='profit-trend'),

    html.H2("Revenue Heatmap"),

    html.Div([
        html.Label("Show top N companies:"),
        dcc.Slider(id='heatmap-top-n', min=5, max=50, step=5, value=20,
                   marks={5:'5',10:'10',20:'20',30:'30',40:'40',50:'50'}),
        html.Br()
    ]),

    dcc.Graph(id='revenue-heatmap'),

    html.H2("Company Data Table"),
    html.Label("Search Company Name:"),
    dcc.Input(id='search-input', type='text', placeholder='Enter company name'),
    html.Button("Search", id='search-btn', n_clicks=0),
    html.Button("Export CSV", id='export-btn', n_clicks=0),
    html.Div(id='export-msg', style={"margin-top": "10px"}),

    dash_table.DataTable(
        id='data-table',
        columns=[],
        data=[],
        page_size=10,
        filter_action="native",
        sort_action="native"
    )
])

# ---------------- CALLBACKS ----------------
@app.callback(
    Output('company-dropdown', 'options'),
    Input('company-dropdown', 'value')
)
def update_dropdown(_):
    df = fetch_companies()
    return [{"label": row["name"], "value": row["sr_no"]} for _, row in df.iterrows()]

@app.callback(
    Output('revenue-trend', 'figure'),
    Output('profit-trend', 'figure'),
    Input('company-dropdown', 'value')
)
def update_graphs(sr_no):
    if sr_no is None:
        return {}, {}

    df = fetch_financials()
    df = df[df['sr_no'] == sr_no]
    df['revenue'] = df['revenue'].replace(r'[\$,]', '', regex=True).astype(float)
    df['profit'] = df['profit'].replace(r'[\$,]', '', regex=True).astype(float)

    fig_revenue = px.line(df, x='run_timestamp', y='revenue', title='Revenue Over Time')
    fig_profit = px.line(df, x='run_timestamp', y='profit', title='Profit Over Time')

    return fig_revenue, fig_profit

@app.callback(
    Output('data-table', 'columns'),
    Output('data-table', 'data'),
    Input('search-btn', 'n_clicks'),
    State('search-input', 'value')
)
def update_table(n_clicks, search_text):
    df = fetch_companies()
    if search_text:
        df = df[df['name'].str.contains(search_text, case=False, na=False)]

    columns = [{"name": i, "id": i} for i in df.columns]
    data = df.to_dict('records')
    return columns, data

@app.callback(
    Output('export-msg', 'children'),
    Input('export-btn', 'n_clicks'),
    State('search-input', 'value')
)
def export_csv(n_clicks, search_text):
    if n_clicks == 0:
        return ""

    df = fetch_companies()
    if search_text:
        df = df[df['name'].str.contains(search_text, case=False, na=False)]

    filename = f"companies_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False)
    return f"✅ Data exported to {filename}"

@app.callback(
    Output('revenue-heatmap', 'figure'),
    Input('heatmap-top-n', 'value')
)
def update_heatmap(top_n):
    return fetch_heatmap(top_n=top_n)

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True, port=8050)

