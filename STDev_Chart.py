import streamlit as st
import pandas as pd
import pybaseball as pb
from datetime import datetime, timedelta
import plotly.graph_objects as go

@st.cache_data
def fetch_season_data(start_date, end_date, chunk_size_days=7):
    """
    Fetch season data in chunks to reduce processing load.
    :param start_date: Start date of the season (YYYY-MM-DD)
    :param end_date: End date of the season (YYYY-MM-DD)
    :param chunk_size_days: Number of days per chunk
    :return: Combined DataFrame for the season
    """
    all_data = []  # List to hold chunked data
    current_start = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    chunk_size = timedelta(days=chunk_size_days)

    while current_start <= end_date:
        current_end = min(current_start + chunk_size - timedelta(days=1), end_date)
        st.write(f"Fetching data from {current_start.date()} to {current_end.date()}...")

        try:
            chunk = pb.statcast(start_dt=current_start.strftime("%Y-%m-%d"), end_dt=current_end.strftime("%Y-%m-%d"))
            if not chunk.empty:
                all_data.append(chunk)
        except Exception as e:
            st.warning(f"Failed to fetch data for {current_start.date()} to {current_end.date()}: {e}")

        current_start += chunk_size

    # Combine all chunks into a single DataFrame
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

def plot_release_points(pitcher_name, pitch_grouped, player_grouped, color_map):
    # Create Plotly 3D scatter plot
    fig = go.Figure()

    # Filter data for the specific pitcher
    pitcher_pitch_data = pitch_grouped[pitch_grouped['player_name'] == pitcher_name]
    pitcher_overall_data = player_grouped[player_grouped['player_name'] == pitcher_name].iloc[0]

    # Determine if the pitcher is left or right-handed based on release_pos_x_mean
    handedness = 'Left-Handed' if pitcher_overall_data['release_pos_x_mean_all'] > 0 else 'Right-Handed'

    # Plot average release point for each pitch (mean and std dev for each pitch type)
    for idx, row in pitcher_pitch_data.iterrows():
        pitch_name = row['pitch_name']
        color = color_map.get(pitch_name, 'gray')

        # Plot each pitch type
        fig.add_trace(go.Scatter3d(
            x=[row['release_pos_x_mean']],
            y=[row['release_pos_y_mean']],
            z=[row['release_pos_z_mean']],
            mode='markers',
            marker=dict(size=5, color=color),
            name=pitch_name
        ))

        # Add error bars for standard deviation
        fig.add_trace(go.Scatter3d(
            x=[row['release_pos_x_mean'] - row['release_pos_x_std'], row['release_pos_x_mean'] + row['release_pos_x_std']],
            y=[row['release_pos_y_mean']] * 2,
            z=[row['release_pos_z_mean']] * 2,
            mode='lines',
            line=dict(color=color, width=2),
            showlegend=False
        ))

    # Plot overall average release point for the pitcher
    fig.add_trace(go.Scatter3d(
        x=[pitcher_overall_data['release_pos_x_mean_all']],
        y=[pitcher_overall_data['release_pos_y_mean_all']],
        z=[pitcher_overall_data['release_pos_z_mean_all']],
        mode='markers',
        marker=dict(size=10, color='green'),
        name='Overall Mean'
    ))

    # Set plot title and axis labels
    fig.update_layout(
        title=f"Release Points for {pitcher_name} ({handedness})",
        scene=dict(
            xaxis_title="Release Pos X",
            yaxis_title="Release Pos Y",
            zaxis_title="Release Pos Z"
        )
    )

    st.plotly_chart(fig)

# Streamlit app
st.title("Pitcher Release Points Analysis")

st.write("Analyze release points for pitchers based on Statcast data.")

# Fetch data
with st.spinner("Fetching data... This may take a while."):
    data = fetch_season_data("2024-03-20", "2024-09-19", chunk_size_days=7)

if data.empty:
    st.warning("No data available.")
    st.stop()

# Filter relevant columns for the analysis
pitch_data = data[['player_name', 'pitch_name', 'release_pos_x', 'release_pos_y', 'release_pos_z']].dropna()

# Group by player_name and pitch_name to calculate mean and std dev for each pitch
pitch_grouped = pitch_data.groupby(['player_name', 'pitch_name']).agg({
    'release_pos_x': ['mean', 'std'],
    'release_pos_y': ['mean', 'std'],
    'release_pos_z': ['mean', 'std']
}).reset_index()

# Flatten the MultiIndex columns
pitch_grouped.columns = ['player_name', 'pitch_name', 'release_pos_x_mean', 'release_pos_x_std',
                         'release_pos_y_mean', 'release_pos_y_std', 'release_pos_z_mean', 'release_pos_z_std']

# Fill any NaN standard deviations with 0 (to avoid issues in plotting)
pitch_grouped.fillna(0, inplace=True)

# Calculate the overall average release point and std dev for each pitcher across all pitches
player_grouped = pitch_data.groupby('player_name').agg({
    'release_pos_x': ['mean', 'std'],
    'release_pos_y': ['mean', 'std'],
    'release_pos_z': ['mean', 'std']
}).reset_index()

# Flatten the MultiIndex columns for player level
player_grouped.columns = ['player_name', 'release_pos_x_mean_all', 'release_pos_x_std_all',
                          'release_pos_y_mean_all', 'release_pos_y_std_all',
                          'release_pos_z_mean_all', 'release_pos_z_std_all']

# Fill any NaN standard deviations with 0
player_grouped.fillna(0, inplace=True)

# Define distinct colors for each pitch type
color_map = {
    '4-Seam Fastball': 'red',
    '2-Seam Fastball': 'red',
    'Sinker': 'purple',
    'Cutter': 'orange',
    'Slider': 'yellow',
    'Sweeper': 'yellow',
    'Curveball': 'blue',
    'Knuckle Curve': 'blue',
    'Changeup': 'green',
    'Splitter': 'pink',
    'Knuckleball': 'black',
}

# Dropdown to select the pitcher
pitcher_name = st.selectbox("Select a pitcher", player_grouped['player_name'].unique())

# Show plot
if pitcher_name:
    plot_release_points(pitcher_name, pitch_grouped, player_grouped, color_map)


