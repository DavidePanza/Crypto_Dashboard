from dash import Dash, html, dcc, Input, Output, State
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime, timedelta
import boto3
from boto3.dynamodb.conditions import Key
import pandas as pd
import plotly.express as px
import os
import time
from dotenv import load_dotenv

load_dotenv()

# AWS configuration 
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_REGION = 'us-east-1'

dynamodb = boto3.resource('dynamodb')
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

CRYPTO_COLORS = {
    'bitcoin': '#F7931A',        # Orange
    'ethereum': '#627EEA',       # Blue/Purple
    'tether': '#26A17B',         # Green
    'binancecoin': '#F3BA2F',    # Yellow/Gold
    'solana': '#14F195',         # Bright Green/Cyan
    'ripple': '#23292F',         # Dark Gray/Black
    'cardano': '#0033AD',        # Blue
    'dogecoin': '#C2A633',       # Gold/Yellow
    'tron': '#FF060A',           # Red
    'usd-coin': '#2775CA',       # Blue
}

app.layout = html.Div([
    html.H1('Crypto Dashboard', style={'color': '#FFF', 'textAlign': 'center'}),
    
    # Hidden component to store data
    dcc.Store(id='crypto-data-store'),
    
    html.Div([
        html.Label('Select Cryptos to Display:', style={'color': '#FFF', 'fontWeight': 'bold'}),
        dcc.Checklist(
            id='crypto-selector',
            options=[{'label': 'Tether', 'value': 'tether'},
                    {'label': 'Ethereum', 'value': 'ethereum'},
                    {'label': 'Binancecoin', 'value': 'binancecoin'},
                    {'label': 'Cardano', 'value': 'cardano'},
                    {'label': 'Dogecoin', 'value': 'dogecoin'},
                    {'label': 'Solana', 'value': 'solana'},
                    {'label': 'Tron', 'value': 'tron'},
                    {'label': 'Ripple', 'value': 'ripple'},
                    {'label': 'Usd-coin', 'value': 'usd-coin'},
                    {'label': 'Bitcoin', 'value': 'bitcoin'}],
            value=['bitcoin'],
            inline=False,
            style={'color': '#FFF', 'padding': '10px'}
        ),
    ], style={'padding': '20px', 'backgroundColor': '#2D2D2D', 'margin': '20px', 'borderRadius': '10px'}),
    
    html.Div([
        html.Label('Start Time:', style={'color': '#FFF', 'marginRight': '10px'}),
        dcc.Input(
            id='start_time',
            value='2025-10-13T16:00', 
            type='datetime-local',
            style={'padding': '8px'}
        ),
        
        html.Label('End Time:', style={'color': '#FFF', 'marginRight': '10px', 'marginLeft': '20px'}),
        dcc.Input(
            id='end_time',
            value='2025-10-14T16:00', 
            type='datetime-local',
            style={'padding': '8px'}
        ),
    ], style={'padding': '20px', 'backgroundColor': '#2D2D2D', 'margin': '20px', 'borderRadius': '10px'}),
    
    html.Div(id='query-status', style={'color': '#FFD700', 'padding': '10px', 'textAlign': 'center'}),
    
    dcc.Graph(id='chart')
], style={'backgroundColor': '#121212', 'minHeight': '100vh'})

# CALLBACK 1: Query database and store data (only triggers on time change)
@app.callback(
    [Output('crypto-data-store', 'data'),
     Output('query-status', 'children')],
    [Input('start_time', 'value'),
     Input('end_time', 'value')]
)
def query_database(start_time, end_time):
    """This runs only when time changes - queries database"""
    print(f"QUERYING DATABASE: {start_time} to {end_time}")
    
    # Query ALL cryptos from database
    df_all = get_data(table, start_time, end_time)
    
    # Convert to JSON for storage
    data_json = df_all.to_json(date_format='iso', orient='split')
    
    status = f"Loaded {len(df_all)} records from database"
    
    return data_json, status

# CALLBACK 2: Update chart display (triggers on crypto selection OR when data changes)
@app.callback(
    Output('chart', 'figure'),
    [Input('crypto-data-store', 'data'),    # Triggers when data is loaded
     Input('crypto-selector', 'value')]     # Triggers when selection changes
)
def update_chart(stored_data, selected_cryptos):
    """This runs when crypto selection changes - uses stored data, NO new query"""
    
    if not stored_data:
        return {
            'data': [],
            'layout': go.Layout(
                title='Waiting for data...',
                template='plotly_dark',
                paper_bgcolor='#1E1E1E',
                plot_bgcolor='#2D2D2D'
            )
        }
    
    print(f"UPDATING CHART (no query): Showing {selected_cryptos}")
    
    # Load data from storage (no database query!)
    df = pd.read_json(stored_data, orient='split')
    
    # Filter by selected cryptos
    traces = []
    for crypto in selected_cryptos:
        if len(df) == 0:
            continue
        
        traces.append(go.Scatter(
            x=df['timestamp'],
            y=df[crypto],
            mode='lines+markers',
            name=crypto,
            line=dict(color=CRYPTO_COLORS.get(crypto, '#FFFFFF'), width=3),
            marker=dict(size=4)
        ))

    return {
        'data': traces,
        'layout': go.Layout(
            title=f'Crypto Prices - Displaying {len(selected_cryptos)} cryptos',
            template='plotly_dark',
            paper_bgcolor='#1E1E1E',
            plot_bgcolor='#2D2D2D',
            xaxis={'title': 'Time'},
            yaxis={'title': 'Price (USD)'},
            hovermode='x unified'
        )
    }

if __name__ == '__main__':
    app.run(debug=True)

# def run_dash():
#     app.run(debug=False, port=8050, use_reloader=False)