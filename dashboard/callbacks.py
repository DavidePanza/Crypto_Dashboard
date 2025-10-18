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
    

def add_news_overlays_single_y(fig, df, df_news, selected_cryptos):
    """Add news event images and markers for single Y-axis charts"""
    if df_news is None or df_news.empty:
        return
    
    # Calculate y position for images (above the chart)
    y_min = float(df[selected_cryptos].min().min())
    y_max = float(df[selected_cryptos].max().max())
    y_range = y_max - y_min
    image_y = y_max + y_range * 0.15
    
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
    
    # Calculate image width (as fraction of time range)
    time_range = (df_crypto['timestamp'].max() - df_crypto['timestamp'].min()).total_seconds() * 1000
    image_width = time_range * 0.015  # 1.5% of time range
    
    # Add each news image as overlay
    for i, row in df_news.iterrows():
        date = pd.to_datetime(row['Date'])
        
        # Make date timezone-aware
        if date.tz is None:
            date = date.tz_localize('UTC')
        
        # Get the person's image
        person_key = row['person'].lower()
        image_source = IMAGE_PATHS.get(person_key, IMAGE_PATHS.get('trump'))
        
        if image_source is None:
            continue
        
        # Add image
        fig.add_layout_image(
            dict(
                source=image_source,
                x=date,
                y=image_y,
                xref="x",
                yref="y",
                sizex=image_width,
                sizey=y_range * 0.08,
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
                y=[image_y - y_range * 0.04, crypto_price],
                mode='lines',
                line=dict(color='rgba(255,255,255,0.5)', width=1, dash='dash'),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            # Add point at intersection
            fig.add_trace(go.Scatter(
                x=[date],
                y=[crypto_price],
                mode='markers',
                marker=dict(
                    size=10,
                    color=CRYPTO_COLORS.get(crypto, '#FFFFFF'),
                    line=dict(color='white', width=2)
                ),
                showlegend=False,
                hovertext=f"{crypto.capitalize()}: ${crypto_price:.2f}<br>{row.get('title', row.get('Title', 'News Event'))}",
                hoverinfo='text'
            ))
    
    # Add invisible scatter for hover on images
    news_dates = pd.to_datetime(df_news['Date'])
    if news_dates.dt.tz is None:
        news_dates = news_dates.dt.tz_localize('UTC')
    
    fig.add_trace(go.Scatter(
        x=news_dates,
        y=[image_y] * len(df_news),
        mode='markers',
        marker=dict(size=60, opacity=0),
        hovertext=df_news.get('title', df_news.get('Title', 'News Event')),
        hoverinfo='text',
        name='News Events',
        showlegend=False
    ))


def add_news_overlays_multi_y(fig, df, df_news, selected_cryptos):
    """Add news event images and markers for multi Y-axis charts"""
    if df_news is None or df_news.empty:
        return
    
    # Calculate individual y ranges for each crypto
    crypto_ranges = {}
    for crypto in selected_cryptos:
        if crypto in df.columns:
            crypto_ranges[crypto] = {
                'min': float(df[crypto].min()),
                'max': float(df[crypto].max()),
                'range': float(df[crypto].max() - df[crypto].min())
            }
    
    # Use the first crypto's range for image positioning
    first_crypto = selected_cryptos[0]
    if first_crypto not in crypto_ranges:
        return
    
    y_max = crypto_ranges[first_crypto]['max']
    y_range = crypto_ranges[first_crypto]['range']
    image_y = y_max + y_range * 0.15
    
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
    image_width = time_range * 0.015
    
    # Add each news image as overlay
    for i, row in df_news.iterrows():
        date = pd.to_datetime(row['Date'])
        
        if date.tz is None:
            date = date.tz_localize('UTC')
        
        person_key = row['person'].lower()
        image_source = IMAGE_PATHS.get(person_key, IMAGE_PATHS.get('trump'))
        
        if image_source is None:
            continue
        
        # Add image (positioned relative to first Y-axis)
        fig.add_layout_image(
            dict(
                source=image_source,
                x=date,
                y=image_y,
                xref="x",
                yref="y",
                sizex=image_width,
                sizey=y_range * 0.08,
                xanchor="center",
                yanchor="bottom",  # Changed to bottom anchor
                layer="above"
            )
        )
        
        # Find closest timestamp
        closest_idx = (df_crypto['timestamp'] - date).abs().idxmin()
        
        # Collect all y-values for this date to draw a single line
        line_x = [date]
        line_y = [image_y]
        
        # Add markers for each crypto on its respective Y-axis
        for j, crypto in enumerate(selected_cryptos):
            if crypto not in df.columns or crypto not in crypto_ranges:
                continue
            
            crypto_price = df.loc[closest_idx, crypto]
            yaxis_ref = 'y' if j == 0 else f'y{j+1}'
            
            # Add point at intersection
            fig.add_trace(go.Scatter(
                x=[date],
                y=[crypto_price],
                mode='markers',
                marker=dict(
                    size=10,
                    color=CRYPTO_COLORS.get(crypto, '#FFFFFF'),
                    line=dict(color='white', width=2)
                ),
                showlegend=False,
                hovertext=f"{crypto.capitalize()}: ${crypto_price:.2f}<br>{row.get('title', row.get('Title', 'News Event'))}",
                hoverinfo='text',
                yaxis=yaxis_ref
            ))
            
            # For the first crypto, add a single dashed line from image to price
            if j == 0:
                line_x.append(date)
                line_y.append(crypto_price)
        
        # Add single dashed line (only for first crypto to avoid overlaps)
        if len(line_y) > 1:
            fig.add_trace(go.Scatter(
                x=line_x,
                y=line_y,
                mode='lines',
                line=dict(color='rgba(255,255,255,0.5)', width=1, dash='dash'),
                showlegend=False,
                hoverinfo='skip',
                yaxis='y'
            ))
    
    # Add invisible scatter for hover on images
    news_dates = pd.to_datetime(df_news['Date'])
    if news_dates.dt.tz is None:
        news_dates = news_dates.dt.tz_localize('UTC')
    
    fig.add_trace(go.Scatter(
        x=news_dates,
        y=[image_y] * len(df_news),
        mode='markers',
        marker=dict(size=60, opacity=0),
        hovertext=df_news.get('title', df_news.get('Title', 'News Event')),
        hoverinfo='text',
        name='News Events',
        showlegend=False,
        yaxis='y'
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
    
    # Add news overlays AFTER layout is set
    if df_news is not None and not df_news.empty:
        add_news_overlays_single_y(fig, df, df_news, selected_cryptos)
    
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
    
    # Add news overlays AFTER layout is set
    if df_news is not None and not df_news.empty:
        add_news_overlays_multi_y(fig, df, df_news, selected_cryptos)
    
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