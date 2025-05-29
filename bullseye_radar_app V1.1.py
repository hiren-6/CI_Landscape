import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math

# Set page config
st.set_page_config(
    page_title="Bulls Eye Radar Chart",
    page_icon="🎯",
    layout="wide"
)

# Initialize session state
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
        'Pan muscarinic antagonist': '#4472C4',
        'Selective D3/D2/D3 Modulator': '#E91E63',
        'Psychedelic': '#F44336',
        'D2 Antagonist': '#9C27B0',
        'P2X7 Functional Antagonist': '#9E9E9E',
        'Interleukin 2': '#FF9800',
        'NMDA Antagonist': '#2196F3',
        'Kappa Receptor Antagonist': '#009688',
        'Dopamine/Serotonin Modulator': '#4CAF50',
        'Cannabinoid': '#8BC34A',
        'BDNF': '#00BCD4',
        'TRB selective agonist': '#424242'
    }

if 'font_settings' not in st.session_state:
    st.session_state.font_settings = {
        'family': 'Arial',
        'size': 12,
        'bold': False,
        'italic': False,
        'color': '#000000'
    }

def phase_to_radius(phase):
    """Convert phase status to radius position"""
    mapping = {
        'Phase 1': 25,
        'Phase 2': 50,
        'Phase 3': 75,
        'Marketed': 100
    }
    return mapping.get(phase, 0)

def calculate_segment_positions(data, segment_column, max_segments=8):
    """Calculate angular position for each asset within its segment"""
    if segment_column not in data.columns:
        return np.linspace(0, 2 * np.pi, len(data), endpoint=False)
    
    segments = data[segment_column].unique()
    num_segments = min(len(segments), max_segments)
    
    # Calculate angle allocation for each segment
    segment_angle = 2 * np.pi / num_segments
    
    angles = []
    segment_positions = {}
    
    # Group data by segment
    for i, segment in enumerate(segments[:num_segments]):
        segment_data = data[data[segment_column] == segment]
        base_angle = i * segment_angle
        
        # Calculate positions within segment
        assets_in_segment = len(segment_data)
        if assets_in_segment == 1:
            positions = [base_angle + segment_angle / 2]
        else:
            # Distribute assets within segment with padding
            padding = segment_angle * 0.1  # 10% padding on each side
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
        if segment in segment_positions:
            segment_data = data[data[segment_column] == segment]
            asset_idx = list(segment_data.index).index(row.name)
            if asset_idx < len(segment_positions[segment]['positions']):
                angles.append(segment_positions[segment]['positions'][asset_idx])
    
    return np.array(angles), segment_positions

def create_moa_legend():
    """Create MOA legend"""
    moa_data = []
    for moa, color in st.session_state.moa_colors.items():
        count = len(st.session_state.assets_data[st.session_state.assets_data['MOA'] == moa]) if 'MOA' in st.session_state.assets_data.columns else 0
        if count > 0:
            moa_data.append({'MOA': moa, 'Color': color, 'Count': count})
    
    return pd.DataFrame(moa_data)

def create_combined_chart_with_legend(data, segment_column='Category', max_segments=2):
    """Creates a bullseye chart with true donut rings and polar-native text labels."""
    # 1) Setup subplots: polar for chart, xy for legend
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.75, 0.25],
        specs=[[{"type": "polar"}, {"type": "xy"}]]
    )

    # 2) Draw true donut rings via Barpolar
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
        ), row=1, col=1)
        prev_r = r

    # 3) Attach phase labels as native polar text
    circle_labels = ['Phase 1', 'Phase 2', 'Phase 3', 'Marketed']
    for r, lbl in zip(circle_radii, circle_labels):
        fig.add_trace(go.Scatterpolar(
            r=[r + 8], theta=[270],  # bottom center
            mode='text', text=[lbl],
            textfont=dict(size=10, color='gray'),
            hoverinfo='skip', showlegend=False
        ), row=1, col=1)

    # 4) Segment dividers & titles
    angles, seg_info = calculate_segment_positions(data, segment_column, max_segments)
    for seg, info in seg_info.items():
        base = info['base_angle']; end = info['end_angle']
        # Divider line
        fig.add_trace(go.Scatterpolar(
            r=[0, circle_radii[-1]],
            theta=[np.degrees(base), np.degrees(base)],
            mode='lines', line=dict(color='gray', width=2),
            hoverinfo='skip', showlegend=False
        ), row=1, col=1)
        # Segment label
        mid = (base + end) / 2
        fig.add_trace(go.Scatterpolar(
            r=[circle_radii[-1] + 10], theta=[np.degrees(mid)],
            mode='text', text=[f"<b>{seg}</b>"],
            textfont=dict(size=12, color='black'),
            hoverinfo='skip', showlegend=False
        ), row=1, col=1)

    # 5) Plot assets & callouts in polar space
    for idx, (_, row) in enumerate(data.iterrows()):
        ang = angles[idx]; rad = phase_to_radius(row['Phase_Status'])
        colr = st.session_state.moa_colors.get(row['MOA'], '#808080')
        # dot
        fig.add_trace(go.Scatterpolar(
            r=[rad], theta=[np.degrees(ang)],
            mode='markers', marker=dict(size=10, color=colr, line=dict(width=1, color='gray')),
            hoverinfo='text', hovertext=row['Asset'], showlegend=False
        ), row=1, col=1)
        # connecting line
        fig.add_trace(go.Scatterpolar(
            r=[rad, circle_radii[-1] + 30], theta=[np.degrees(ang), np.degrees(ang)],
            mode='lines', line=dict(color=colr, width=1), hoverinfo='skip', showlegend=False
        ), row=1, col=1)
        # label
        fig.add_trace(go.Scatterpolar(
            r=[circle_radii[-1] + 30], theta=[np.degrees(ang)],
            mode='text', text=[row['Asset']], textposition='middle right',
            textfont=dict(size=10, color=colr), hoverinfo='skip', showlegend=False
        ), row=1, col=1)

    # 6) Add MOA legend on XY subplot (reuse your existing logic)
    moa_df = create_moa_legend()
    y_pos = 0.9
    for _, m in moa_df.iterrows():
        fig.add_trace(go.Scatter(
            x=[0.77], y=[y_pos], mode='markers',
            marker=dict(size=12, color=m['Color'], symbol='circle', line=dict(width=1, color='gray')),
            showlegend=False, hoverinfo='skip'
        ), row=1, col=2)
        fig.add_annotation(
            x=0.8, y=y_pos, xref='paper', yref='paper', text=m['MOA'],
            showarrow=False, font=dict(size=10), xanchor='left'
        )
        y_pos -= 0.08
    # (keep your Status Unknown annotation and layout tweaks)

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=False, range=[0, circle_radii[-1] + 40]), angularaxis=dict(visible=False)),
        showlegend=False, width=1400, height=700, margin=dict(l=20, r=20, t=50, b=50)
    )
    return fig

# Landing Page
if st.session_state.page_state == 'landing':
    st.title("🎯 Bulls Eye Radar Chart")
    st.markdown("### Welcome to Asset Development Portfolio Visualization")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("---")
        
        # Option 1: Use dummy data
        if st.button("📊 Use Sample Data", use_container_width=True, type="primary"):
            st.session_state.page_state = 'dashboard'
            st.rerun()
        
        st.markdown("**OR**")
        
        # Option 2: Upload data
        if st.button("📤 Upload Your Data", use_container_width=True):
            st.session_state.page_state = 'upload'
            st.rerun()
        
        st.markdown("---")
        
        # Show sample data preview
        st.markdown("### Sample Data Preview")
        st.dataframe(st.session_state.assets_data, use_container_width=True)

# Upload Page
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
        
        # Download template
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
                
                # Validation
                required_cols = ['Asset', 'Company', 'Phase_Status', 'MOA', 'Category']
                missing_cols = [col for col in required_cols if col not in uploaded_data.columns]
                
                if missing_cols:
                    st.error(f"❌ Missing columns: {', '.join(missing_cols)}")
                else:
                    # Validate phase status
                    valid_phases = ['Phase 1', 'Phase 2', 'Phase 3', 'Marketed']
                    invalid_phases = uploaded_data[~uploaded_data['Phase_Status'].isin(valid_phases)]['Phase_Status'].unique()
                    
                    if len(invalid_phases) > 0:
                        st.error(f"❌ Invalid Phase_Status values: {', '.join(invalid_phases)}")
                        st.info(f"Valid values are: {', '.join(valid_phases)}")
                    else:
                        # Update MOA colors for new MOAs
                        new_moas = set(uploaded_data['MOA'].unique()) - set(st.session_state.moa_colors.keys())
                        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
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
    
    # Back button
    if st.button("⬅️ Back to Landing", use_container_width=True):
        st.session_state.page_state = 'landing'
        st.rerun()

# Dashboard Page
elif st.session_state.page_state == 'dashboard':
    
    # Create sidebar for chart settings
    with st.sidebar:
        st.title("🎨 Chart Settings")
        
        st.subheader("Segments")
        segment_column = st.selectbox("Segment By:", ['Category', 'Company', 'MOA'], index=0)
        max_segments = st.slider("Max Segments:", 2, 8, 2)
        
        st.subheader("Font Settings")
        st.session_state.font_settings['family'] = st.selectbox(
            "Font Family:", 
            ['Arial', 'Times New Roman', 'Helvetica', 'Georgia', 'Courier New'],
            index=0
        )
        st.session_state.font_settings['size'] = st.slider("Font Size:", 8, 20, 12)
        
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.font_settings['bold'] = st.checkbox("Bold")
        with col2:
            st.session_state.font_settings['italic'] = st.checkbox("Italic")
        
        st.session_state.font_settings['color'] = st.color_picker("Font Color:", "#000000")
        
        st.subheader("MOA Colors")
        current_moas = st.session_state.assets_data['MOA'].unique() if 'MOA' in st.session_state.assets_data.columns else []
        
        for moa in current_moas:
            if moa in st.session_state.moa_colors:
                new_color = st.color_picker(
                    f"{moa[:15]}...", 
                    st.session_state.moa_colors[moa],
                    key=f"color_{moa}"
                )
                st.session_state.moa_colors[moa] = new_color
        
        st.markdown("---")
        
        # Data management buttons
        if st.button("✏️ Edit Data", use_container_width=True):
            st.session_state.page_state = 'edit'
            st.rerun()
        
        if st.button("📤 Upload New Data", use_container_width=True):
            st.session_state.page_state = 'upload'
            st.rerun()
        
        if st.button("🏠 Back to Landing", use_container_width=True):
            st.session_state.page_state = 'landing'
            st.rerun()
    
    # Main content area - removed title as it's now in the chart
    
    # Create combined chart with legend on the right
    combined_fig = create_combined_chart_with_legend(
        st.session_state.assets_data,
        segment_column=segment_column,
        max_segments=max_segments
    )
    
    # Display chart without zoom controls
    st.plotly_chart(combined_fig, use_container_width=True, config={'displayModeBar': False})

# Edit Data Page
elif st.session_state.page_state == 'edit':
    st.title("✏️ Edit Asset Data")
    
    # Data editor
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
    
    # Action buttons
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
        # Download current data
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

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; font-size: 12px;'>Built with Streamlit | Bulls Eye Asset Portfolio Visualization</div>",
    unsafe_allow_html=True
)
