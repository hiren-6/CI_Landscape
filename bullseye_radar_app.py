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
        'Asset': ['Drug A', 'Drug B', 'Drug C', 'Drug D', 'Drug E', 'Drug F'],
        'Company': ['Pharma Corp', 'BioTech Inc', 'MedCorp', 'HealthCo', 'BioPharma', 'DrugCorp'],
        'Current_Phase': [25, 45, 70, 35, 85, 60],
        'MOA': ['Kinase Inhibitor', 'Antibody', 'Small Molecule', 'Kinase Inhibitor', 'Antibody', 'Small Molecule'],
        'Category': ['Oncology', 'Immunology', 'Oncology', 'Neurology', 'Immunology', 'Cardiology']
    })

if 'moa_colors' not in st.session_state:
    st.session_state.moa_colors = {
        'Kinase Inhibitor': '#FF6B6B',
        'Antibody': '#4ECDC4', 
        'Small Molecule': '#45B7D1',
        'Gene Therapy': '#96CEB4',
        'Cell Therapy': '#FFEAA7',
        'Protein': '#DDA0DD',
        'Vaccine': '#98D8C8',
        'Other': '#F7DC6F'
    }

def get_segments_data(data, segment_column):
    """Get unique segments and their asset counts"""
    if segment_column in data.columns:
        segments = data[segment_column].unique()
        segment_counts = data[segment_column].value_counts()
        return segments, segment_counts
    return [], {}

def calculate_position_in_segment(data, segment_column, num_segments=None):
    """Calculate angular position for each asset within its segment"""
    if segment_column not in data.columns:
        # Fallback to equal distribution
        n_assets = len(data)
        angles = np.linspace(0, 2 * np.pi, n_assets, endpoint=False)
        return angles
    
    segments, segment_counts = get_segments_data(data, segment_column)
    
    if num_segments is None:
        num_segments = len(segments)
    
    # Calculate angle allocation for each segment
    segment_angle = 2 * np.pi / num_segments
    
    angles = []
    for i, (_, row) in enumerate(data.iterrows()):
        segment = row[segment_column]
        segment_idx = list(segments).index(segment)
        
        # Count assets in this segment up to current position
        segment_data = data[data[segment_column] == segment]
        asset_idx_in_segment = list(segment_data.index).index(row.name)
        assets_in_segment = len(segment_data)
        
        # Calculate position within segment
        if assets_in_segment == 1:
            angle_in_segment = segment_angle / 2
        else:
            angle_in_segment = (asset_idx_in_segment * segment_angle) / assets_in_segment
        
        # Base angle for segment + position within segment
        base_angle = segment_idx * segment_angle
        final_angle = base_angle + angle_in_segment
        
        angles.append(final_angle)
    
    return np.array(angles)

def create_bullseye_radar(data, segment_column='Category', num_segments=None, title="Bulls Eye Radar Chart"):
    """Create a bulls eye radar chart with segments and asset representation"""
    
    # Calculate positions
    angles = calculate_position_in_segment(data, segment_column, num_segments)
    
    # Create the plotly figure
    fig = go.Figure()
    
    # Add concentric circles (bulls eye rings)
    circle_radii = [33, 66, 100]
    circle_colors = ['rgba(255, 0, 0, 0.1)', 'rgba(255, 165, 0, 0.1)', 'rgba(0, 255, 0, 0.1)']
    circle_names = ['Phase 1 (0-33%)', 'Phase 2 (34-66%)', 'Phase 3 (67-100%)']
    
    for i, (radius, color, name) in enumerate(zip(circle_radii, circle_colors, circle_names)):
        # Create circle coordinates
        circle_angles = np.linspace(0, 2 * np.pi, 100)
        circle_r = [radius] * 100
        circle_theta = circle_angles
        
        fig.add_trace(go.Scatterpolar(
            r=circle_r,
            theta=np.degrees(circle_theta),
            mode='lines',
            line=dict(color=color.replace('0.1', '0.5'), width=2),
            fill='toself',
            fillcolor=color,
            name=name,
            showlegend=True,
            hoverinfo='skip'
        ))
    
    # Add segment dividers if using segments
    if segment_column in data.columns and num_segments:
        segments, _ = get_segments_data(data, segment_column)
        segment_angle = 360 / num_segments
        
        for i in range(num_segments):
            angle = i * segment_angle
            fig.add_trace(go.Scatterpolar(
                r=[0, 100],
                theta=[angle, angle],
                mode='lines',
                line=dict(color='gray', width=1, dash='dash'),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # Group assets by MOA for legend
    moa_groups = data.groupby('MOA')
    
    # Add assets as dots with lines
    for moa, group in moa_groups:
        moa_color = st.session_state.moa_colors.get(moa, '#808080')
        
        group_angles = []
        group_radii = []
        group_labels = []
        
        for idx, (_, row) in enumerate(group.iterrows()):
            asset_angle = angles[data.index.get_loc(row.name)]
            asset_radius = row['Current_Phase']
            
            group_angles.append(asset_angle)
            group_radii.append(asset_radius)
            group_labels.append(f"{row['Asset']}<br>{row['Company']}")
            
            # Add line from center to asset position
            fig.add_trace(go.Scatterpolar(
                r=[0, asset_radius],
                theta=[np.degrees(asset_angle), np.degrees(asset_angle)],
                mode='lines',
                line=dict(color=moa_color, width=2, dash='solid'),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        # Add dots for this MOA group
        fig.add_trace(go.Scatterpolar(
            r=group_radii,
            theta=np.degrees(group_angles),
            mode='markers+text',
            marker=dict(
                size=12,
                color=moa_color,
                symbol='circle',
                line=dict(width=2, color='white')
            ),
            text=[f"{row['Asset']}<br>{row['Company']}" for _, row in group.iterrows()],
            textposition='middle right',
            textfont=dict(size=10, color='black'),
            name=f'{moa} ({len(group)})',
            showlegend=True,
            hovertemplate='<b>%{text}</b><br>Phase: %{r}%<br>MOA: ' + moa + '<extra></extra>'
        ))
    
    # Add segment labels if using segments
    if segment_column in data.columns and num_segments:
        segments, segment_counts = get_segments_data(data, segment_column)
        segment_angle = 2 * np.pi / num_segments
        
        for i, segment in enumerate(segments):
            label_angle = i * segment_angle + segment_angle / 2
            label_radius = 110  # Outside the chart
            
            fig.add_annotation(
                x=label_radius * np.cos(label_angle - np.pi/2),
                y=label_radius * np.sin(label_angle - np.pi/2),
                text=f"<b>{segment}</b><br>({segment_counts[segment]} assets)",
                showarrow=False,
                font=dict(size=12, color='black'),
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='gray',
                borderwidth=1
            )
    
    # Update layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickmode='linear',
                tick0=0,
                dtick=20,
                gridcolor='lightgray'
            ),
            angularaxis=dict(
                visible=False,  # Hide angular axis as we're using custom labels
                gridcolor='lightgray'
            )
        ),
        title=dict(
            text=title,
            x=0.5,
            font=dict(size=20)
        ),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            title="Mechanism of Action"
        ),
        width=900,
        height=700,
        margin=dict(l=50, r=150, t=80, b=50)
    )
    
    return fig

def create_progress_comparison(data):
    """Create a comparison chart showing progress by category and MOA"""
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Progress by Category', 'Progress by Mechanism of Action'),
        vertical_spacing=0.15
    )
    
    # Progress by Category
    if 'Category' in data.columns:
        category_avg = data.groupby('Category')['Current_Phase'].mean().sort_values(ascending=True)
        
        fig.add_trace(
            go.Bar(
                x=category_avg.values,
                y=category_avg.index,
                orientation='h',
                name='Category Progress',
                marker_color='lightblue',
                showlegend=False
            ),
            row=1, col=1
        )
    
    # Progress by MOA
    if 'MOA' in data.columns:
        moa_avg = data.groupby('MOA')['Current_Phase'].mean().sort_values(ascending=True)
        moa_colors = [st.session_state.moa_colors.get(moa, '#808080') for moa in moa_avg.index]
        
        fig.add_trace(
            go.Bar(
                x=moa_avg.values,
                y=moa_avg.index,
                orientation='h',
                name='MOA Progress',
                marker_color=moa_colors,
                showlegend=False
            ),
            row=2, col=1
        )
    
    fig.update_xaxes(title_text="Average Progress (%)", row=1, col=1)
    fig.update_xaxes(title_text="Average Progress (%)", row=2, col=1)
    fig.update_layout(height=600, title_text="Asset Progress Analysis")
    
    return fig

# App title
st.title("🎯 Bulls Eye Radar Chart for Asset Progress")
st.markdown("Track and visualize pharmaceutical assets across development phases with company information and mechanism-based coloring.")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select Page", ["Dashboard", "Edit Data", "Upload CSV", "Settings"])

if page == "Dashboard":
    st.header("Asset Progress Dashboard")
    
    # Segmentation controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        segment_column = st.selectbox(
            "Segment Assets By:",
            options=['Category', 'Company', 'MOA', 'None'],
            index=0
        )
    
    with col2:
        if segment_column != 'None':
            segments, _ = get_segments_data(st.session_state.assets_data, segment_column)
            max_segments = len(segments)
            num_segments = st.number_input(
                "Number of Segments:",
                min_value=2,
                max_value=max_segments,
                value=min(max_segments, 3)
            )
        else:
            num_segments = None
    
    with col3:
        show_labels = st.checkbox("Show Asset Labels", value=True)
    
    # Display current data
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Current Asset Data")
        st.dataframe(st.session_state.assets_data, use_container_width=True)
    
    with col2:
        st.subheader("Summary by MOA")
        if 'MOA' in st.session_state.assets_data.columns:
            moa_summary = st.session_state.assets_data.groupby('MOA').agg({
                'Current_Phase': ['count', 'mean'],
                'Category': lambda x: ', '.join(x.unique())
            }).round(1)
            moa_summary.columns = ['Count', 'Avg Progress', 'Categories']
            st.dataframe(moa_summary, use_container_width=True)
    
    # Create and display bulls eye radar chart
    st.subheader("Bulls Eye Radar Chart")
    
    segment_col = segment_column if segment_column != 'None' else 'Category'
    radar_fig = create_bullseye_radar(
        st.session_state.assets_data, 
        segment_column=segment_col,
        num_segments=num_segments,
        title="Asset Development Progress - Bulls Eye View"
    )
    st.plotly_chart(radar_fig, use_container_width=True)
    
    # Progress comparison chart
    st.subheader("Progress Analysis")
    comparison_fig = create_progress_comparison(st.session_state.assets_data)
    st.plotly_chart(comparison_fig, use_container_width=True)
    
    # Legend explanation
    st.subheader("Chart Legend & Interpretation")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("**📍 Chart Elements:**")
        st.markdown("""
        - **🔴 Inner Circle (0-33%)**: Early development phase
        - **🟠 Middle Circle (34-66%)**: Mid-stage development  
        - **🟢 Outer Circle (67-100%)**: Late-stage/market ready
        - **Lines**: Connect center to asset position
        - **Dots**: Asset position colored by MOA
        - **Labels**: Show asset and company name
        """)
    
    with col2:
        st.markdown("**🎨 MOA Color Coding:**")
        for moa, color in st.session_state.moa_colors.items():
            if moa in st.session_state.assets_data['MOA'].values:
                count = len(st.session_state.assets_data[st.session_state.assets_data['MOA'] == moa])
                st.markdown(f'<span style="color: {color};">●</span> **{moa}** ({count} assets)', unsafe_allow_html=True)

elif page == "Edit Data":
    st.header("Edit Asset Data")
    st.markdown("Modify asset information including names, companies, phases, MOA, and categories.")
    
    # Data editor
    edited_data = st.data_editor(
        st.session_state.assets_data,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Asset": st.column_config.TextColumn("Asset Name", required=True),
            "Company": st.column_config.TextColumn("Company Name", required=True),
            "Current_Phase": st.column_config.NumberColumn(
                "Current Phase (%)", 
                min_value=0, 
                max_value=100, 
                step=1,
                required=True
            ),
            "MOA": st.column_config.SelectboxColumn(
                "Mechanism of Action",
                options=list(st.session_state.moa_colors.keys()),
                required=True
            ),
            "Category": st.column_config.TextColumn("Category", required=True),
        }
    )
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("💾 Save Changes", type="primary"):
            st.session_state.assets_data = edited_data
            st.success("Data saved successfully!")
            st.rerun()
    
    with col2:
        if st.button("🔄 Reset to Default"):
            st.session_state.assets_data = pd.DataFrame({
                'Asset': ['Drug A', 'Drug B', 'Drug C', 'Drug D', 'Drug E', 'Drug F'],
                'Company': ['Pharma Corp', 'BioTech Inc', 'MedCorp', 'HealthCo', 'BioPharma', 'DrugCorp'],
                'Current_Phase': [25, 45, 70, 35, 85, 60],
                'MOA': ['Kinase Inhibitor', 'Antibody', 'Small Molecule', 'Kinase Inhibitor', 'Antibody', 'Small Molecule'],
                'Category': ['Oncology', 'Immunology', 'Oncology', 'Neurology', 'Immunology', 'Cardiology']
            })
            st.success("Data reset to default values!")
            st.rerun()
    
    with col3:
        # Download current data as CSV
        csv_buffer = io.StringIO()
        st.session_state.assets_data.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name="asset_progress_data.csv",
            mime="text/csv"
        )
    
    # Preview of changes
    if not edited_data.equals(st.session_state.assets_data):
        st.subheader("Preview of Changes")
        st.info("Click 'Save Changes' to apply the modifications.")
        preview_fig = create_bullseye_radar(edited_data, title="Preview - Bulls Eye Radar Chart")
        st.plotly_chart(preview_fig, use_container_width=True)

elif page == "Upload CSV":
    st.header("Upload CSV Data")
    st.markdown("Upload a CSV file with asset progress data in the required format.")
    
    # Show required format
    st.subheader("Required CSV Format")
    required_format = pd.DataFrame({
        'Asset': ['Drug Example', 'Compound X'],
        'Company': ['Big Pharma', 'Startup Bio'],
        'Current_Phase': [45, 75],
        'MOA': ['Kinase Inhibitor', 'Antibody'],
        'Category': ['Oncology', 'Immunology']
    })
    st.dataframe(required_format, use_container_width=True)
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type="csv",
        help="CSV should have columns: Asset, Company, Current_Phase, MOA, Category"
    )
    
    if uploaded_file is not None:
        try:
            # Read the CSV
            uploaded_data = pd.read_csv(uploaded_file)
            
            st.subheader("Uploaded Data Preview")
            st.dataframe(uploaded_data, use_container_width=True)
            
            # Validate required columns
            required_columns = ['Asset', 'Company', 'Current_Phase', 'MOA', 'Category']
            missing_columns = [col for col in required_columns if col not in uploaded_data.columns]
            
            if missing_columns:
                st.error(f"Missing required columns: {', '.join(missing_columns)}")
                st.info("Required columns: Asset, Company, Current_Phase, MOA, Category")
            else:
                # Data validation
                uploaded_data['Current_Phase'] = pd.to_numeric(uploaded_data['Current_Phase'], errors='coerce')
                
                # Check for invalid values
                if uploaded_data['Current_Phase'].isnull().any():
                    st.warning("Some non-numeric values found in Current_Phase column. They will be treated as 0.")
                    uploaded_data['Current_Phase'] = uploaded_data['Current_Phase'].fillna(0)
                
                # Clamp values between 0 and 100
                uploaded_data['Current_Phase'] = uploaded_data['Current_Phase'].clip(0, 100)
                
                # Update MOA colors for new MOAs
                new_moas = set(uploaded_data['MOA'].unique()) - set(st.session_state.moa_colors.keys())
                default_colors = ['#FF9999', '#99FF99', '#9999FF', '#FFFF99', '#FF99FF', '#99FFFF']
                for i, moa in enumerate(new_moas):
                    if i < len(default_colors):
                        st.session_state.moa_colors[moa] = default_colors[i]
                    else:
                        st.session_state.moa_colors[moa] = '#808080'
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    if st.button("📊 Use This Data", type="primary"):
                        st.session_state.assets_data = uploaded_data
                        st.success("Data uploaded and applied successfully!")
                        st.balloons()
                
                with col2:
                    if st.button("👁️ Preview Only"):
                        st.info("Showing preview without saving changes.")
                
                # Show charts for uploaded data
                st.subheader("Bulls Eye Radar Chart from Uploaded Data")
                uploaded_fig = create_bullseye_radar(uploaded_data, title="Uploaded Data - Bulls Eye Radar")
                st.plotly_chart(uploaded_fig, use_container_width=True)
                
                # Progress comparison
                st.subheader("Progress Analysis from Uploaded Data")
                uploaded_comparison = create_progress_comparison(uploaded_data)
                st.plotly_chart(uploaded_comparison, use_container_width=True)
                
        except Exception as e:
            st.error(f"Error reading CSV file: {str(e)}")
            st.info("Please ensure your CSV file is properly formatted.")
    
    else:
        # Download sample CSV
        sample_csv = required_format.to_csv(index=False)
        st.download_button(
            label="📥 Download Sample CSV Template",
            data=sample_csv,
            file_name="sample_asset_data.csv",
            mime="text/csv"
        )

elif page == "Settings":
    st.header("Settings & Customization")
    
    # MOA Color Settings
    st.subheader("🎨 Mechanism of Action Colors")
    st.markdown("Customize colors for different mechanisms of action:")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Current MOAs in data
        current_moas = st.session_state.assets_data['MOA'].unique() if 'MOA' in st.session_state.assets_data.columns else []
        
        for moa in current_moas:
            current_color = st.session_state.moa_colors.get(moa, '#808080')
            new_color = st.color_picker(f"{moa}", current_color, key=f"color_{moa}")
            st.session_state.moa_colors[moa] = new_color
    
    with col2:
        # Add new MOA
        st.markdown("**Add New MOA:**")
        new_moa = st.text_input("MOA Name:")
        new_moa_color = st.color_picker("MOA Color:", "#808080")
        
        if st.button("Add MOA") and new_moa:
            st.session_state.moa_colors[new_moa] = new_moa_color
            st.success(f"Added {new_moa} with color {new_moa_color}")
            st.rerun()
    
    # Display all available MOAs
    st.subheader("All Available MOAs")
    moa_df = pd.DataFrame([
        {"MOA": moa, "Color": color, "In_Current_Data": moa in current_moas}
        for moa, color in st.session_state.moa_colors.items()
    ])
    
    st.dataframe(
        moa_df,
        use_container_width=True,
        column_config={
            "Color": st.column_config.ColorColumn("Color"),
            "In_Current_Data": st.column_config.CheckboxColumn("Used in Data")
        }
    )
    
    # Reset colors
    if st.button("🔄 Reset to Default Colors"):
        st.session_state.moa_colors = {
            'Kinase Inhibitor': '#FF6B6B',
            'Antibody': '#4ECDC4', 
            'Small Molecule': '#45B7D1',
            'Gene Therapy': '#96CEB4',
            'Cell Therapy': '#FFEAA7',
            'Protein': '#DDA0DD',
            'Vaccine': '#98D8C8',
            'Other': '#F7DC6F'
        }
        st.success("Colors reset to defaults!")
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    Built with Streamlit 🚀 | Bulls Eye Radar Chart for Pharmaceutical Asset Portfolio Management
</div>
""", unsafe_allow_html=True)