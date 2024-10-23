import streamlit as st
import pybaseball as pb
import plotly.graph_objects as go
import warnings

# Suppress FutureWarnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# Fetch data for all pitches thrown in 2024
@st.cache_data  # Cache data so it doesn't reload every time
def fetch_pitch_data():
    return pb.statcast(start_dt="2024-03-20", end_dt="2024-09-19")

data = fetch_pitch_data()

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

# Streamlit app
def plot_release_points(pitcher_name):
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

    # Display the 3D plot in Streamlit
    st.plotly_chart(fig)

# Streamlit layout
st.title("Pitcher Release Points Analysis")

# Dropdown to select the pitcher
pitcher_name = st.selectbox("Select a pitcher", player_grouped['player_name'].unique())

# Plot the selected pitcher's release points
if pitcher_name:
    plot_release_points(pitcher_name)


