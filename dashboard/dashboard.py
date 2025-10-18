from dash import Dash, html, dcc, Input, Output, State
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import boto3
from boto3.dynamodb.conditions import Key
import requests
from datetime import datetime, timedelta, date
from io import StringIO
import os
import math
from callbacks import update_chart
from dotenv import load_dotenv

load_dotenv()

# AWS configuration 
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_REGION = 'us-east-1'

dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    region_name='us-east-1'
)
table = dynamodb.Table('crypto-prices')

def get_data(table, time1, time2):
    try:
        response = table.query(
            KeyConditionExpression =Key('PK').eq('CRYPTO_PRICES') &
                                    Key('timestamp').between(time1, time2)
        )
        df = pd.DataFrame(response['Items']).drop(columns=['ttl', 'PK'])
        return df
    except Exception as e:
        raise Exception(f'Query failed: {e}')


app = Dash(__name__)

app.layout = html.Div([
    # Header
    html.Div([
        html.H1('Crypto Dashboard', 
                style={
                    'color': '#FFF',
                    'textAlign': 'center',
                    'margin': '0',
                    'padding': '30px',
                    'fontSize': '42px',
                    'fontWeight': '700',
                    'letterSpacing': '1px'
                }),
    ], style={
        'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'boxShadow': '0 4px 6px rgba(0,0,0,0.3)',
        'marginBottom': '30px'
    }),
    
    # Main container
    html.Div([
        dcc.Store(id='news-data-store'),
        dcc.Store(id='crypto-data-store'),
        
        # Left sidebar - Controls
        html.Div([
            # Crypto Selector Section
            html.Div([
                html.Div([
                    html.Span('₿', style={'fontSize': '26px', 'marginRight': '10px'}),
                    html.Span('Cryptocurrencies', style={'fontSize': '22px', 'fontWeight': '600'})
                ], style={'marginBottom': '10px', 'display': 'flex', 'alignItems': 'center'}),
                
                html.P('Choose which cryptocurrencies to display on the chart', 
                       style={'color': '#888', 'fontSize': '13px', 'marginBottom': '15px', 'fontStyle': 'italic'}),
                
                dcc.Checklist(
                    id='crypto-selector',
                    options=[
                        {'label': 'Bitcoin', 'value': 'bitcoin'},
                        {'label': 'Ethereum', 'value': 'ethereum'},
                        {'label': 'Tether', 'value': 'tether'},
                        {'label': 'Binance Coin', 'value': 'binancecoin'},
                        {'label': 'Solana', 'value': 'solana'},
                        {'label': 'Cardano', 'value': 'cardano'},
                        {'label': 'Dogecoin', 'value': 'dogecoin'},
                        {'label': 'Ripple', 'value': 'ripple'},
                        {'label': 'Tron', 'value': 'tron'},
                        {'label': 'USD Coin', 'value': 'usd-coin'},
                    ],
                    value=['bitcoin'],
                    inline=False,
                    style={'color': '#E0E0E0', 'fontSize': '17px'},
                    labelStyle={'display': 'block', 'marginBottom': '10px', 'cursor': 'pointer'}
                ),
                
                # Time Range Section (below crypto selector)
                html.Div([
                    html.Hr(style={'border': 'none', 'borderTop': '1px solid #333', 'margin': '20px 0'}),
                    
                    html.Div([
                        html.Span('📅', style={'fontSize': '22px', 'marginRight': '8px'}),
                        html.Span('Time Range', style={'fontSize': '18px', 'fontWeight': '600'})
                    ], style={'marginBottom': '10px', 'display': 'flex', 'alignItems': 'center'}),
                    
                    html.P('Select the date range for cryptocurrency data', 
                           style={'color': '#888', 'fontSize': '12px', 'marginBottom': '12px', 'fontStyle': 'italic'}),
                    
                    dcc.DatePickerRange(
                        id='date-picker-range',
                        min_date_allowed=date(2025, 10, 13),
                        max_date_allowed=(datetime.now() - timedelta(hours=1)).date(),
                        start_date=(datetime.now() - timedelta(days=1)).date(),
                        end_date=datetime.now().date(),
                        display_format='YYYY-MM-DD',
                    ),
                ]),
            ], style={
                'padding': '20px',
                'backgroundColor': '#1E1E1E',
                'borderRadius': '12px',
                'boxShadow': '0 2px 8px rgba(0,0,0,0.3)',
                'border': '1px solid #333'
            }),

        ], style={'width': '280px', 'marginRight': '30px', 'flexShrink': '0'}),

        # Right panel - Chart and News
        html.Div([
            # News Section
            html.Div([
                html.Div([
                    html.Span('📰', style={'fontSize': '26px', 'marginRight': '10px'}),
                    html.Span('News Search', style={'fontSize': '22px', 'fontWeight': '600'})
                ], style={'marginBottom': '10px', 'display': 'flex', 'alignItems': 'center'}),
                
                html.P('Search for news articles related to people and keywords affecting crypto markets', 
                       style={'color': '#888', 'fontSize': '13px', 'marginBottom': '20px', 'fontStyle': 'italic'}),
                
                html.Div([
                    # Left column - People, Keywords, Sources
                    html.Div([
                        # People Selector
                        html.Div([
                            html.Label('People:', style={'color': '#B0B0B0', 'fontSize': '15px', 'marginRight': '15px', 'minWidth': '100px'}),
                            dcc.Dropdown(
                                id='news-personality-preset',
                                options=[
                                    {'label': 'Donald Trump', 'value': 'Trump'},
                                    {'label': 'Elon Musk', 'value': 'Musk'},
                                    {'label': 'Vladimir Putin', 'value': 'Putin'},
                                    {'label': 'Christine Lagarde', 'value': 'Lagarde'},
                                ],
                                placeholder='Select people...',
                                multi=True,
                                style={'width': '300px', 'marginRight': '15px'},
                                className='dark-dropdown'
                            ),
                            html.Span('or', style={'color': '#B0B0B0', 'fontSize': '14px', 'marginRight': '15px'}),
                            dcc.Input(
                                id='news-personality-custom',
                                type='text',
                                placeholder='TO BE IMPLEMENTED...',
                                style={
                                    'width': '350px',
                                    'padding': '8px 12px',
                                    'backgroundColor': '#2D2D2D',
                                    'border': '1px solid #444',
                                    'borderRadius': '4px',
                                    'color': '#E0E0E0',
                                    'fontSize': '14px'
                                }
                            ),
                        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '15px'}),

                        # Keywords Selector
                        html.Div([
                            html.Label('Keywords:', style={'color': '#B0B0B0', 'fontSize': '15px', 'marginRight': '15px', 'minWidth': '100px'}),
                            dcc.Dropdown(
                                id='keyword-preset',
                                options=[
                                    {'label': 'Cryptocurrency', 'value': 'cryptocurrency'},
                                    {'label': 'Bitcoin', 'value': 'bitcoin'},
                                    {'label': 'Regulation', 'value': 'regulation'},
                                    {'label': 'Market', 'value': 'market'},
                                ],
                                placeholder='Select keywords...',
                                multi=True,
                                style={'width': '300px', 'marginRight': '15px'},
                                className='dark-dropdown'
                            ),
                            html.Span('or', style={'color': '#B0B0B0', 'fontSize': '14px', 'marginRight': '15px'}),
                            dcc.Input(
                                id='keyword-custom',
                                type='text',
                                placeholder='Custom keywords (comma-separated)...',
                                style={
                                    'width': '350px',
                                    'padding': '8px 12px',
                                    'backgroundColor': '#2D2D2D',
                                    'border': '1px solid #444',
                                    'borderRadius': '4px',
                                    'color': '#E0E0E0',
                                    'fontSize': '14px'
                                }
                            ),
                        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '15px'}),

                        # Sources Selector
                        html.Div([
                            html.Label('Sources:', style={'color': '#B0B0B0', 'fontSize': '15px', 'marginRight': '15px', 'minWidth': '100px'}),
                            dcc.Dropdown(
                                id='source-preset',
                                options=[
                                    {'label': 'Wall Street Journal', 'value': 'wsj.com'},
                                    {'label': 'Financial Times', 'value': 'ft.com'},
                                    {'label': 'New York Times', 'value': 'nytimes.com'},
                                    {'label': 'Bloomberg', 'value': 'bloomberg.com'},
                                    {'label': 'CoinDesk', 'value': 'coindesk.com'},
                                ],
                                value=['wsj.com', 'ft.com', 'nytimes.com', 'bloomberg.com', 'coindesk.com'],
                                placeholder='Select sources...',
                                multi=True,
                                style={'width': '300px', 'marginRight': '15px'},
                                className='dark-dropdown'
                            ),
                            html.Span('or', style={'color': '#B0B0B0', 'fontSize': '14px', 'marginRight': '15px'}),
                            dcc.Input(
                                id='source-custom',
                                type='text',
                                placeholder='Custom sources (comma-separated)...',
                                style={
                                    'width': '350px',
                                    'padding': '8px 12px',
                                    'backgroundColor': '#2D2D2D',
                                    'border': '1px solid #444',
                                    'borderRadius': '4px',
                                    'color': '#E0E0E0',
                                    'fontSize': '14px'
                                }
                            ),
                        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '15px'}),
                    ], style={'flex': '1', 'marginRight': '30px'}),

                    # Right column - Time Range and Button
                    html.Div([
                        html.Label('News Time Range:', style={'color': '#B0B0B0', 'fontSize': '15px', 'marginBottom': '8px', 'display': 'block'}),
                        dcc.DatePickerRange(
                            id='news-date-range',
                            min_date_allowed=date(2025, 10, 13),
                            max_date_allowed=datetime.now().date(),
                            start_date=date(2025, 10, 13),
                            end_date=date(2025, 10, 16),
                            display_format='YYYY-MM-DD',
                            style={'marginBottom': '10px'}
                        ),
                        html.Button(
                            '↻ Sync with Crypto',
                            id='sync-dates-button',
                            n_clicks=0,
                            style={
                                'width': '100%',
                                'padding': '8px 16px',
                                'backgroundColor': '#444',
                                'color': '#E0E0E0',
                                'border': '1px solid #666',
                                'borderRadius': '4px',
                                'fontSize': '13px',
                                'cursor': 'pointer',
                                'marginBottom': '30px'
                            }
                        ),
                        html.Button(
                            'Search News',
                            id='search-news-button',
                            n_clicks=0,
                            style={
                                'width': '100%',
                                'padding': '12px 16px',
                                'backgroundColor': '#627EEA',
                                'color': '#FFFFFF',
                                'border': 'none',
                                'borderRadius': '6px',
                                'fontSize': '15px',
                                'fontWeight': '600',
                                'cursor': 'pointer',
                            }
                        )
                    ], style={'width': '270px', 'marginRight': '10px'}),
                ], style={'display': 'flex', 'marginBottom': '15px'}),

                html.Div(id='news-status', style={'textAlign': 'center'}),

            ], style={
                'padding': '20px',
                'backgroundColor': '#1E1E1E',
                'borderRadius': '8px',
                'marginBottom': '20px',
                'border': '1px solid #333'
            }),

            # Display Mode Section
            html.Div([
                html.Label('Display Mode:', style={'color': '#B0B0B0', 'fontSize': '15px', 'marginRight': '15px'}),
                dcc.RadioItems(
                    id='plot-mode',
                    options=[
                        {'label': ' Overlaid (Same Y)', 'value': 'overlaid'},
                        {'label': ' Overlaid (Multi Y)', 'value': 'multi_y'},
                        {'label': ' Separated', 'value': 'separated'}
                    ],
                    value='overlaid',
                    inline=True,
                    style={'color': '#E0E0E0', 'fontSize': '15px'},
                    labelStyle={'marginRight': '20px', 'cursor': 'pointer'}
                ),
            ], style={
                'display': 'flex',
                'alignItems': 'center',
                'padding': '15px 20px',
                'backgroundColor': '#1E1E1E',
                'borderRadius': '8px',
                'marginBottom': '20px',
                'border': '1px solid #333'
            }),
            
            # Chart Container
            html.Div([
                dcc.Graph(
                    id='chart',
                    config={
                        'displayModeBar': True,
                        'displaylogo': False,
                        'modeBarButtonsToRemove': ['lasso2d', 'select2d']
                    }
                )
            ], style={
                'backgroundColor': '#1E1E1E',
                'borderRadius': '12px',
                'padding': '20px',
                'boxShadow': '0 2px 8px rgba(0,0,0,0.3)',
                'border': '1px solid #333'
            }),

        ], style={'flex': '1'}),
        
    ], style={
        'display': 'flex',
        'padding': '0 30px 30px 30px',
        'maxWidth': '1600px',
        'margin': '0 auto'
    }),
    
], style={
    'backgroundColor': '#0F0F0F',
    'minHeight': '100vh',
    'color': '#FFF'
})


# Callback to sync news dates with crypto dates
@app.callback(
    [Output('news-date-range', 'start_date'),
     Output('news-date-range', 'end_date')],
    [Input('sync-dates-button', 'n_clicks')],
    [State('date-picker-range', 'start_date'),
     State('date-picker-range', 'end_date')]
)
def sync_dates(n_clicks, crypto_start, crypto_end):
    if n_clicks == 0:
        return date(2025, 10, 13), date(2025, 10, 16)
    return crypto_start, crypto_end


# Query database and store data
@app.callback(
    Output('crypto-data-store', 'data'),  
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')]
)
def query_database(start_date, end_date):
    start_time = f"{start_date}T12:00:00"
    end_time = f"{end_date}T12:59:59"
    
    df_all = get_data(table, start_time, end_time)
    data_json = df_all.to_json(date_format='iso', orient='split')
    
    return data_json


# Update chart display
@app.callback(
    Output('chart', 'figure'),
    [Input('crypto-data-store', 'data'),
     Input('crypto-selector', 'value'),
     Input('plot-mode', 'value')]
)
def chart_callback(stored_data, selected_cryptos, plot_mode):
    return update_chart(stored_data, selected_cryptos, plot_mode)


# Search news
@app.callback(
    [Output('news-data-store', 'data'),
     Output('news-status', 'children')],
    [Input('search-news-button', 'n_clicks')],
    [State('news-personality-preset', 'value'),
     State('news-personality-custom', 'value'),
     State('keyword-preset', 'value'),
     State('keyword-custom', 'value'),
     State('source-preset', 'value'),
     State('source-custom', 'value'),
     State('news-date-range', 'start_date'),
     State('news-date-range', 'end_date')]
)
def search_news(n_clicks, preset_people, custom_people, preset_keywords, custom_keywords, 
                preset_sources, custom_sources, news_start, news_end):
    
    if not n_clicks:
        return None, ""
    
    try:
        # Combine preset and custom inputs
        people = []
        if preset_people:
            people.extend(preset_people)
        if custom_people and custom_people.strip():
            people.extend([name.strip() for name in custom_people.split(',') if name.strip()])
        
        keywords = []
        if preset_keywords:
            keywords.extend(preset_keywords)
        if custom_keywords and custom_keywords.strip():
            keywords.extend([kw.strip() for kw in custom_keywords.split(',') if kw.strip()])
        
        sources = []
        if preset_sources:
            sources.extend(preset_sources)
        if custom_sources and custom_sources.strip():
            sources.extend([src.strip() for src in custom_sources.split(',') if src.strip()])
        
        # Validation
        if not people:
            return None, html.Div("⚠️ Please select at least one person", 
                                  style={'color': '#FF6B6B', 'marginTop': '10px'})
        
        if not keywords:
            keywords = ["bitcoin"]
        
        if not sources:
            sources = ["wsj.com", "ft.com", "nytimes.com", "bloomberg.com", "coindesk.com"]
        
        # Convert dates to GDELT format
        start_dt = datetime.strptime(news_start, '%Y-%m-%d').strftime('%Y%m%d000000')
        end_dt = datetime.strptime(news_end, '%Y-%m-%d').strftime('%Y%m%d235959')
        
        # GDELT API setup
        base_url = "https://api.gdeltproject.org/api/v2/doc/doc"
        proximity = 15
        all_news = []
        
        # Search for each person separately
        for personality in people:
            domain_filters = " OR ".join([f"domainis:{d}" for d in sources])
            near_queries = ' OR '.join([f'near{proximity}:"{personality} {kw}"' for kw in keywords])
            
            full_query = f"({near_queries}) sourcelang:English ({domain_filters})" if len(keywords) > 1 else f"{near_queries} sourcelang:English ({domain_filters})"
            
            params = {
                "query": full_query,
                "mode": "artlist",
                "format": "csv",
                "startdatetime": start_dt,
                "enddatetime": end_dt,
                "sort": "datedesc",
                "maxrecords": 250
            }
            
            response = requests.get(base_url, params=params, timeout=30)
            
            if response.status_code == 200 and response.text.strip():
                csv_data = StringIO(response.text)
                df_person = pd.read_csv(csv_data)
                
                if not df_person.empty:
                    df_person['person'] = personality
                    all_news.append(df_person)
        
        # Combine results
        if all_news:
            df_news = pd.concat(all_news, ignore_index=True)
            
            if 'seendate' in df_news.columns:
                df_news = df_news.sort_values('seendate', ascending=False)
            
            news_json = df_news.to_json(orient='split', date_format='iso')
            
            person_counts = df_news['person'].value_counts().to_dict()
            breakdown = ", ".join([f"{person}: {count}" for person, count in person_counts.items()])
            
            status_msg = html.Div([
                html.Div([
                    html.Span("✓ ", style={'color': '#4CAF50', 'fontSize': '18px'}),
                    html.Span(f"Found {len(df_news)} total articles", 
                             style={'color': '#4CAF50', 'fontSize': '14px', 'fontWeight': '600'})
                ]),
                html.Div(breakdown, 
                        style={'color': '#B0B0B0', 'fontSize': '12px', 'marginTop': '5px'})
            ], style={'marginTop': '10px'})
            
            return news_json, status_msg
        else:
            return None, html.Div("⚠️ No articles found", 
                                  style={'color': '#FFA726', 'marginTop': '10px'})
    
    except Exception as e:
        return None, html.Div(f"❌ Error: {str(e)}", 
                              style={'color': '#FF6B6B', 'marginTop': '10px', 'fontSize': '12px'})


app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * {
                font-family: 'Montserrat', sans-serif !important;
            }
            
            .dark-dropdown .Select-control {
                background-color: #2D2D2D !important;
                border-color: #444 !important;
            }
            
            .dark-dropdown .Select-placeholder,
            .dark-dropdown .Select-value-label {
                color: #E0E0E0 !important;
            }
            
            .dark-dropdown .Select-menu-outer {
                background-color: #2D2D2D !important;
                border-color: #444 !important;
            }
            
            .dark-dropdown .Select-option {
                background-color: #2D2D2D !important;
                color: #E0E0E0 !important;
            }
            
            .dark-dropdown .Select-option:hover,
            .dark-dropdown .Select-option.is-focused {
                background-color: #3D3D3D !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)