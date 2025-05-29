import streamlit as st
import pandas as pd
import numpy as np
import json
import io
import streamlit.components.v1 as components

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
        return list(np.linspace(0, 2 * np.pi, len(data), endpoint=False))
    
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
    angle_dict = {}
    for idx, (_, row) in enumerate(data.iterrows()):
        segment = row[segment_column]
        if segment in segment_positions:
            segment_data = data[data[segment_column] == segment]
            asset_idx = list(segment_data['Asset']).index(row['Asset'])
            if asset_idx < len(segment_positions[segment]['positions']):
                angle_dict[row['Asset']] = segment_positions[segment]['positions'][asset_idx]
                angles.append(segment_positions[segment]['positions'][asset_idx])
    
    return angles, segment_positions

def create_d3_bullseye_chart(data, segment_column='Category', max_segments=2, font_settings=None, moa_colors=None):
    """Create D3.js bullseye radar chart component"""
    
    # Prepare data for D3.js
    angles, segment_info = calculate_segment_positions(data, segment_column, max_segments)
    
    # Convert data to JavaScript-friendly format
    assets_data = []
    for idx, (_, row) in enumerate(data.iterrows()):
        assets_data.append({
            'asset': row['Asset'],
            'company': row['Company'],
            'phase': row['Phase_Status'],
            'moa': row['MOA'],
            'category': row.get(segment_column, ''),
            'radius': phase_to_radius(row['Phase_Status']),
            'angle': angles[idx] if idx < len(angles) else 0,
            'color': moa_colors.get(row['MOA'], '#808080')
        })
    
    # Convert segment info to JavaScript format
    segments_js = []
    for segment, info in segment_info.items():
        segments_js.append({
            'name': segment,
            'baseAngle': info['base_angle'],
            'endAngle': info['end_angle']
        })
    
    # Create MOA legend data
    moa_legend = []
    for moa, color in moa_colors.items():
        count = len(data[data['MOA'] == moa])
        if count > 0:
            moa_legend.append({
                'moa': moa,
                'color': color,
                'count': count
            })
    
    # D3.js component HTML/JavaScript
    component_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://d3js.org/d3.v7.min.js"></script>
        <style>
            body {{
                margin: 0;
                padding: 20px;
                font-family: {font_settings['family']}, sans-serif;
                background: white;
            }}
            .container {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
            }}
            .chart-container {{
                flex: 0 0 75%;
            }}
            .legend-container {{
                flex: 0 0 20%;
                margin-left: 20px;
            }}
            .tooltip {{
                position: absolute;
                text-align: center;
                padding: 10px;
                font: 12px sans-serif;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                border: 0px;
                border-radius: 8px;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.2s;
            }}
            .legend-item {{
                display: flex;
                align-items: center;
                margin-bottom: 8px;
                cursor: pointer;
                opacity: 1;
                transition: opacity 0.3s;
            }}
            .legend-item.dimmed {{
                opacity: 0.3;
            }}
            .legend-dot {{
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 8px;
                border: 1px solid #ccc;
            }}
            .legend-text {{
                font-size: {font_settings['size']}px;
                color: {font_settings['color']};
                font-weight: {('bold' if font_settings['bold'] else 'normal')};
                font-style: {('italic' if font_settings['italic'] else 'normal')};
            }}
            .asset-dot {{
                cursor: pointer;
                transition: all 0.3s;
            }}
            .asset-dot:hover {{
                r: 8;
                stroke-width: 3;
            }}
            .asset-label {{
                pointer-events: none;
                font-size: {font_settings['size'] - 2}px;
            }}
            .segment-label {{
                font-weight: bold;
                font-size: {font_settings['size'] + 2}px;
            }}
            .phase-label {{
                fill: #666;
                font-size: {font_settings['size'] - 2}px;
            }}
            .export-buttons {{
                position: absolute;
                top: 10px;
                right: 10px;
            }}
            .export-buttons button {{
                margin-left: 5px;
                padding: 5px 10px;
                cursor: pointer;
                background: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 4px;
            }}
            .export-buttons button:hover {{
                background: #e0e0e0;
            }}
        </style>
    </head>
    <body>
        <div class="export-buttons">
            <button onclick="exportSVG()">Export SVG</button>
            <button onclick="exportPNG()">Export PNG</button>
        </div>
        <div class="container">
            <div class="chart-container">
                <svg id="bullseye-chart"></svg>
            </div>
            <div class="legend-container">
                <h3>Mechanism of Action</h3>
                <div id="legend"></div>
            </div>
        </div>
        <div class="tooltip"></div>
        
        <script>
            // Data from Python
            const assetsData = {json.dumps(assets_data)};
            const segmentsData = {json.dumps(segments_js)};
            const moaLegend = {json.dumps(moa_legend)};
            
            // Chart dimensions
            const width = 700;
            const height = 700;
            const margin = 80;
            const radius = Math.min(width, height) / 2 - margin;
            
            // Create SVG
            const svg = d3.select('#bullseye-chart')
                .attr('width', width)
                .attr('height', height);
            
            const g = svg.append('g')
                .attr('transform', `translate(${{width/2}},${{height/2}})`);
            
            // Create tooltip
            const tooltip = d3.select('.tooltip');
            
            // Draw concentric circles (phases) with hex colors and opacity
            const phases = [
                {{r: radius * 0.25, label: 'Phase 1', color: '#E6E6E6', opacity: 0.3}},
                {{r: radius * 0.5, label: 'Phase 2', color: '#C8C8C8', opacity: 0.3}},
                {{r: radius * 0.75, label: 'Phase 3', color: '#AAAAAA', opacity: 0.3}},
                {{r: radius, label: 'Marketed', color: '#8C8C8C', opacity: 0.3}}
            ];
            
            // Draw phase circles
            phases.forEach((phase, i) => {{
                g.append('circle')
                    .attr('r', phase.r)
                    .attr('fill', phase.color)
                    .attr('fill-opacity', phase.opacity)
                    .attr('stroke', '#ccc')
                    .attr('stroke-width', 1);
                
                // Add phase labels
                g.append('text')
                    .attr('class', 'phase-label')
                    .attr('x', 0)
                    .attr('y', phase.r + 15)
                    .attr('text-anchor', 'middle')
                    .text(phase.label);
            }});
            
            // Draw segment dividers and labels
            segmentsData.forEach(segment => {{
                const x1 = 0;
                const y1 = 0;
                const x2 = radius * Math.cos(segment.baseAngle - Math.PI/2);
                const y2 = radius * Math.sin(segment.baseAngle - Math.PI/2);
                
                // Draw divider line
                g.append('line')
                    .attr('x1', x1)
                    .attr('y1', y1)
                    .attr('x2', x2)
                    .attr('y2', y2)
                    .attr('stroke', '#666')
                    .attr('stroke-width', 2);
                
                // Add segment label
                const midAngle = (segment.baseAngle + segment.endAngle) / 2;
                const labelX = (radius + 30) * Math.cos(midAngle - Math.PI/2);
                const labelY = (radius + 30) * Math.sin(midAngle - Math.PI/2);
                
                g.append('text')
                    .attr('class', 'segment-label')
                    .attr('x', labelX)
                    .attr('y', labelY)
                    .attr('text-anchor', 'middle')
                    .text(segment.name);
            }});
            
            // Track active MOAs for filtering
            let activeMOAs = new Set(moaLegend.map(d => d.moa));
            
            // Draw assets
            const assetGroups = g.selectAll('.asset-group')
                .data(assetsData)
                .enter()
                .append('g')
                .attr('class', 'asset-group');
            
            // Asset dots
            assetGroups.append('circle')
                .attr('class', 'asset-dot')
                .attr('cx', d => d.radius * radius / 100 * Math.cos(d.angle - Math.PI/2))
                .attr('cy', d => d.radius * radius / 100 * Math.sin(d.angle - Math.PI/2))
                .attr('r', 6)
                .attr('fill', d => d.color)
                .attr('stroke', '#333')
                .attr('stroke-width', 1)
                .on('mouseover', function(event, d) {{
                    tooltip.style('opacity', 1)
                        .html(`<strong>${{d.asset}}</strong><br/>
                               Company: ${{d.company}}<br/>
                               Phase: ${{d.phase}}<br/>
                               MOA: ${{d.moa}}`);
                }})
                .on('mousemove', function(event) {{
                    tooltip.style('left', (event.pageX + 10) + 'px')
                        .style('top', (event.pageY - 10) + 'px');
                }})
                .on('mouseout', function() {{
                    tooltip.style('opacity', 0);
                }});
            
            // Asset labels with lines
            assetGroups.each(function(d) {{
                const group = d3.select(this);
                const dotX = d.radius * radius / 100 * Math.cos(d.angle - Math.PI/2);
                const dotY = d.radius * radius / 100 * Math.sin(d.angle - Math.PI/2);
                const labelX = (radius + 50) * Math.cos(d.angle - Math.PI/2);
                const labelY = (radius + 50) * Math.sin(d.angle - Math.PI/2);
                
                // Connecting line
                group.append('line')
                    .attr('x1', dotX)
                    .attr('y1', dotY)
                    .attr('x2', labelX)
                    .attr('y2', labelY)
                    .attr('stroke', d.color)
                    .attr('stroke-width', 1)
                    .attr('opacity', 0.5);
                
                // Label
                group.append('text')
                    .attr('class', 'asset-label')
                    .attr('x', labelX)
                    .attr('y', labelY)
                    .attr('text-anchor', d.angle > Math.PI ? 'end' : 'start')
                    .attr('dy', '0.35em')
                    .attr('fill', d.color)
                    .text(d.asset);
            }});
            
            // Create legend
            const legend = d3.select('#legend');
            
            const legendItems = legend.selectAll('.legend-item')
                .data(moaLegend)
                .enter()
                .append('div')
                .attr('class', 'legend-item')
                .on('click', function(event, d) {{
                    // Toggle MOA visibility
                    if (activeMOAs.has(d.moa)) {{
                        activeMOAs.delete(d.moa);
                        d3.select(this).classed('dimmed', true);
                    }} else {{
                        activeMOAs.add(d.moa);
                        d3.select(this).classed('dimmed', false);
                    }}
                    updateVisibility();
                }});
            
            legendItems.append('div')
                .attr('class', 'legend-dot')
                .style('background-color', d => d.color);
            
            legendItems.append('div')
                .attr('class', 'legend-text')
                .text(d => `${{d.moa}} (${{d.count}})`);
            
            // Update visibility based on active MOAs
            function updateVisibility() {{
                assetGroups.style('display', d => 
                    activeMOAs.has(d.moa) ? 'block' : 'none'
                );
            }}
            
            // Export functions
            function exportSVG() {{
                const svgData = document.getElementById('bullseye-chart').outerHTML;
                const blob = new Blob([svgData], {{type: 'image/svg+xml'}});
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = 'bullseye-chart.svg';
                link.click();
                URL.revokeObjectURL(url);
            }}
            
            function exportPNG() {{
                const svgElement = document.getElementById('bullseye-chart');
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                
                canvas.width = width;
                canvas.height = height;
                
                // Create a white background
                ctx.fillStyle = 'white';
                ctx.fillRect(0, 0, width, height);
                
                // Convert SVG to image
                const svgString = new XMLSerializer().serializeToString(svgElement);
                const svg = new Blob([svgString], {{type: 'image/svg+xml'}});
                const url = URL.createObjectURL(svg);
                const img = new Image();
                
                img.onload = function() {{
                    ctx.drawImage(img, 0, 0);
                    canvas.toBlob(function(blob) {{
                        const link = document.createElement('a');
                        link.href = URL.createObjectURL(blob);
                        link.download = 'bullseye-chart.png';
                        link.click();
                    }});
                    URL.revokeObjectURL(url);
                }};
                
                img.src = url;
            }}
            
            // Add zoom and pan functionality
            const zoom = d3.zoom()
                .scaleExtent([0.5, 3])
                .on('zoom', function(event) {{
                    g.attr('transform', event.transform);
                }});
            
            svg.call(zoom);
            
            // Add double-click to reset zoom
            svg.on('dblclick.zoom', function() {{
                svg.transition()
                    .duration(750)
                    .call(zoom.transform, d3.zoomIdentity);
            }});
        </script>
    </body>
    </html>
    """
    
    # Return the component
    return components.html(component_html, height=800, scrolling=False)

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
        if st.button("📁 Upload Your Data", use_container_width=True):
            st.session_state.page_state = 'upload'
            st.rerun()
        
        st.markdown("---")
        
        # Show sample data preview
        st.markdown("### Sample Data Preview")
        st.dataframe(st.session_state.assets_data, use_container_width=True)

# Upload Page
elif st.session_state.page_state == 'upload':
    st.title("📁 Upload Your Data")
    
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
        st.subheader("📁 Upload File")
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
                                st.success("📈 Data uploaded successfully!")
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
        st.title("⚙️ Chart Settings")
        
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
        
        if st.button("📁 Upload New Data", use_container_width=True):
            st.session_state.page_state = 'upload'
            st.rerun()
        
        if st.button("🏠 Back to Landing", use_container_width=True):
            st.session_state.page_state = 'landing'
            st.rerun()
    
    # Main content area
    st.title("🎯 Interactive Bulls Eye Asset Portfolio")
    
    # Create and display D3.js chart
    create_d3_bullseye_chart(
        st.session_state.assets_data,
        segment_column=segment_column,
        max_segments=max_segments,
        font_settings=st.session_state.font_settings,
        moa_colors=st.session_state.moa_colors
    )
    
    # Add instructions
    with st.expander("📖 How to Use"):
        st.markdown("""
        - **Hover** over any asset dot to see detailed information
        - **Click** on MOA items in the legend to show/hide assets
        - **Scroll** to zoom in/out of the chart
        - **Drag** to pan around when zoomed
        - **Double-click** to reset the zoom
        - Use the **Export** buttons to save as SVG or PNG
        """)

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
        csv_data = st.session_state.assets_data.to_csv(index=False)
        
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
