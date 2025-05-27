import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import io
import math

# Set page config
st.set_page_config(
    page_title="Bulls Eye Radar Chart",
    page_icon="🎯",
    layout="wide"
)

# Initialize session state
if 'assets_data' not in st.session_state:
    st.session_state.assets_data = pd.DataFrame({
        'Asset': ['DPI-387', 'Cariprazine', 'Lumateperone', 'ILT1011'],
        'Company': ['Defender Pharma', 'Abbvie', 'Xyz', 'Hôpitaux de Paris/ Iltoo Pharma'],
        'Current_Phase': [35, 85, 75, 60],
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

if 'editable_mode' not in st.session_state:
    st.session_state.editable_mode = False

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

def create_bullseye_radar_advanced(data, segment_column='Category', max_segments=2, title="Bulls Eye Radar Chart"):
    """Create advanced bulls eye radar chart matching the reference image"""
    
    # Calculate positions
    angles, segment_info = calculate_segment_positions(data, segment_column, max_segments)
    
    # Create the plotly figure
    fig = go.Figure()
    
    # Add concentric circles with labels
    circle_radii = [25, 50, 75, 100]
    circle_colors = ['rgba(200, 200, 200, 0.1)', 'rgba(150, 150, 150, 0.1)', 
                    'rgba(100, 100, 100, 0.1)', 'rgba(50, 50, 50, 0.1)']
    circle_labels = ['Phase 1', 'Phase 2', 'Phase 3', 'Marketed']
    
    for i, (radius, color, label) in enumerate(zip(circle_radii, circle_colors, circle_labels)):
        # Create circle
        circle_angles = np.linspace(0, 2 * np.pi, 100)
        circle_r = [radius] * 100
        circle_theta = circle_angles
        
        fig.add_trace(go.Scatterpolar(
            r=circle_r,
            theta=np.degrees(circle_theta),
            mode='lines',
            line=dict(color='lightgray', width=1),
            fill='toself',
            fillcolor=color,
            name=label,
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Add circle labels
        label_angle = np.pi / 4  # 45 degrees
        label_x = radius * np.cos(label_angle)
        label_y = radius * np.sin(label_angle)
        
        fig.add_annotation(
            x=label_x,
            y=label_y,
            text=label,
            showarrow=False,
            font=dict(size=10, color='gray'),
            bgcolor='rgba(255,255,255,0.7)'
        )
    
    # Add segment dividers
    if max_segments > 1:
        segments = list(segment_info.keys())
        for segment, info in segment_info.items():
            # Add segment divider lines
            base_angle = info['base_angle']
            end_angle = info['end_angle']
            
            # Divider line
            fig.add_trace(go.Scatterpolar(
                r=[0, 120],
                theta=[np.degrees(base_angle), np.degrees(base_angle)],
                mode='lines',
                line=dict(color='gray', width=2),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            # Segment background
            segment_angles = np.linspace(base_angle, end_angle, 20)
            segment_r = [110] * 20
            
            fig.add_trace(go.Scatterpolar(
                r=segment_r,
                theta=np.degrees(segment_angles),
                mode='lines',
                line=dict(color='lightblue', width=0),
                fill='toself',
                fillcolor='rgba(173, 216, 230, 0.2)',
                showlegend=False,
                hoverinfo='skip'
            ))
            
            # Segment label
            mid_angle = (base_angle + end_angle) / 2
            label_radius = 130
            
            fig.add_annotation(
                x=label_radius * np.cos(mid_angle),
                y=label_radius * np.sin(mid_angle),
                text=f"<b>{segment}</b>",
                showarrow=False,
                font=dict(size=14, color='black'),
                bgcolor='rgba(173, 216, 230, 0.8)',
                bordercolor='gray',
                borderwidth=1
            )
    
    # Add assets as dots with lines extending outside
    for idx, (_, row) in enumerate(data.iterrows()):
        if idx < len(angles):
            angle = angles[idx]
            radius = row['Current_Phase']
            moa_color = st.session_state.moa_colors.get(row['MOA'], '#808080')
            
            # Line from dot to outside (for label connection)
            label_radius = 140
            
            fig.add_trace(go.Scatterpolar(
                r=[radius, label_radius],
                theta=[np.degrees(angle), np.degrees(angle)],
                mode='lines',
                line=dict(color='black', width=1),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            # Asset dot
            fig.add_trace(go.Scatterpolar(
                r=[radius],
                theta=[np.degrees(angle)],
                mode='markers',
                marker=dict(
                    size=12,
                    color=moa_color,
                    symbol='circle',
                    line=dict(width=2, color='white')
                ),
                name=row['MOA'],
                showlegend=False,
                hovertemplate=f'<b>{row["Asset"]}</b><br>{row["Company"]}<br>Phase: {radius}%<br>MOA: {row["MOA"]}<extra></extra>'
            ))
            
            # Asset label outside circle
            label_x = label_radius * np.cos(angle)
            label_y = label_radius * np.sin(angle)
            
            # Determine text alignment based on angle
            if np.cos(angle) > 0:
                xanchor = 'left'
            else:
                xanchor = 'right'
                
            if np.sin(angle) > 0:
                yanchor = 'bottom'
            else:
                yanchor = 'top'
            
            font_weight = 'bold' if st.session_state.font_settings['bold'] else 'normal'
            font_style = 'italic' if st.session_state.font_settings['italic'] else 'normal'
            
            fig.add_annotation(
                x=label_x,
                y=label_y,
                text=f"<b>{row['Asset']}</b><br>{row['Company']}",
                showarrow=False,
                font=dict(
                    family=st.session_state.font_settings['family'],
                    size=st.session_state.font_settings['size'],
                    color=st.session_state.font_settings['color']
                ),
                xanchor=xanchor,
                yanchor=yanchor,
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='gray',
                borderwidth=1
            )
    
    # Update layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=False,
                range=[0, 150]
            ),
            angularaxis=dict(
                visible=False
            )
        ),
        title=dict(
            text=title,
            x=0.5,
            font=dict(size=20)
        ),
        showlegend=False,
        width=800,
        height=800,
        margin=dict(l=100, r=100, t=100, b=100),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

def create_moa_legend():
    """Create MOA legend"""
    moa_data = []
    for moa, color in st.session_state.moa_colors.items():
        count = len(st.session_state.assets_data[st.session_state.assets_data['MOA'] == moa]) if 'MOA' in st.session_state.assets_data.columns else 0
        if count > 0:
            moa_data.append({'MOA': moa, 'Color': color, 'Count': count})
    
    return pd.DataFrame(moa_data)

# Sidebar Navigation
with st.sidebar:
    st.title("🎯 Bulls Eye Radar")
    
    # Clean navigation with icons
    page = st.radio(
        "Navigation",
        options=["📊 Dashboard", "✏️ Edit Data", "📁 Upload Data"],
        label_visibility="collapsed"
    )
    
    # Extract page name
    if "Dashboard" in page:
        current_page = "Dashboard"
    elif "Edit Data" in page:
        current_page = "Edit Data"
    else:
        current_page = "Upload Data"

# Main content based on page selection
if current_page == "Dashboard":
    # Main dashboard with only the chart
    st.title("Asset Development Portfolio")
    
    # Chart controls in expandable sections
    with st.expander("🎨 Chart Settings", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Segments")
            segment_column = st.selectbox("Segment By:", ['Category', 'Company', 'MOA'], index=0)
            max_segments = st.slider("Max Segments:", 2, 8, 2)
        
        with col2:
            st.subheader("Font Settings")
            st.session_state.font_settings['family'] = st.selectbox(
                "Font Family:", 
                ['Arial', 'Times New Roman', 'Helvetica', 'Georgia', 'Courier New'],
                index=0
            )
            st.session_state.font_settings['size'] = st.slider("Font Size:", 8, 20, 12)
            
            col2a, col2b = st.columns(2)
            with col2a:
                st.session_state.font_settings['bold'] = st.checkbox("Bold")
            with col2b:
                st.session_state.font_settings['italic'] = st.checkbox("Italic")
            
            st.session_state.font_settings['color'] = st.color_picker("Font Color:", "#000000")
        
        with col3:
            st.subheader("MOA Colors")
            current_moas = st.session_state.assets_data['MOA'].unique() if 'MOA' in st.session_state.assets_data.columns else []
            
            for moa in current_moas:
                if moa in st.session_state.moa_colors:
                    new_color = st.color_picker(
                        f"{moa[:20]}...", 
                        st.session_state.moa_colors[moa],
                        key=f"color_{moa}"
                    )
                    st.session_state.moa_colors[moa] = new_color
    
    # Main chart
    radar_fig = create_bullseye_radar_advanced(
        st.session_state.assets_data,
        segment_column=segment_column,
        max_segments=max_segments,
        title=""
    )
    st.plotly_chart(radar_fig, use_container_width=True)
    
    # MOA Legend
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Mechanism of Action")
        moa_legend = create_moa_legend()
        if not moa_legend.empty:
            for _, row in moa_legend.iterrows():
                st.markdown(
                    f'<span style="color: {row["Color"]}; font-size: 20px;">●</span> {row["MOA"]} ({row["Count"]})',
                    unsafe_allow_html=True
                )
    
    with col2:
        st.subheader("Trial Status")
        st.markdown("🚀 **Advanced to next Phase of development**")
        st.markdown("❓ **Status Unknown**")

elif current_page == "Edit Data":
    st.title("Edit Asset Data")
    
    # Direct editing mode toggle
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("Modify asset information and properties")
    with col2:
        st.session_state.editable_mode = st.toggle("Chart Edit Mode", st.session_state.editable_mode)
    
    if st.session_state.editable_mode:
        st.info("💡 Chart Edit Mode: Click on asset labels in the chart to edit names directly")
        
        # Show chart with editable elements
        radar_fig = create_bullseye_radar_advanced(st.session_state.assets_data, title="Click labels to edit")
        st.plotly_chart(radar_fig, use_container_width=True)
    
    # Data editor
    st.subheader("Data Table Editor")
    edited_data = st.data_editor(
        st.session_state.assets_data,
        num_rows="dynamic",
        use_container_width=True,
        key="data_editor",
        column_config={
            "Asset": st.column_config.TextColumn("Asset Name", required=True, width="medium"),
            "Company": st.column_config.TextColumn("Company Name", required=True, width="large"),
            "Current_Phase": st.column_config.NumberColumn(
                "Current Phase (%)", 
                min_value=0, 
                max_value=100, 
                step=1,
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
                'Current_Phase': [35, 85, 75, 60],
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
        if st.button("👀 Preview", use_container_width=True):
            if not edited_data.equals(st.session_state.assets_data):
                st.info("📊 Preview of changes:")
                preview_fig = create_bullseye_radar_advanced(edited_data, title="Preview")
                st.plotly_chart(preview_fig, use_container_width=True)

elif current_page == "Upload Data":
    st.title("Upload CSV Data")
    
    # Required format
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        st.subheader("📋 Required CSV Format")
        sample_data = pd.DataFrame({
            'Asset': ['DPI-387', 'Cariprazine'],
            'Company': ['Defender Pharma', 'Abbvie'],  
            'Current_Phase': [35, 85],
            'MOA': ['Pan muscarinic antagonist', 'D2 Antagonist'],
            'Category': ['Treatment Sensitive', 'Treatment Resistant']
        })
        st.dataframe(sample_data, use_container_width=True)
        
        # Download template
        template_csv = sample_data.to_csv(index=False)
        st.download_button(
            "📥 Download Template",
            template_csv,
            "template.csv",
            "text/csv"
        )
    
    with col2:
        st.subheader("📤 Upload File")
        uploaded_file = st.file_uploader(
            "Choose CSV file",
            type="csv",
            help="Upload CSV with Asset, Company, Current_Phase, MOA, Category columns"
        )
    
    if uploaded_file is not None:
        try:
            uploaded_data = pd.read_csv(uploaded_file)
            
            st.subheader("📊 Uploaded Data Preview")
            st.dataframe(uploaded_data, use_container_width=True)
            
            # Validation
            required_cols = ['Asset', 'Company', 'Current_Phase', 'MOA', 'Category']
            missing_cols = [col for col in required_cols if col not in uploaded_data.columns]
            
            if missing_cols:
                st.error(f"❌ Missing columns: {', '.join(missing_cols)}")
            else:
                # Data cleaning
                uploaded_data['Current_Phase'] = pd.to_numeric(uploaded_data['Current_Phase'], errors='coerce')
                uploaded_data['Current_Phase'] = uploaded_data['Current_Phase'].fillna(0).clip(0, 100)
                
                # Update MOA colors for new MOAs
                new_moas = set(uploaded_data['MOA'].unique()) - set(st.session_state.moa_colors.keys())
                colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
                for i, moa in enumerate(new_moas):
                    st.session_state.moa_colors[moa] = colors[i % len(colors)]
                
                # Preview chart
                st.subheader("📈 Preview Chart")
                preview_fig = create_bullseye_radar_advanced(uploaded_data, title="Data Preview")
                st.plotly_chart(preview_fig, use_container_width=True)
                
                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Use This Data", type="primary", use_container_width=True):
                        st.session_state.assets_data = uploaded_data
                        st.success("🎉 Data uploaded successfully!")
                        st.balloons()
                        st.rerun()
                
                with col2:
                    if st.button("❌ Cancel", use_container_width=True):
                        st.rerun()
                        
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; font-size: 12px;'>Built with Streamlit | Bulls Eye Asset Portfolio Visualization</div>",
    unsafe_allow_html=True
)
