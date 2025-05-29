import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math
import io

# --- App Config ---
st.set_page_config(
    page_title="Bulls Eye Radar Chart",
    page_icon="🎯",
    layout="wide"
)

# --- Session State Initialization ---
if 'page_state' not in st.session_state:
    st.session_state.page_state = 'landing'

if 'assets_data' not in st.session_state:
    st.session_state.assets_data = pd.DataFrame({
        'Asset': ['DPI-387', 'Cariprazine', 'Lumateperone', 'ILT1011'],
        'Company': ['Defender Pharma', 'Abbvie', 'Xyz', 'Hôpitaux de Paris/ Iltoo Pharma'],
        'Phase_Status': ['Phase 1', 'Phase 3', 'Phase 3', 'Phase 2'],
        'MOA': ['Pan muscarinic antagonist', 'D2 Antagonist', 'Dopamine/Serotonin Modulator', 'Interleukin 2'],
        'Category': ['Treatment Sensitive Category', 'Treatment Resistant Category', 'Treatment Resistant Category', 'Treatment Resistant Category']
    })

if 'moa_colors' not in st.session_state:
    st.session_state.moa_colors = {
        'Pan muscarinic antagonist': '#264ec6',
        'Selective D3; D2/D3 Modulator': '#e048a7',
        'Psychedelic': '#ee4345',
        'D2 Antagonist': '#9747b6',
        'P2X7 Functional Antagonist': '#a0a0a0',
        'Interleukin 2': '#ffa800',
        'NMDA Antagonist': '#0c98f5',
        'Kappa Receptor Antagonist': '#0c9488',
        'Dopamine/Serotonin Modulator': '#36ab54',
        'Cannabinoid': '#89c242',
        'BDNF': '#00c2d6',
        'TRB selective agonist': '#3e3e3e'
    }

# --- Utilities ---
def phase_to_radius(phase):
    mapping = {
        'Phase 1': 25,
        'Phase 2': 50,
        'Phase 3': 75,
        'Marketed': 100
    }
    return mapping.get(phase, 0)

def calculate_segment_positions(data, segment_column):
    # Get unique segments
    segments = data[segment_column].unique()
    num_segments = len(segments)
    segment_angle = 2 * np.pi / num_segments
    angles = []
    segment_positions = {}

    # Group data by segment
    for i, segment in enumerate(segments):
        segment_data = data[data[segment_column] == segment]
        base_angle = i * segment_angle
        # Place points within segment
        assets_in_segment = len(segment_data)
        if assets_in_segment == 1:
            positions = [base_angle + segment_angle / 2]
        else:
            padding = segment_angle * 0.15 if num_segments == 2 else segment_angle * 0.08
            available_angle = segment_angle - 2 * padding
            positions = [base_angle + padding + j * available_angle / (assets_in_segment - 1)
                         for j in range(assets_in_segment)]
        segment_positions[segment] = {
            'base_angle': base_angle,
            'end_angle': base_angle + segment_angle,
            'positions': positions
        }

    # Assign angles to each asset
    for _, row in data.iterrows():
        segment = row[segment_column]
        segment_data = data[data[segment_column] == segment]
        asset_idx = list(segment_data.index).index(row.name)
        angles.append(segment_positions[segment]['positions'][asset_idx])

    return np.array(angles), segment_positions

def create_moa_legend():
    moa_data = []
    for moa, color in st.session_state.moa_colors.items():
        count = len(st.session_state.assets_data[st.session_state.assets_data['MOA'] == moa]) if 'MOA' in st.session_state.assets_data.columns else 0
        if count > 0:
            moa_data.append({'MOA': moa, 'Color': color, 'Count': count})
    return pd.DataFrame(moa_data)

def get_trial_status_legend():
    # Returns a list of dictionaries for trial status legend (icon, description)
    return [
        {
            "icon": "🟢", # Replace with custom SVG or emoji if needed
            "label": "Advanced to next Phase of development"
        },
        {
            "icon": "❓",
            "label": "Status Unknown"
        }
    ]

def get_category_labels(segment_positions):
    return list(segment_positions.keys())

def _get_label_coords(r, theta_rad, offset=24):
    # Compute label coordinates outside the radar for annotation lines
    x = (r + offset) * np.cos(theta_rad)
    y = (r + offset) * np.sin(theta_rad)
    return x, y

def create_bullseye_chart_with_callouts(data, segment_column='Category'):
    segments = data[segment_column].unique()
    num_segments = len(segments)
    # Get angles for each asset in its segment
    angles, segment_positions = calculate_segment_positions(data, segment_column)

    # Chart setup
    fig = go.Figure()
    circle_radii = [25, 50, 75, 100]
    circle_colors = [
        'rgba(230,230,230,0.3)', 'rgba(200,200,200,0.3)',
        'rgba(170,170,170,0.3)', 'rgba(140,140,140,0.3)'
    ]
    prev_r = 0
    for r, c in zip(circle_radii, circle_colors):
        fig.add_trace(go.Barpolar(
            base=[prev_r],
            r=[r - prev_r],
            theta=[0], width=[360],
            marker_line_color='lightgray', marker_line_width=1,
            marker_color=c,
            hoverinfo='skip', showlegend=False
        ))
        prev_r = r

    # Add Phase labels
    circle_labels = ['Phase 1', 'Phase 2', 'Phase 3', 'Marketed']
    for r, lbl in zip(circle_radii, circle_labels):
        fig.add_trace(go.Scatterpolar(
            r=[r + 5], theta=[270], # bottom center
            mode='text', text=[lbl],
            textfont=dict(size=11, color='gray'),
            hoverinfo='skip', showlegend=False
        ))

    # Draw segment dividers and category labels
    for idx, (seg, info) in enumerate(segment_positions.items()):
        base = info['base_angle']
        end = info['end_angle']
        mid = (base + end) / 2
        # Divider line
        fig.add_trace(go.Scatterpolar(
            r=[0, circle_radii[-1]],
            theta=[np.degrees(base), np.degrees(base)],
            mode='lines', line=dict(color='gray', width=1.5),
            hoverinfo='skip', showlegend=False
        ))
        # Add category label as annotation at the top
        fig.add_trace(go.Scatterpolar(
            r=[circle_radii[-1] + 32],
            theta=[np.degrees(mid)],
            mode='text',
            text=[f"<b>{seg}</b>"],
            textfont=dict(size=16, color='#333'),
            hoverinfo='skip',
            showlegend=False
        ))

    # For 2 categories, force vertical split and center labels
    if num_segments == 2:
        # Draw vertical line
        fig.add_trace(go.Scatterpolar(
            r=[0, circle_radii[-1]],
            theta=[90, 90],
            mode='lines', line=dict(color='gray', width=2),
            hoverinfo='skip', showlegend=False
        ))
        fig.add_trace(go.Scatterpolar(
            r=[0, circle_radii[-1]],
            theta=[270, 270],
            mode='lines', line=dict(color='gray', width=2),
            hoverinfo='skip', showlegend=False
        ))

    # Draw asset points and callout lines/labels OUTSIDE the radar
    for idx, (_, row) in enumerate(data.iterrows()):
        ang = angles[idx]
        rad = phase_to_radius(row['Phase_Status'])
        colr = st.session_state.moa_colors.get(row['MOA'], '#808080')
        theta_deg = np.degrees(ang)
        theta_rad = ang

        # Dot on radar
        fig.add_trace(go.Scatterpolar(
            r=[rad], theta=[theta_deg],
            mode='markers', marker=dict(size=12, color=colr, line=dict(width=1, color='#666')),
            hoverinfo='skip', showlegend=False
        ))

        # Compute callout label coordinates OUTSIDE the radar
        label_r = 120  # Outside the largest ring
        label_x, label_y = _get_label_coords(label_r, theta_rad, offset=0)
        dot_x, dot_y = _get_label_coords(rad, theta_rad, offset=0)

        # Draw callout line from dot to label
        fig.add_trace(go.Scatterpolar(
            r=[rad, label_r],
            theta=[theta_deg, theta_deg],
            mode='lines',
            line=dict(color=colr, width=1.5),
            hoverinfo='skip',
            showlegend=False
        ))

        # Asset Name (bold) and Company Name (regular) as HTML in annotation
        label_html = (
            f"<span style='font-weight:700; font-size:15px'>{row['Asset']}</span><br>"
            f"<span style='font-weight:400; font-size:13px'>{row['Company']}</span>"
        )
        fig.add_trace(go.Scatterpolar(
            r=[label_r],
            theta=[theta_deg],
            mode='text',
            text=[label_html],
            textfont=dict(size=14, color='#222'),
            hoverinfo='skip',
            showlegend=False
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=False, range=[0, 130]),
            angularaxis=dict(visible=False)
        ),
        showlegend=False, width=1000, height=650, margin=dict(l=20, r=20, t=30, b=30),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )
    return fig

# --- Pages ---
if st.session_state.page_state == 'landing':
    st.title("🎯 Bulls Eye Radar Chart")
    st.markdown("### Welcome to Asset Development Portfolio Visualization")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("---")
        if st.button("📊 Use Sample Data", use_container_width=True, type="primary"):
            st.session_state.page_state = 'dashboard'
            st.rerun()
        st.markdown("**OR**")
        if st.button("📤 Upload Your Data", use_container_width=True):
            st.session_state.page_state = 'upload'
            st.rerun()
        st.markdown("---")
        st.markdown("### Sample Data Preview")
        st.dataframe(st.session_state.assets_data, use_container_width=True)

elif st.session_state.page_state == 'upload':
    st.title("📤 Upload Your Data")
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📋 Required CSV Format")
        sample_data = pd.DataFrame({
            'Asset': ['DPI-387', 'Cariprazine'],
            'Company': ['Defender Pharma', 'Abbvie'],
            'Phase_Status': ['Phase 1', 'Phase 3'],
            'MOA': ['Pan muscarinic antagonist', 'D2 Antagonist'],
            'Category': ['Treatment Sensitive Category', 'Treatment Resistant Category']
        })
        st.dataframe(sample_data, use_container_width=True)
        st.info("**Phase_Status** must be one of: Phase 1, Phase 2, Phase 3, Marketed")
        template_csv = sample_data.to_csv(index=False)
        st.download_button(
            "📥 Download Template",
            template_csv,
            "template.csv",
            "text/csv",
            use_container_width=True
        )

    with col2:
        st.subheader("📤 Upload File")
        uploaded_file = st.file_uploader(
            "Choose CSV file",
            type="csv",
            help="Upload CSV with Asset, Company, Phase_Status, MOA, Category columns"
        )

        if uploaded_file is not None:
            try:
                uploaded_data = pd.read_csv(uploaded_file)
                st.subheader("📊 Uploaded Data Preview")
                st.dataframe(uploaded_data, use_container_width=True)

                required_cols = ['Asset', 'Company', 'Phase_Status', 'MOA', 'Category']
                missing_cols = [col for col in required_cols if col not in uploaded_data.columns]
                if missing_cols:
                    st.error(f"❌ Missing columns: {', '.join(missing_cols)}")
                else:
                    valid_phases = ['Phase 1', 'Phase 2', 'Phase 3', 'Marketed']
                    invalid_phases = uploaded_data[~uploaded_data['Phase_Status'].isin(valid_phases)]['Phase_Status'].unique()
                    if len(invalid_phases) > 0:
                        st.error(f"❌ Invalid Phase_Status values: {', '.join(invalid_phases)}")
                        st.info(f"Valid values are: {', '.join(valid_phases)}")
                    else:
                        new_moas = set(uploaded_data['MOA'].unique()) - set(st.session_state.moa_colors.keys())
                        colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7', '#dda0dd', '#98d8c8', '#f7dc6f']
                        for i, moa in enumerate(new_moas):
                            st.session_state.moa_colors[moa] = colors[i % len(colors)]
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Use This Data", type="primary", use_container_width=True):
                                st.session_state.assets_data = uploaded_data
                                st.session_state.page_state = 'dashboard'
                                st.success("🎉 Data uploaded successfully!")
                                st.rerun()
                        with col2:
                            if st.button("❌ Cancel", use_container_width=True):
                                st.session_state.page_state = 'landing'
                                st.rerun()
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
    if st.button("⬅️ Back to Landing", use_container_width=True):
        st.session_state.page_state = 'landing'
        st.rerun()

elif st.session_state.page_state == 'dashboard':
    with st.sidebar:
        st.title("🎨 Chart Settings")
        st.subheader("Segments")
        segment_column = 'Category'  # Only allow category for this chart type
        st.markdown("_Segments by_ **Category** _(fixed)_")

        st.subheader("MOA Colors")
        current_moas = st.session_state.assets_data['MOA'].unique() if 'MOA' in st.session_state.assets_data.columns else []
        for moa in current_moas:
            if moa in st.session_state.moa_colors:
                new_color = st.color_picker(
                    f"{moa[:18]}...",
                    st.session_state.moa_colors[moa],
                    key=f"color_{moa}"
                )
                st.session_state.moa_colors[moa] = new_color
        st.markdown("---")
        if st.button("✏️ Edit Data", use_container_width=True):
            st.session_state.page_state = 'edit'
            st.rerun()
        if st.button("📤 Upload New Data", use_container_width=True):
            st.session_state.page_state = 'upload'
            st.rerun()
        if st.button("🏠 Back to Landing", use_container_width=True):
            st.session_state.page_state = 'landing'
            st.rerun()

    # MAIN: Legend/Trial Status (left), Chart (right)
    col1, col2 = st.columns([1.08, 2.2], gap="large")

    with col1:
        st.markdown("### Mechanism of Action")
        moa_df = create_moa_legend()
        for _, row in moa_df.iterrows():
            st.markdown(
                f"<div style='display: flex; align-items: center; margin-bottom: 7px;'>"
                f"<div style='width: 15px; height: 15px; border-radius: 50%; background: {row['Color']}; margin-right: 10px; border: 1.3px solid #333;'></div>"
                f"<span style='font-size: 15px; color: #2b2b2b'>{row['MOA']}</span>"
                f"</div>",
                unsafe_allow_html=True
            )

        st.markdown("### Trial Status")
        # Show trial status legend (icons and text)
        st.markdown(
            "<div style='display: flex; align-items: center; margin-bottom: 6px;'>"
            "<span style='font-size:20px; margin-right:9px;'>🟢</span>"
            "<span style='font-size:15px; font-weight:600'>Advanced to next Phase of development</span>"
            "</div>"
            "<div style='display: flex; align-items: center; margin-bottom: 2px;'>"
            "<span style='font-size:20px; margin-right:10px;'>❓</span>"
            "<span style='font-size:15px; font-weight:600'>Status Unknown</span>"
            "</div>",
            unsafe_allow_html=True
        )

    with col2:
        fig = create_bullseye_chart_with_callouts(
            st.session_state.assets_data,
            segment_column='Category'
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

elif st.session_state.page_state == 'edit':
    st.title("✏️ Edit Asset Data")
    edited_data = st.data_editor(
        st.session_state.assets_data,
        num_rows="dynamic",
        use_container_width=True,
        key="data_editor",
        column_config={
            "Asset": st.column_config.TextColumn("Asset Name", required=True, width="medium"),
            "Company": st.column_config.TextColumn("Company Name", required=True, width="large"),
            "Phase_Status": st.column_config.SelectboxColumn(
                "Phase Status",
                options=['Phase 1', 'Phase 2', 'Phase 3', 'Marketed'],
                required=True,
                width="small"
            ),
            "MOA": st.column_config.SelectboxColumn(
                "Mechanism of Action",
                options=list(st.session_state.moa_colors.keys()),
                required=True,
                width="large"
            ),
            "Category": st.column_config.TextColumn("Category", required=True, width="medium"),
        }
    )
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        if st.button("💾 Save Changes", type="primary", use_container_width=True):
            st.session_state.assets_data = edited_data
            st.success("✅ Changes saved!")
            st.rerun()
    with col2:
        if st.button("🔄 Reset Default", use_container_width=True):
            st.session_state.assets_data = pd.DataFrame({
                'Asset': ['DPI-387', 'Cariprazine', 'Lumateperone', 'ILT1011'],
                'Company': ['Defender Pharma', 'Abbvie', 'Xyz', 'Hôpitaux de Paris/ Iltoo Pharma'],
                'Phase_Status': ['Phase 1', 'Phase 3', 'Phase 3', 'Phase 2'],
                'MOA': ['Pan muscarinic antagonist', 'D2 Antagonist', 'Dopamine/Serotonin Modulator', 'Interleukin 2'],
                'Category': ['Treatment Sensitive Category', 'Treatment Resistant Category', 'Treatment Resistant Category', 'Treatment Resistant Category']
            })
            st.success("✅ Reset to defaults!")
            st.rerun()
    with col3:
        csv_buffer = io.StringIO()
        st.session_state.assets_data.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name="asset_data.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col4:
        if st.button("⬅️ Back to Chart", use_container_width=True):
            st.session_state.page_state = 'dashboard'
            st.rerun()

# --- Footer ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; font-size: 12px;'>Built with Streamlit | Bulls Eye Asset Portfolio Visualization</div>",
    unsafe_allow_html=True
)
