import pandas as pd
from io import StringIO

def load_dataframe_from_store(stored_data):
    """Convert stored JSON data back to DataFrame"""
    if not stored_data:
        return None
    return pd.read_json(StringIO(stored_data), orient='split')

def create_empty_figure():
    """Create empty figure when no data available"""
    import plotly.graph_objects as go
    return {
        'data': [],
        'layout': go.Layout(
            title='Select cryptocurrencies to display',
            template='plotly_dark',
            paper_bgcolor='#1E1E1E',
            plot_bgcolor='#2D2D2D'
        )
    }