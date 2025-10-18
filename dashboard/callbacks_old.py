import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
from config import CRYPTO_COLORS
from utils import load_dataframe_from_store, create_empty_figure


def update_chart(stored_data, selected_cryptos, plot_mode):
    """Main chart update callback logic"""
    if not stored_data or not selected_cryptos:
        return create_empty_figure()
    
    df = load_dataframe_from_store(stored_data)
    
    if plot_mode == 'overlaid':
        return create_overlaid_chart(df, selected_cryptos)
    elif plot_mode == 'multi_y':
        return create_multi_y_chart(df, selected_cryptos)
    else:  # separated
        return create_separated_charts(df, selected_cryptos)


def create_overlaid_chart(df, selected_cryptos):
    """Create overlaid chart with single Y axis"""
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


def create_multi_y_chart(df, selected_cryptos):
    """Create chart with multiple Y axes"""
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


def create_separated_charts(df, selected_cryptos):
    """Create separated subplots"""
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
        height=total_height,
        title='Cryptocurrency Prices (Separated)',
        margin=dict(t=100, b=50, l=50, r=50)
    )
    
    return fig