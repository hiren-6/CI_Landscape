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
    phase_mapping = {
        'Phase 1': 25,
        'Phase 2': 50,
        'Phase 3': 75,
        'Marketed': 100
    }
    return phase_mapping.get(phase, 25)

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
    """Create combined chart with legend on the right side and permanent asset labels"""
    
    # Create subplot with custom spacing - radar chart on left, legend on right
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.75, 0.25],  # More space for radar chart
        subplot_titles=('', ''),
        specs=[[{"type": "polar"}, {"type": "xy"}]]
    )
    
    # Create the radar chart
    angles, segment_info = calculate_segment_positions(data, segment_column, max_segments)
    
    # Add concentric circles with improved styling
    circle_radii = [25, 50, 75, 100]
    circle_colors = ['rgba(230, 230, 230, 0.3)', 'rgba(200, 200, 200, 0.3)', 
                    'rgba(170, 170, 170, 0.3)', 'rgba(140, 140, 140, 0.3)']
    circle_labels = ['Phase 1', 'Phase 2', 'Phase 3', 'Marketed']
    
    for i, (radius, color, label) in enumerate(zip(circle_radii, circle_colors, circle_labels)):
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
            showlegend=False,
            hoverinfo='skip'
        ), row=1, col=1)
    
    # Add phase labels at the bottom center of each ring
    for i, (radius, label) in enumerate(zip(circle_radii, circle_labels)):
        fig.add_annotation(
            x=0,
            y=-radius - 8,
            text=label,
            showarrow=False,
            font=dict(size=10, color='gray'),
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='lightgray',
            borderwidth=1,
            xref="x",
            yref="y"
        )
    
    # Add segment dividers and labels
    if max_segments > 1:
        for segment, info in segment_info.items():
            base_angle = info['base_angle']
            
            # Vertical divider line
            fig.add_trace(go.Scatterpolar(
                r=[0, 100],
                theta=[np.degrees(base_angle), np.degrees(base_angle)],
                mode='lines',
                line=dict(color='gray', width=2),
                showlegend=False,
                hoverinfo='skip'
            ), row=1, col=1)
            
            # Segment label at the top
            mid_angle = (base_angle + info['end_angle']) / 2
            label_radius = 110
            
            fig.add_annotation(
                x=label_radius * np.cos(mid_angle),
                y=label_radius * np.sin(mid_angle),
                text=f"<b>{segment}</b>",
                showarrow=False,
                font=dict(size=12, color='black', family='Arial'),
                bgcolor='rgba(173, 216, 230, 0.9)',
                bordercolor='gray',
                borderwidth=1,
                xref="x",
                yref="y"
            )
    
    # Add assets with permanent labels
    for idx, (_, row) in enumerate(data.iterrows()):
        if idx < len(angles):
            angle = angles[idx]
            radius = phase_to_radius(row['Phase_Status'])
            moa_color = st.session_state.moa_colors.get(row['MOA'], '#808080')
            
            # Line from dot to label (extended further out)
            label_radius = 140
            
            fig.add_trace(go.Scatterpolar(
                r=[radius, label_radius],
                theta=[np.degrees(angle), np.degrees(angle)],
                mode='lines',
                line=dict(color='black', width=1),
                showlegend=False,
                hoverinfo='skip'
            ), row=1, col=1)
            
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
                showlegend=False,
                hovertemplate=f'<b>{row["Asset"]}</b><br>{row["Company"]}<br>Phase: {row["Phase_Status"]}<br>MOA: {row["MOA"]}<extra></extra>'
            ), row=1, col=1)
            
            # Permanent asset label outside circle
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
            
            # Add permanent asset name and company label
            fig.add_annotation(
                x=label_x,
                y=label_y,
                text=f"<b>{row['Asset']}</b><br><span style='font-size:10px'>{row['Company']}</span>",
                showarrow=False,
                font=dict(
                    family=st.session_state.font_settings['family'],
                    size=st.session_state.font_settings['size'],
                    color=st.session_state.font_settings['color']
                ),
                xanchor=xanchor,
                yanchor=yanchor,
                bgcolor='rgba(255,255,255,0.9)',
                bordercolor='gray',
                borderwidth=1,
                xref="x",
                yref="y"
            )
    
    # Add MOA Legend on the right side
    moa_legend = create_moa_legend()
    y_pos = 0.95
    
    # Legend title
    fig.add_annotation(
        x=0.85, y=0.98,
        text="<b>Mechanism of Action</b>",
        showarrow=False,
        font=dict(size=14, color='black', family='Arial'),
        xref="paper", yref="paper"
    )
    
    # MOA legend items
    for _, row in moa_legend.iterrows():
        # Color dot
        fig.add_trace(go.Scatter(
            x=[0.77], y=[y_pos - 0.05],
            mode='markers',
            marker=dict(size=12, color=row['Color'], symbol='circle', line=dict(width=1, color='gray')),
            showlegend=False,
            hoverinfo='skip'
        ), row=1, col=2)
        
        # MOA text
        fig.add_annotation(
            x=0.8, y=y_pos - 0.05,
            text=f"{row['MOA']}",
            showarrow=False,
            font=dict(size=10, color='black', family='Arial'),
            xref="paper", yref="paper",
            xanchor="left"
        )
        y_pos -= 0.08
    
    # Trial Status section
    y_pos -= 0.05
    fig.add_annotation(
        x=0.85, y=y_pos,
        text="<b>Trial Status</b>",
        showarrow=False,
        font=dict(size=14, color='black', family='Arial'),
        xref="paper", yref="paper"
    )
    
    y_pos -= 0.08
    fig.add_annotation(
        x=0.77, y=y_pos,
        text="🚀 Advanced to next Phase of development",
        showarrow=False,
        font=dict(size=10, color='green', family='Arial'),
        xref="paper", yref="paper",
        xanchor="left"
    )
    
    y_pos -= 0.08
    fig.add_annotation(
        x=0.77, y=y_pos,
        text="❓ Status Unknown",
        showarrow=False,
        font=dict(size=10, color='gray', family='Arial'),
        xref="paper", yref="paper",
        xanchor="left"
    )
    
    # Update layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=False, range=[0, 160]),  # Extended range for labels
            angularaxis=dict(visible=False)
        ),
        showlegend=False,
        width=1400,  # Increased width for better spacing
        height=700,
        margin=dict(l=20, r=20, t=50, b=50),
        plot_bgcolor='white',
        paper_bgcolor='white',
        title=dict(
            text="Asset Development Portfolio",
            x=0.4,  # Adjust title position for radar chart
            font=dict(size=20, family='Arial')
        )
    )
    
    # Hide right subplot axes
    fig.update_xaxes(visible=False, row=1, col=2)
    fig.update_yaxes(visible=False, row=1, col=2)
    
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
