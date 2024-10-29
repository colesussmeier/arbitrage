import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_arbitrage():
    df = pd.read_csv('arbitrage_data.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    fig = make_subplots(
        rows=3, 
        cols=1,
        subplot_titles=(
            'Arbitrage Opportunities Over Time', 
            'No Combinations Over Time',
            'Yes Combinations Over Time'
        ),
        vertical_spacing=0.1
    )

    # First subplot: Arbitrage opportunities
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['arbitrage_no_spread_percent_return'],
            name='Trump No + Kamala No',
            line=dict(color='green', width=2),
            legendgroup="1",
            legendgrouptitle=dict(
                text="&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Arbitrage Returns"
            ),
            showlegend=True
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['arbitrage_yes_no_spread_percent_return'],
            name='Kamala Yes + Kamala No',
            line=dict(color='blue', width=2),
            legendgroup="1",
            showlegend=True
        ),
        row=1, col=1
    )

    # Second subplot: No combinations
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['polymarket_trump_no'],
            name='Trump No (Poly)',
            line=dict(dash='solid', color='red'),
            legendgroup="2",
            legendgrouptitle=dict(
                text="&nbsp;&nbsp;&nbsp;&nbsp;No Probabilities",
            ),
            showlegend=True
        ),
        row=2, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['kalshi_kamala_no'],
            name='Kamala No (Kalshi)',
            line=dict(dash='solid', color='orange'),
            legendgroup="2",
            showlegend=True
        ),
        row=2, col=1
    )

    # Third subplot: Yes combinations
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['polymarket_kamala_yes'],
            name='Kamala Yes (Poly)',
            line=dict(dash='solid', color='purple'),
            legendgroup="3",
            legendgrouptitle=dict(
                text="&nbsp;&nbsp;&nbsp;&nbsp;Yes Probabilities",
            ),
            showlegend=True
        ),
        row=3, col=1
    )

    # Add the missing Trump Yes trace
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['kalshi_trump_yes'],
            name='Trump Yes (Kalshi)',
            line=dict(dash='solid', color='magenta'),
            legendgroup="3",
            showlegend=True
        ),
        row=3, col=1
    )

    fig.update_layout(
        height=1200,
        showlegend=True,
        hovermode='x unified',
        plot_bgcolor='rgba(240, 240, 240, 0.5)',
        paper_bgcolor='white',
        legend=dict(
            tracegroupgap=315
        )
    )

    fig.update_yaxes(title_text='Percentage Return', row=1, col=1, gridcolor='white')
    fig.update_yaxes(title_text='No Probabilities', row=2, col=1, gridcolor='white')
    fig.update_yaxes(title_text='Yes Probabilities', row=3, col=1, gridcolor='white')
    
    fig.update_xaxes(title_text='Time', row=3, col=1, gridcolor='white')

    for i in range(1, 4):
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)',
            row=i,
            col=1
        )
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)',
            row=i,
            col=1
        )

    fig.write_html('arbitrage_plot.html')

if __name__ == "__main__":
    plot_arbitrage()
