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
                                    Key('timestamp').between(
                                        time1,
                                        time2
                                        )
                                    )
        df = pd.DataFrame(response['Items']).drop(columns=['ttl', 'PK'])

        return df
    
    except Exception as e:
        raise Exception(f'qQuery failed: {e}')


app = Dash(__name__)

app.layout = html.Div([
    # Header with gradient background
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
        # Store component
        dcc.Store(id='news-data-store'),
        dcc.Store(id='crypto-data-store'),
        
        # Left panel - Controls
        html.Div([
            # Time range
            html.Div([
                html.Div([
                    html.Span('📅', style={'fontSize': '26px', 'marginRight': '10px'}),
                    html.Span('Time Range', style={'fontSize': '22px', 'fontWeight': '600'})
                ], style={'marginBottom': '20px', 'display': 'flex', 'alignItems': 'center'}),
                
                html.Label('Date Range:', style={'color': '#B0B0B0', 'fontSize': '15px', 'marginBottom': '8px', 'display': 'block'}),
                
                html.Div([
                    dcc.DatePickerRange(
                        id='date-picker-range',
                        min_date_allowed=date(2025, 10, 13),
                        max_date_allowed=(datetime.now() - timedelta(hours=1)).date(),
                        start_date=(datetime.now() - timedelta(days=1)).date(),
                        end_date=datetime.now().date(),
                        display_format='YYYY-MM-DD',
                    ),
                ], style={'transform': 'scale(0.90)', 'transformOrigin': 'left top', 'marginBottom': '10px'}),
                
            ], style={
                'padding': '20px',
                'backgroundColor': '#1E1E1E',
                'borderRadius': '12px',
                'boxShadow': '0 2px 8px rgba(0,0,0,0.3)',
                'marginBottom': '20px',
                'border': '1px solid #333'
            }),

            # Crypto selector
            html.Div([
                html.Div([
                    html.Span('₿', style={'fontSize': '26px', 'marginRight': '10px'}),
                    html.Span('Cryptocurrencies', style={'fontSize': '22px', 'fontWeight': '600'})
                ], style={'marginBottom': '15px', 'display': 'flex', 'alignItems': 'center'}),
                
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
            ], style={
                'padding': '20px',
                'backgroundColor': '#1E1E1E',
                'borderRadius': '12px',
                'boxShadow': '0 2px 8px rgba(0,0,0,0.3)',
                'border': '1px solid #333'
            }),

        ], style={'width': '280px', 'marginRight': '30px', 'flexShrink': '0'}),

        # Right panel - Chart
        html.Div([

            # News Section
            html.Div([
                # Header
                html.Div([
                    html.Span('📰', style={'fontSize': '26px', 'marginRight': '10px'}),
                    html.Span('News', style={'fontSize': '22px', 'fontWeight': '600'})
                ], style={'marginBottom': '20px', 'display': 'flex', 'alignItems': 'center'}),
                
                # Time Range Section
                html.Div([
                    html.Label('Time Range:', style={'color': '#B0B0B0', 'fontSize': '15px', 'marginBottom': '10px', 'display': 'block'}),
                    
                    # Toggle: Use crypto timerange or custom
                    dcc.RadioItems(
                        id='news-timerange-toggle',
                        options=[
                            {'label': ' Use Crypto Time Range', 'value': 'crypto'},
                            {'label': ' Custom Time Range', 'value': 'custom'}
                        ],
                        value='crypto',
                        inline=True,
                        style={'color': '#E0E0E0', 'fontSize': '14px', 'marginBottom': '10px'},
                        labelStyle={'marginRight': '20px', 'cursor': 'pointer'}
                    ),
                    
                    # Custom date picker (shown only when custom is selected)
                    html.Div([
                        dcc.DatePickerRange(
                            id='news-date-range',
                            start_date='2025-10-13',
                            end_date='2025-10-16',
                            display_format='YYYY-MM-DD',
                            style={'marginTop': '10px'},
                            className='dark-datepicker'
                        )
                    ], id='news-date-picker-container'),
                    
                ], style={'marginBottom': '15px'}),

                # Person selector
                html.Div([
                    html.Label('Choose People:', style={'color': '#B0B0B0', 'fontSize': '15px', 'marginRight': '15px', 'minWidth': '150px'}),
                    dcc.Dropdown(
                        id='news-personality-preset',
                        options=[
                            {'label': 'Donald Trump', 'value': 'Trump'},
                            {'label': 'Elon Musk', 'value': 'Musk'},
                            {'label': 'Vladimir Putin', 'value': 'Putin'},
                            {'label': 'Christine Lagarde', 'value': 'Lagarde'},
                        ],
                        placeholder='Select personalities...',
                        multi=True,
                        style={'width': '300px', 'marginRight': '15px'},
                        className='dark-dropdown'
                    ),
                    html.Span('or', style={'color': '#B0B0B0', 'fontSize': '14px', 'marginRight': '15px'}),
                    dcc.Input(
                        id='news-personality-custom',
                        type='text',
                        placeholder='To be implemented...', #'Enter names (comma-separated)...',
                        style={
                            'width': '300px',
                            'padding': '8px 12px',
                            'backgroundColor': '#2D2D2D',
                            'border': '1px solid #444',
                            'borderRadius': '4px',
                            'color': '#E0E0E0',
                            'fontSize': '14px'
                        }
                    ),
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '15px'}),

                # Keyword selector
                html.Div([
                    html.Label('Choose Keywords:', style={'color': '#B0B0B0', 'fontSize': '15px', 'marginRight': '15px', 'minWidth': '150px'}),
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
                        placeholder='Enter keywords (comma-separated)...',
                        style={
                            'width': '300px',
                            'padding': '8px 12px',
                            'backgroundColor': '#2D2D2D',
                            'border': '1px solid #444',
                            'borderRadius': '4px',
                            'color': '#E0E0E0',
                            'fontSize': '14px'
                        }
                    ),
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '15px'}),

                # Source selector
                html.Div([
                    html.Label('Choose Sources:', style={'color': '#B0B0B0', 'fontSize': '15px', 'marginRight': '15px', 'minWidth': '150px'}),
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
                        placeholder='Enter sources (comma-separated)...',
                        style={
                            'width': '300px',
                            'padding': '8px 12px',
                            'backgroundColor': '#2D2D2D',
                            'border': '1px solid #444',
                            'borderRadius': '4px',
                            'color': '#E0E0E0',
                            'fontSize': '14px'
                        }
                    ),
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px'}),

                # Search Button
                html.Div([
                    html.Button(
                        'Search News',
                        id='search-news-button',
                        n_clicks=0,
                        style={
                            'padding': '12px 40px',
                            'backgroundColor': '#627EEA',
                            'color': '#FFFFFF',
                            'border': 'none',
                            'borderRadius': '6px',
                            'fontSize': '15px',
                            'fontWeight': '600',
                            'cursor': 'pointer',
                            'transition': 'background-color 0.3s'
                        }
                    )
                ], style={'display': 'flex', 'justifyContent': 'center', 'marginTop': '10px'}),

                html.Div(id='news-status', style={'textAlign': 'center'}),

            ], style={
                'padding': '20px',
                'backgroundColor': '#1E1E1E',
                'borderRadius': '8px',
                'marginBottom': '20px',
                'border': '1px solid #333'
            }),

            # Display mode selector
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
            
            # Chart container
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



# CALLBACK 1: Query database and store data (only triggers on time change)
@app.callback(
    Output('crypto-data-store', 'data'),  
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')]
)
def query_database(start_date, end_date):
    """This runs only when time changes - queries database"""
    
    start_time = f"{start_date}T12:00:00"
    end_time = f"{end_date}T12:59:59"
    
    df_all = get_data(table, start_time, end_time)
    data_json = df_all.to_json(date_format='iso', orient='split')
    
    return data_json

# CALLBACK 2: Update chart display (triggers on crypto selection OR when data changes)
@app.callback(
    Output('chart', 'figure'),
    [Input('crypto-data-store', 'data'),
     Input('crypto-selector', 'value'),
     Input('plot-mode', 'value')]
)
def chart_callback(stored_data, selected_cryptos, plot_mode):
    return update_chart(stored_data, selected_cryptos, plot_mode)



@app.callback(
    [Output('news-data-store', 'data'),
     Output('news-status', 'children')],
    [Input('search-news-button', 'n_clicks')],
    [State('news-personality-preset', 'value'),
     State('news-personality-custom', 'value'),
     State('keyword-preset', 'value'),
     State('keyword-custom', 'value'),
     State('source-preset', 'value'),
     State('source-custom', 'value')]
)
def search_news(n_clicks, preset_people, custom_people, preset_keywords, custom_keywords, 
                preset_sources, custom_sources):
    
    # Don't run on initial load
    if not n_clicks:
        return None, ""
    
    try:
        # Combine preset and custom inputs - SIMPLIFIED
        people = []
        
        # Add preset selections (multi-select returns list or None)
        if preset_people:  # Will be a list like ['Trump', 'Musk'] or None
            people.extend(preset_people)
        
        # Add custom text
        if custom_people and custom_people.strip():
            custom_list = [name.strip() for name in custom_people.split(',') if name.strip()]
            people.extend(custom_list)
        
        # Same for keywords
        keywords = []
        if preset_keywords:
            keywords.extend(preset_keywords)
        
        if custom_keywords and custom_keywords.strip():
            custom_list = [kw.strip() for kw in custom_keywords.split(',') if kw.strip()]
            keywords.extend(custom_list)
        
        # Same for sources
        sources = []
        if preset_sources:
            sources.extend(preset_sources)
        
        if custom_sources and custom_sources.strip():
            custom_list = [src.strip() for src in custom_sources.split(',') if src.strip()]
            sources.extend(custom_list)
        
        # Debug print - IMPORTANT
        print(f"\n{'='*60}")
        print(f"Raw preset_people: {preset_people} (type: {type(preset_people)})")
        print(f"Raw custom_people: {custom_people} (type: {type(custom_people)})")
        print(f"Final People: {people}")
        print(f"Final Keywords: {keywords}")
        print(f"Final Sources: {sources}")
        print(f"{'='*60}\n")
        
        # Validation
        if not people:
            return None, html.Div("⚠️ Please select at least one person", 
                                  style={'color': '#FF6B6B', 'marginTop': '10px'})
        
        if not keywords:
            keywords = ["bitcoin"]  # Default keyword
        
        if not sources:
            sources = ["wsj.com", "ft.com", "nytimes.com", "bloomberg.com", "coindesk.com"]
        
        # GDELT API setup
        base_url = "https://api.gdeltproject.org/api/v2/doc/doc"
        proximity = 15
        
        all_news = []
        
        # Search for each person SEPARATELY
        for personality in people:
            # Build domain filter with OR
            domain_filters = " OR ".join([f"domainis:{d}" for d in sources])
            
            # Build nearX query: ONE person with MULTIPLE keywords (OR)
            near_queries = ' OR '.join([f'near{proximity}:"{personality} {kw}"' for kw in keywords])
            
            # Combine: only add parentheses if multiple keywords
            if len(keywords) > 1:
                full_query = f"({near_queries}) sourcelang:English ({domain_filters})"
            else:
                full_query = f"{near_queries} sourcelang:English ({domain_filters})"
            
            # Date parameters
            params = {
                "query": full_query,
                "mode": "artlist",
                "format": "csv",
                "startdatetime": "20251013000000",
                "enddatetime": "20251016235959",
                "sort": "datedesc",
                "maxrecords": 250
            }
            
            print(f"\nSearching for: {personality}")
            print(f"Keywords: {keywords}")
            print(f"Query: {full_query}")
            
            # Make request
            response = requests.get(base_url, params=params, timeout=30)
            
            print(f"Response status: {response.status_code}, length: {len(response.text)}")
            
            if response.status_code == 200 and response.text.strip():
                csv_data = StringIO(response.text)
                df_person = pd.read_csv(csv_data)
                
                if not df_person.empty:
                    df_person['person'] = personality
                    all_news.append(df_person)
                    print(f"✓ Found {len(df_person)} articles for {personality}")
                else:
                    print(f"✗ Empty DataFrame for {personality}")
            else:
                print(f"✗ No response for {personality}")
        
        # Combine all results
        if all_news:
            df_news = pd.concat(all_news, ignore_index=True)
            
            # Sort by date
            if 'seendate' in df_news.columns:
                df_news = df_news.sort_values('seendate', ascending=False)
            
            # Store as JSON
            news_json = df_news.to_json(orient='split', date_format='iso')
            
            # Create status message
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
            return None, html.Div("⚠️ No articles found for any person", 
                                  style={'color': '#FFA726', 'marginTop': '10px'})
    
    except Exception as e:
        print(f"Error in news search: {str(e)}")
        import traceback
        traceback.print_exc()
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
            
            /* Dark dropdown styling */
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
            
            .dark-dropdown .Select-arrow-zone {
                color: #E0E0E0 !important;
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
