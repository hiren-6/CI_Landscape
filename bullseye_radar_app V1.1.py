import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
import plotly.express as px

# --- Helper functions ---
def calculate_segment_positions(data, segment_column, max_segments=8):
    labels = data[segment_column].unique().tolist()[:max_segments]
    angles = np.linspace(0, 2 * np.pi, len(labels) + 1)
    seg_info = {}
    for i, lbl in enumerate(labels):
        seg_info[lbl] = {
            'base_angle': angles[i],
            'end_angle': angles[i + 1]
        }
    # assign each row the base angle of its segment
    positions = [seg_info[row[segment_column]]['base_angle'] for _, row in data.iterrows()]
    return positions, seg_info


def phase_to_radius(phase):
    mapping = {'Phase 1': 25, 'Phase 2': 50, 'Phase 3': 75, 'Marketed': 100}
    return mapping.get(phase, 0)


def create_bullseye_chart(data, segment_column='Category', max_segments=8):
    # Single-polar subplot for the bullseye
    fig = make_subplots(rows=1, cols=1, specs=[[{'type': 'polar'}]])

    # Draw annular rings via Barpolar
    radii = [25, 50, 75, 100]
    colors = ['rgba(230,230,230,0.3)', 'rgba(200,200,200,0.3)',
              'rgba(170,170,170,0.3)', 'rgba(140,140,140,0.3)']
    base = 0
    for r, c in zip(radii, colors):
        fig.add_trace(go.Barpolar(
            r=[r - base], base=[base], theta=[0], width=[360],
            marker_color=c, marker_line_color='lightgray', marker_line_width=1,
            hoverinfo='skip', showlegend=False
        ))
        base = r

    # Phase labels around bottom
    phase_labels = ['Phase 1', 'Phase 2', 'Phase 3', 'Marketed']
    for r, lbl in zip(radii, phase_labels):
        fig.add_trace(go.Scatterpolar(
            r=[r + 8], theta=[270], mode='text', text=[lbl],
            textfont=dict(size=10, color='gray'), hoverinfo='skip', showlegend=False
        ))

    # Segment dividers and labels
    angles, seg_info = calculate_segment_positions(data, segment_column, max_segments)
    for seg, info in seg_info.items():
        base_ang = np.degrees(info['base_angle'])
        end_ang = np.degrees(info['end_angle'])
        # Divider
        fig.add_trace(go.Scatterpolar(
            r=[0, radii[-1]], theta=[base_ang, base_ang],
            mode='lines', line=dict(color='gray', width=2),
            hoverinfo='skip', showlegend=False
        ))
        # Segment title
        mid = (info['base_angle'] + info['end_angle']) / 2
        fig.add_trace(go.Scatterpolar(
            r=[radii[-1] + 10], theta=[np.degrees(mid)],
            mode='text', text=[f"<b>{seg}</b>"],
            textfont=dict(size=12, color='black'),
            hoverinfo='skip', showlegend=False
        ))

    # Plot each asset
    for idx, row in data.iterrows():
        ang = np.degrees(angles[idx])
        rad = phase_to_radius(row['Phase_Status'])
        colr = st.session_state.moa_colors.get(row['MOA'], '#888')
        # Marker
        fig.add_trace(go.Scatterpolar(
            r=[rad], theta=[ang], mode='markers',
            marker=dict(size=10, color=colr, line=dict(width=1, color='gray')),
            hoverinfo='text', hovertext=row['Asset'], showlegend=False
        ))
        # Callout line and label
        fig.add_trace(go.Scatterpolar(
            r=[rad, radii[-1] + 30], theta=[ang, ang],
            mode='lines', line=dict(color=colr, width=1),
            hoverinfo='skip', showlegend=False
        ))
        fig.add_trace(go.Scatterpolar(
            r=[radii[-1] + 30], theta=[ang], mode='text', text=[row['Asset']],
            textposition='middle right', textfont=dict(size=10, color=colr),
            hoverinfo='skip', showlegend=False
        ))

    # Layout polish
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=False, range=[0, radii[-1] + 40]),
            angularaxis=dict(visible=False)
        ),
        margin=dict(l=20, r=20, t=20, b=20),
        height=600,
        showlegend=False
    )
    return fig


# --- Streamlit App ---
st.set_page_config(layout='wide')
st.title('Bullseye Pipeline Visualization')

# Data ingestion
uploaded = st.file_uploader('Upload CSV with columns Asset, MOA, Category, Phase_Status', type='csv')
if not uploaded:
    st.info('Please upload a CSV file to proceed.')
    st.stop()
data = pd.read_csv(uploaded)

# Initialize MOA colors
if 'moa_colors' not in st.session_state:
    unique_moas = data['MOA'].unique().tolist()
    palette = px.colors.qualitative.Plotly
    st.session_state.moa_colors = {moa: palette[i % len(palette)]
                                   for i, moa in enumerate(unique_moas)}

# Layout: chart + right pane
col1, col2 = st.columns([3, 1])
with col1:
    fig = create_bullseye_chart(data)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # MOA legend
    st.subheader('Mechanisms of Action')
    for moa, color in st.session_state.moa_colors.items():
        st.markdown(
            f"<span style='display:inline-block;width:14px;height:14px;"
        "background-color:{color};margin-right:6px;'></span> {moa}",
            unsafe_allow_html=True
        )

    # Trial Status
    st.subheader('Trial Status')
    st.markdown('🚀 **Advanced to next Phase of development**')
    st.markdown('❓ **Status Unknown**')

    # Status table
    status_df = data[['Asset', 'Phase_Status']].rename(columns={
        'Phase_Status': 'Current Phase'
    })
    st.dataframe(status_df, use_container_width=True)
