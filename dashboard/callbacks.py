import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import math
from config import CRYPTO_COLORS
from utils import load_dataframe_from_store, create_empty_figure, img_to_base64

# Load images
IMAGE_PATHS = {
    'trump': img_to_base64('./images/round/trump.png'),
    'musk': img_to_base64('./images/round/elon.png'),
    'putin': img_to_base64('./images/round/putin.png'),
    'lagarde': img_to_base64('./images/round/lagarde.png'),
}

def update_chart(stored_crypto_data, stored_news_data, selected_cryptos, plot_mode):
    """Main chart update callback logic"""
    if not stored_crypto_data or not selected_cryptos:
        return create_empty_figure()
    
    df = load_dataframe_from_store(stored_crypto_data)
    
    # Load news data if available
    df_news = None
    if stored_news_data:
        df_news = load_dataframe_from_store(stored_news_data)
    
    if plot_mode == 'overlaid':
        return create_overlaid_chart(df, selected_cryptos, df_news)
    elif plot_mode == 'multi_y':
        return create_multi_y_chart(df, selected_cryptos, df_news)
    else:  # separated
        return create_separated_charts(df, selected_cryptos)
    

def add_news_overlays(fig, df, df_news, selected_cryptos):
    """Add news event images and markers to the chart"""
    if df_news is None or df_news.empty:
        return
    
    # Calculate y position for images (above the chart)
    y_min = float(df[selected_cryptos].min().min())
    y_max = float(df[selected_cryptos].max().max())
    image_y = y_max + (y_max - y_min) * 0.05
    
    # Ensure timestamp column exists in news data
    if 'seendate' in df_news.columns:
        df_news['Date'] = pd.to_datetime(df_news['seendate'], format='%Y%m%dT%H%M%SZ')
    elif 'Date' not in df_news.columns:
        return
    
    # Make crypto timestamps timezone-aware
    df_crypto = df.copy()
    df_crypto['timestamp'] = pd.to_datetime(df_crypto['timestamp'])
    if df_crypto['timestamp'].dt.tz is None:
        df_crypto['timestamp'] = df_crypto['timestamp'].dt.tz_localize('UTC')
    
    # Calculate image width
    time_range = (df_crypto['timestamp'].max() - df_crypto['timestamp'].min()).total_seconds() * 1000
    image_width = time_range * 0.02  # 2% of time range
    
    # Add each news image as overlay
    for i, row in df_news.iterrows():
        date = pd.to_datetime(row['Date'])
        
        # Make date timezone-aware
        if date.tz is None:
            date = date.tz_localize('UTC')
        
        # Get the person's image
        person_key = row['person'].lower()
        image_source = IMAGE_PATHS.get(person_key, IMAGE_PATHS['trump'])
        
        # Add image
        fig.add_layout_image(
            dict(
                source=image_source,
                x=date,
                y=image_y,
                xref="x",
                yref="y",
                sizex=image_width,
                sizey=(y_max - y_min) * 0.1,
                xanchor="center",
                yanchor="middle",
                layer="above"
            )
        )
        
        # Find closest timestamp in crypto data
        closest_idx = (df_crypto['timestamp'] - date).abs().idxmin()
        
        # Add lines and markers for each selected crypto
        for crypto in selected_cryptos:
            if crypto not in df.columns:
                continue
                
            crypto_price = df.loc[closest_idx, crypto]
            
            # Add dashed line from image to price
            fig.add_trace(go.Scatter(
                x=[date, date],
                y=[image_y, crypto_price],
                mode='lines',
                line=dict(color='white', width=1, dash='dash'),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            # Add point at intersection
            fig.add_trace(go.Scatter(
                x=[date],
                y=[crypto_price],
                mode='markers',
                marker=dict(
                    size=8,
                    color=CRYPTO_COLORS.get(crypto, '#FFFFFF'),
                    line=dict(color='white', width=2)
                ),
                showlegend=False,
                hovertext=f"{crypto}: ${crypto_price:.2f}<br>{row.get('title', 'News Event')}",
                hoverinfo='text'
            ))
    
    # Add invisible scatter for hover on images
    fig.add_trace(go.Scatter(
        x=pd.to_datetime(df_news['Date']).dt.tz_localize('UTC') if pd.to_datetime(df_news['Date']).dt.tz is None else pd.to_datetime(df_news['Date']),
        y=[image_y] * len(df_news),
        mode='markers',
        marker=dict(size=50, opacity=0),
        hovertext=df_news.get('title', df_news.get('Title', 'News Event')),
        hoverinfo='text',
        name='News Events',
        showlegend=False
    ))


def create_overlaid_chart(df, selected_cryptos, df_news=None):
    """Create overlaid chart with single Y axis"""
    fig = go.Figure()
    
    for crypto in selected_cryptos:
        if crypto not in df.columns:
            continue
        
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(df['timestamp']),
            y=df[crypto],
            mode='lines',
            name=crypto.capitalize(),
            line=dict(color=CRYPTO_COLORS.get(crypto, '#FFFFFF'), width=2.5),
            marker=dict(size=5)
        ))
    
    # Add news overlays if available
    if df_news is not None and not df_news.empty:
        add_news_overlays(fig, df, df_news, selected_cryptos)
    
    # Set initial view to last 24 hours
    latest_date = pd.to_datetime(df['timestamp']).max()
    
    fig.update_layout(
        title='Cryptocurrency Prices with News Events',
        template='plotly_dark',
        paper_bgcolor='#1E1E1E',
        plot_bgcolor='#2D2D2D',
        xaxis=dict(
            title='Time',
            rangeslider_visible=True,
            rangeslider_thickness=0.1,
            range=[latest_date - pd.Timedelta(hours=24), latest_date],
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1H", step="hour", stepmode="backward"),
                    dict(count=1, label="1D", step="day", stepmode="backward"),
                    dict(count=3, label="3D", step="day", stepmode="backward"),
                    dict(step="all", label="All")
                ],
                bgcolor="#2D2D2D",
                activecolor="#4D4D4D",
                bordercolor="#FFFFFF",
                borderwidth=1,
                font=dict(color="#FFFFFF")
            )
        ),
        yaxis={'title': 'Price (USD)', 'tickformat': '$,.0f'},
        hovermode='closest',
        height=600
    )
    
    return fig


def create_multi_y_chart(df, selected_cryptos, df_news=None):
    """Create chart with multiple Y axes"""
    fig = go.Figure()
    
    for i, crypto in enumerate(selected_cryptos):
        if crypto not in df.columns:
            continue
        
        yaxis_name = 'y' if i == 0 else f'y{i+1}'
        
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(df['timestamp']),
            y=df[crypto],
            mode='lines',
            name=crypto.capitalize(),
            line=dict(color=CRYPTO_COLORS.get(crypto, '#FFFFFF'), width=2.5),
            marker=dict(size=5),
            yaxis=yaxis_name
        ))
    
    # Add news overlays if available
    if df_news is not None and not df_news.empty:
        add_news_overlays(fig, df, df_news, selected_cryptos)
    
    layout = {
        'template': 'plotly_dark',
        'paper_bgcolor': '#1E1E1E',
        'plot_bgcolor': '#2D2D2D',
        'xaxis': {'title': 'Time'},
        'hovermode': 'closest',
        'height': 600,
        'title': 'Cryptocurrency Prices with News Events'
    }
    
    for i, crypto in enumerate(selected_cryptos):
        if crypto not in df.columns:
            continue
        
        if i == 0:
            layout['yaxis'] = {'tickformat': '$,.0f', 'showticklabels': False}
        else:
            layout[f'yaxis{i+1}'] = {
                'tickformat': '$,.0f',
                'overlaying': 'y',
                'showticklabels': False
            }
    
    fig.update_layout(layout)
    return fig


def create_separated_charts(df, selected_cryptos):
    """Create separated subplots - news overlay not supported in this mode"""
    n_cryptos = len(selected_cryptos)
    n_cols = 2
    n_rows = math.ceil(n_cryptos / n_cols)
    
    plot_height = 250
    gap = 120
    total_height = (plot_height * n_rows) + (gap * (n_rows - 1)) + 150
    v_spacing = gap / total_height if n_rows > 1 else 0.1
    
    fig = make_subplots(
        rows=n_rows,
        cols=n_cols,
        subplot_titles=[crypto.capitalize() for crypto in selected_cryptos],
        vertical_spacing=v_spacing,
        horizontal_spacing=0.1
    )
    
    for i, crypto in enumerate(selected_cryptos):
        if crypto not in df.columns:
            continue
        
        row = (i // n_cols) + 1
        col = (i % n_cols) + 1
        
        fig.add_trace(
            go.Scatter(
                x=pd.to_datetime(df['timestamp']),
                y=df[crypto],
                mode='lines',
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
        height=total_height,
        title='Cryptocurrency Prices (Separated)',
        margin=dict(t=100, b=50, l=50, r=50)
    )
    
    return fig