from dash import Dash, html, dcc, Input, Output
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime, timedelta, date
from plotly.subplots import make_subplots
import math
import boto3
from boto3.dynamodb.conditions import Key
import pandas as pd
from io import StringIO
import os
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
                    value=['bitcoin', 'ethereum'],
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
def update_chart(stored_data, selected_cryptos, plot_mode):
    if not stored_data or not selected_cryptos:
        return {
            'data': [],
            'layout': go.Layout(
                title='Select cryptocurrencies to display',
                template='plotly_dark',
                paper_bgcolor='#1E1E1E',
                plot_bgcolor='#2D2D2D'
            )
        }
    
    df = pd.read_json(StringIO(stored_data), orient='split')
    
    if plot_mode == 'overlaid':
        # Overlaid - same Y axis
        traces = []
        for crypto in selected_cryptos:
            if crypto not in df.columns:
                continue
            
            traces.append(go.Scatter(
                x=df['timestamp'],
                y=df[crypto],
                mode='lines+markers',
                name=crypto.capitalize(),
                line=dict(color=CRYPTO_COLORS.get(crypto, '#FFFFFF'), width=2.5),
                marker=dict(size=5)
            ))
        
        return {
            'data': traces,
            'layout': go.Layout(
                title='Cryptocurrency Prices',
                template='plotly_dark',
                paper_bgcolor='#1E1E1E',
                plot_bgcolor='#2D2D2D',
                xaxis={'title': 'Time'},
                yaxis={'title': 'Price (USD)', 'tickformat': '$,.0f'},
                hovermode='x unified',
                height=600
            )
        }
    
    elif plot_mode == 'multi_y':
        # Overlaid - multiple Y axes
        fig = go.Figure()
        
        for i, crypto in enumerate(selected_cryptos):
            if crypto not in df.columns:
                continue
            
            yaxis_name = 'y' if i == 0 else f'y{i+1}'
            
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df[crypto],
                mode='lines+markers',
                name=crypto.capitalize(),
                line=dict(color=CRYPTO_COLORS.get(crypto, '#FFFFFF'), width=2.5),
                marker=dict(size=5),
                yaxis=yaxis_name
            ))
        
        # Configure layout with multiple y-axes
        layout = {
            'template': 'plotly_dark',
            'paper_bgcolor': '#1E1E1E',
            'plot_bgcolor': '#2D2D2D',
            'xaxis': {'title': 'Time'},
            'hovermode': 'x unified',
            'height': 600,
            'title': 'Cryptocurrency Prices'
        }
        
        for i, crypto in enumerate(selected_cryptos):
            if crypto not in df.columns:
                continue
            
            if i == 0:
                layout['yaxis'] = {
                    'tickformat': '$,.0f',
                    'showticklabels': False
                }
            else:
                layout[f'yaxis{i+1}'] = {
                    'tickformat': '$,.0f',
                    'overlaying': 'y',
                    'showticklabels': False
                }
        
        fig.update_layout(layout)
        return fig
    
    else:  # separated
        # Separated plots - 2 per row
        n_cryptos = len(selected_cryptos)
        n_cols = 2
        n_rows = math.ceil(n_cryptos / n_cols)
        
        fig = make_subplots(
            rows=n_rows,
            cols=n_cols,
            subplot_titles=[crypto.capitalize() for crypto in selected_cryptos],
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )
        
        for i, crypto in enumerate(selected_cryptos):
            if crypto not in df.columns:
                continue
            
            row = (i // n_cols) + 1
            col = (i % n_cols) + 1
            
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df[crypto],
                    mode='lines+markers',
                    name=crypto.capitalize(),
                    line=dict(color=CRYPTO_COLORS.get(crypto, '#FFFFFF'), width=2.5),
                    marker=dict(size=4),
                    showlegend=False
                ),
                row=row,
                col=col
            )
            
            fig.update_yaxes(title_text='Price (USD)', row=row, col=col, tickformat='$,.0f')
        
        fig.update_xaxes(title_text='Time')
        
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='#1E1E1E',
            plot_bgcolor='#2D2D2D',
            height=350 * n_rows,
            title='Cryptocurrency Prices (Separated)'
        )
        
        return fig


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

# def run_dash():
#     app.run(debug=False, port=8050, use_reloader=False)

