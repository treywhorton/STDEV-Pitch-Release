import streamlit as st
import pybaseball as pb
import matplotlib.pyplot as plt
import warnings

# Suppress FutureWarnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# Fetch data for all pitches thrown in 2024
@st.cache_data  # Caches the data to avoid refetching on every page load
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

# Scaling factor
scaling_factor = 1.2

# Streamlit app
def plot_release_points(pitcher_name):
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')

    # Filter data for the specific pitcher
    pitcher_pitch_data = pitch_grouped[pitch_grouped['player_name'] == pitcher_name]
    pitcher_overall_data = player_grouped[player_grouped['player_name'] == pitcher_name].iloc[0]

    # Determine if the pitcher is left or right-handed based on release_pos_x_mean
    handedness = 'Left-Handed' if pitcher_overall_data['release_pos_x_mean_all'] > 0 else 'Right-Handed'

    # Plot average release point for each pitch (mean and std dev for each pitch type)
    for idx, row in pitcher_pitch_data.iterrows():
        pitch_name = row['pitch_name']
        color = color_map.get(pitch_name, 'gray')

        ax.scatter(row['release_pos_x_mean'] * scaling_factor,
                   row['release_pos_y_mean'] * scaling_factor,
                   row['release_pos_z_mean'] * scaling_factor,
                   color=color, s=50, label=pitch_name if pitch_name not in ax.get_legend_handles_labels()[1] else "")

        # Plot standard deviation error bars
        ax.plot([row['release_pos_x_mean'] * scaling_factor - row['release_pos_x_std'] * scaling_factor,
                 row['release_pos_x_mean'] * scaling_factor + row['release_pos_x_std'] * scaling_factor],
                [row['release_pos_y_mean'] * scaling_factor, row['release_pos_y_mean'] * scaling_factor],
                [row['release_pos_z_mean'] * scaling_factor, row['release_pos_z_mean'] * scaling_factor],
                color=color, linestyle='--')

    # Overall average release point for the pitcher (green for all pitches combined)
    ax.scatter(pitcher_overall_data['release_pos_x_mean_all'] * scaling_factor,
               pitcher_overall_data['release_pos_y_mean_all'] * scaling_factor,
               pitcher_overall_data['release_pos_z_mean_all'] * scaling_factor,
               color='green', label='Overall Mean release point', s=100)

    # Set plot title and axis labels
    ax.set_title(f'Release Points for {pitcher_name} ({handedness})', fontsize=18)

    # Add legend
    ax.legend()

    # Display the plot in Streamlit
    st.pyplot(fig)

# Streamlit layout
st.title("Pitcher Release Points Analysis")

# Dropdown to select the pitcher
pitcher_name = st.selectbox("Select a pitcher", player_grouped['player_name'].unique())

# Plot the selected pitcher's release points
if pitcher_name:
    plot_release_points(pitcher_name)


