"""
UI Styling for Kerry Logistics Carbon Emission Tracker
- Dark Theme based on Kerry Logistics colors
- Provides consistent styling across the application
"""

import streamlit as st

# Kerry Logistics Colors
KERRY_ORANGE = "#FF6600"
KERRY_DARK_BLUE = "#003366"
KERRY_BLUE = "#0066CC"
KERRY_LIGHT_BLUE = "#66CCFF"

# Dark Theme Colors - More high-tech
BACKGROUND_COLOR = "#0A0F16"  # Darker blue-black
SURFACE_COLOR = "#121920"     # Dark blue-gray
CARD_COLOR = "#1A2530"        # Midnight blue
TEXT_COLOR = "#E0E7FF"        # Slightly blue-tinted white
TEXT_SECONDARY_COLOR = "#8A9AB0"  # Muted blue-gray
DIVIDER_COLOR = "#2A3A4A"     # Deep blue-gray
ACCENT_COLOR = "#00C8FF"      # Bright cyan accent

# Route Colors
ORIGINAL_ROUTE_COLOR = "#FF6600"  # Kerry Orange
PROCESSED_ROUTE_COLOR = "#00C8FF"  # Bright cyan
ANGLE_FILTERED_COLOR = "#00E676"   # Bright green

def apply_custom_styles():
    """Apply custom CSS to create a dark theme with Kerry Logistics colors"""
    
    # Main Styles
    st.markdown("""
    <style>
        /* Main Background and Text */
        .stApp {
            background-color: """ + BACKGROUND_COLOR + """;
            color: """ + TEXT_COLOR + """;
            background-image: 
                radial-gradient(circle at 100% 0%, rgba(0, 102, 204, 0.08) 0%, transparent 25%),
                radial-gradient(circle at 0% 100%, rgba(255, 102, 0, 0.08) 0%, transparent 25%);
            background-attachment: fixed;
        }
        
        /* Compact layout - reduce spacing to minimize scrolling */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 0;
            max-width: 95%;  /* Use more screen width */
        }
        [data-testid="stVerticalBlock"] {
            gap: 0.8rem;
        }
        
        /* Fancy Glassmorphism for cards and widgets */
        .stBlock, .element-container, .stDataFrame, .stMetric, div[data-testid="stMetricValue"] {
            backdrop-filter: blur(6px);
        }
        
        /* Glowing accent dividers and borders */
        hr {
            border-color: """ + DIVIDER_COLOR + """;
            box-shadow: 0 0 8px """ + KERRY_LIGHT_BLUE + """30;
        }
        
        /* Sidebar Styling - More high-tech */
        [data-testid="stSidebar"] {
            background-color: """ + SURFACE_COLOR + """;
            border-right: 1px solid """ + DIVIDER_COLOR + """;
            box-shadow: 2px 0 8px rgba(0,0,0,0.3);
            background-image: 
                linear-gradient(180deg, """ + SURFACE_COLOR + """ 0%, """ + SURFACE_COLOR + """ 85%, rgba(0, 102, 204, 0.15) 100%);
        }
        
        /* Headers with futuristic styling */
        h1, h2, h3 {
            color: """ + TEXT_COLOR + """;
            letter-spacing: 0.05em;
        }
        h1 {
            font-size: 2.2rem;
            font-weight: 700;
            border-bottom: 2px solid """ + KERRY_ORANGE + """;
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
            position: relative;
            text-shadow: 0 0 10px """ + KERRY_ORANGE + """50;
        }
        h1:after {
            content: '';
            position: absolute;
            width: 30%;
            height: 2px;
            bottom: -2px;
            left: 0;
            background: linear-gradient(90deg, """ + KERRY_ORANGE + """, transparent);
            box-shadow: 0 0 8px """ + KERRY_ORANGE + """;
        }
        h2 {
            font-size: 1.8rem;
            font-weight: 600;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            color: """ + KERRY_LIGHT_BLUE + """;
            text-shadow: 0 0 5px """ + KERRY_LIGHT_BLUE + """40;
        }
        h3 {
            font-size: 1.4rem;
            font-weight: 500;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
            color: """ + ACCENT_COLOR + """;
        }
        
        /* Neon effect for highlighted text */
        .highlight {
            color: """ + KERRY_ORANGE + """;
            text-shadow: 0 0 5px """ + KERRY_ORANGE + """70;
        }
        
        /* Cards for metrics and data - more high-tech with glassmorphism */
        .metric-card {
            background-color: """ + CARD_COLOR + """88;
            background: linear-gradient(135deg, """ + CARD_COLOR + """AA, """ + CARD_COLOR + """77);
            padding: 1.2rem;
            border-radius: 10px;
            border-left: 3px solid """ + KERRY_ORANGE + """;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), 0 0 10px """ + KERRY_ORANGE + """30;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
            margin-bottom: 1rem;
        }
        .metric-card:hover {
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4), 0 0 15px """ + KERRY_ORANGE + """50;
            transform: translateY(-2px);
        }
        .metric-value {
            font-size: 2.2rem;
            font-weight: 700;
            color: """ + KERRY_LIGHT_BLUE + """;
            text-shadow: 0 0 8px """ + KERRY_LIGHT_BLUE + """50;
            margin-bottom: 0.5rem;
        }
        .metric-label {
            font-size: 0.95rem;
            color: """ + TEXT_SECONDARY_COLOR + """;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }
        
        /* Multi Routes Specific Styling */
        .date-selector-container {
            background: linear-gradient(135deg, """ + CARD_COLOR + """AA, """ + CARD_COLOR + """77);
            padding: 1.2rem;
            border-radius: 10px;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(6px);
        }
        
        .date-label {
            font-size: 0.9rem;
            color: """ + KERRY_ORANGE + """;
            font-weight: 500;
            margin-bottom: 0.3rem;
            letter-spacing: 0.05em;
        }
        
        .multi-metrics-container {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        
        .analytics-container {
            background: linear-gradient(135deg, """ + CARD_COLOR + """DD, """ + CARD_COLOR + """BB);
            padding: 1rem 1.5rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            position: relative;
            overflow: hidden;
        }
        
        .analytics-container:before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 3px;
            background: linear-gradient(90deg, """ + KERRY_ORANGE + """ 0%, """ + KERRY_LIGHT_BLUE + """ 100%);
        }
        
        .period-info {
            background-color: """ + SURFACE_COLOR + """AA;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        
        .info-label {
            color: """ + TEXT_SECONDARY_COLOR + """;
            margin-right: 0.5rem;
            font-size: 0.9rem;
        }
        
        .info-value {
            color: """ + TEXT_COLOR + """;
            font-weight: 500;
            margin-right: 1.5rem;
        }
        
        .performance-indicators {
            display: flex;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        
        .indicator-card {
            background: linear-gradient(135deg, rgba(26, 37, 48, 0.6), rgba(26, 37, 48, 0.4));
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(4px);
            border-top: 2px solid """ + KERRY_BLUE + """;
        }
        
        .indicator-title {
            font-size: 0.9rem;
            color: """ + TEXT_SECONDARY_COLOR + """;
            margin-bottom: 0.5rem;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }
        
        .indicator-value {
            font-size: 1.8rem;
            font-weight: 600;
            color: """ + KERRY_LIGHT_BLUE + """;
            text-shadow: 0 0 5px """ + KERRY_LIGHT_BLUE + """40;
        }
        
        .export-options {
            background: linear-gradient(135deg, """ + CARD_COLOR + """AA, """ + CARD_COLOR + """77);
            padding: 1rem 1.5rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        
        .page-subtitle {
            color: """ + KERRY_ORANGE + """;
            font-weight: 600;
            margin-bottom: 1.5rem;
            text-align: center;
        }
        
        .page-subtitle h2 {
            margin-top: 0;
            text-shadow: 0 0 10px """ + KERRY_ORANGE + """30;
        }
        
        /* Metrics row layout */
        .metrics-row {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        
        /* Compact widgets */
        .compact-widget {
            margin-bottom: 0.5rem;
        }
        .compact-widget label {
            margin-bottom: 0;
        }
        
        /* Database badges */
        .db-badge {
            display: inline-block;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            margin-top: 5px;
            margin-bottom: 5px;
            text-align: center;
            font-weight: 500;
            letter-spacing: 0.05em;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
        }
        .db-badge-warning {
            background-color: rgba(255, 102, 0, 0.2);
            border: 1px solid """ + KERRY_ORANGE + """;
            color: """ + KERRY_ORANGE + """;
        }
        .db-badge-info {
            background-color: rgba(102, 204, 255, 0.2);
            border: 1px solid """ + KERRY_LIGHT_BLUE + """;
            color: """ + KERRY_LIGHT_BLUE + """;
        }
        
        /* Buttons with hover effects and gradients */
        .stButton>button {
            background: linear-gradient(135deg, """ + KERRY_BLUE + """, #0057B3);
            color: white;
            border: none;
            padding: 0.6rem 1.2rem;
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.3s;
            box-shadow: 0 4px 10px rgba(0, 102, 204, 0.3);
        }
        .stButton>button:hover {
            background: linear-gradient(135deg, """ + KERRY_ORANGE + """, #E95D00);
            box-shadow: 0 6px 15px rgba(255, 102, 0, 0.4), 0 0 5px """ + KERRY_ORANGE + """50;
            transform: translateY(-2px);
        }
        
        /* Download Button */
        .stDownloadButton>button {
            background: linear-gradient(135deg, """ + KERRY_ORANGE + """, #E95D00);
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.3s;
            box-shadow: 0 4px 10px rgba(255, 102, 0, 0.3);
        }
        .stDownloadButton>button:hover {
            background: linear-gradient(135deg, """ + KERRY_BLUE + """, #0057B3);
            box-shadow: 0 6px 15px rgba(0, 102, 204, 0.4);
            transform: translateY(-2px);
        }
        
        /* Selectbox - more high-tech */
        .stSelectbox>div>div {
            background-color: """ + SURFACE_COLOR + """;
            border: 1px solid """ + DIVIDER_COLOR + """;
            border-radius: 6px;
        }
        .stSelectbox>div>div:hover {
            border-color: """ + KERRY_LIGHT_BLUE + """;
            box-shadow: 0 0 8px """ + KERRY_LIGHT_BLUE + """50;
        }
        
        /* Date input - make more compact */
        .stDateInput>div {
            margin-bottom: 0;
        }
        .stDateInput>div>div {
            background-color: """ + SURFACE_COLOR + """;
            border-radius: 6px;
            border: 1px solid """ + DIVIDER_COLOR + """;
        }
        .stDateInput>div>div:hover {
            border-color: """ + KERRY_LIGHT_BLUE + """;
            box-shadow: 0 0 8px """ + KERRY_LIGHT_BLUE + """50;
        }
        
        /* Radio buttons - high-tech style */
        div[role="radiogroup"] {
            border-radius: 8px;
            background-color: """ + SURFACE_COLOR + """;
            padding: 0.5rem;
            box-shadow: inset 0 2px 5px rgba(0, 0, 0, 0.2);
        }
        .stRadio > div {
            padding: 0.5rem;
            border-radius: 6px;
        }
        div[data-baseweb="radio"] {
            transition: all 0.2s ease;
        }
        div[data-baseweb="radio"]:hover {
            transform: translateY(-1px);
        }
        
        /* Data Tables - high-tech */
        .stDataFrame {
            background-color: """ + SURFACE_COLOR + """;
            padding: 0.5rem;
            border-radius: 10px;
            border: 1px solid """ + DIVIDER_COLOR + """;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }
        .stDataFrame table {
            border-collapse: separate;
            border-spacing: 0;
        }
        .stDataFrame th {
            background-color: """ + CARD_COLOR + """;
            color: """ + KERRY_LIGHT_BLUE + """;
        }
        
        /* Success/Info/Warning/Error - with glow effects */
        .stSuccess {
            background-color: rgba(0, 204, 102, 0.15);
            border-left: 3px solid #00CC66;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0, 204, 102, 0.2);
            backdrop-filter: blur(4px);
        }
        .stInfo {
            background-color: rgba(102, 204, 255, 0.15);
            border-left: 3px solid """ + KERRY_LIGHT_BLUE + """;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(102, 204, 255, 0.2);
            backdrop-filter: blur(4px);
        }
        .stWarning {
            background-color: rgba(255, 102, 0, 0.15);
            border-left: 3px solid """ + KERRY_ORANGE + """;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(255, 102, 0, 0.2);
            backdrop-filter: blur(4px);
        }
        .stError {
            background-color: rgba(255, 51, 51, 0.15);
            border-left: 3px solid #FF3333;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(255, 51, 51, 0.2);
            backdrop-filter: blur(4px);
        }
        
        /* Sidebar navigation - futuristic */
        .sidebar-nav {
            padding: 0.8rem;
            margin-bottom: 1.5rem;
            border-radius: 8px;
            background: linear-gradient(180deg, """ + CARD_COLOR + """99, """ + CARD_COLOR + """66);
            backdrop-filter: blur(10px);
            border: 1px solid """ + DIVIDER_COLOR + """;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        }
        
        /* Welcome message at top of sidebar */
        .sidebar-welcome {
            padding: 0.8rem;
            margin-bottom: 1rem;
            border-radius: 8px;
            background: linear-gradient(135deg, """ + CARD_COLOR + """AA, """ + CARD_COLOR + """77);
            backdrop-filter: blur(10px);
            border: 1px solid """ + DIVIDER_COLOR + """;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        }
        .sidebar-welcome h3 {
            color: """ + KERRY_ORANGE + """;
            margin: 0;
            font-size: 1.2rem;
            text-shadow: 0 0 5px """ + KERRY_ORANGE + """40;
        }
        
        /* Sidebar footer with logout - stronger styling to override Streamlit defaults */
        .sidebar-logout {
            position: fixed !important;
            bottom: 0 !important;
            left: 0 !important;
            width: 100% !important;
            max-width: 300px !important;
            border-top: 1px solid """ + DIVIDER_COLOR + """ !important;
            background: """ + BACKGROUND_COLOR + """ !important;
            background-image: linear-gradient(0deg, """ + SURFACE_COLOR + """, rgba(18, 25, 32, 0.95)) !important;
            backdrop-filter: blur(10px) !important;
            box-shadow: 0 -4px 10px rgba(0, 0, 0, 0.2) !important;
            z-index: 9999 !important;
            padding: 15px !important;
            margin: 0 !important;
        }
        
        /* Make the sidebar bottom padding extra large to accommodate the logout button */
        [data-testid="stSidebar"] > div:first-child {
            padding-bottom: 120px !important;
            overflow-y: auto !important;
        }
        
        /* Make the logout button full width and properly styled */
        .sidebar-logout button, .sidebar-logout div {
            width: 100% !important;
            margin: 0 !important;
        }
        
        /* Ensure iframe for logout doesn't mess up positioning */
        iframe[height="0"] {
            display: none !important;
        }
        
        /* Kerry Logistics branding */
        .kerry-logo {
            text-align: center;
            margin-bottom: 1.5rem;
            padding: 1.5rem 0;
        }
        .kerry-logo img {
            max-width: 80%;
            margin: 0 auto;
            filter: drop-shadow(0 0 10px rgba(255, 102, 0, 0.5));
        }
        
        /* Page title with Kerry colors and futuristic style */
        .page-title {
            color: """ + KERRY_ORANGE + """;
            font-weight: 700;
            margin-bottom: 2rem;
            background: linear-gradient(135deg, """ + SURFACE_COLOR + """DD, """ + SURFACE_COLOR + """88);
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
            border-bottom: 2px solid """ + KERRY_ORANGE + """;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3), 0 0 30px rgba(255, 102, 0, 0.1);
            backdrop-filter: blur(10px);
            position: relative;
            overflow: hidden;
        }
        .page-title:before {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, """ + KERRY_ORANGE + """, transparent);
            box-shadow: 0 0 20px 5px """ + KERRY_ORANGE + """;
            filter: blur(3px);
        }
        .page-title h1 {
            border: none;
            margin-bottom: 0;
            position: relative;
            z-index: 2;
            text-shadow: 0 0 15px """ + KERRY_ORANGE + """40;
        }
        
        /* Map container with futuristic design */
        .map-container {
            background: linear-gradient(135deg, """ + CARD_COLOR + """CC, """ + CARD_COLOR + """88);
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
            border: 1px solid """ + DIVIDER_COLOR + """;
            backdrop-filter: blur(10px);
            position: relative;
            overflow: hidden;
        }
        .map-container:after {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 30%;
            height: 5px;
            background: linear-gradient(90deg, transparent, """ + KERRY_ORANGE + """);
            filter: blur(2px);
        }
        
        /* Animated pulse effect for important metrics */
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(255, 102, 0, 0.4); }
            70% { box-shadow: 0 0 0 10px rgba(255, 102, 0, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 102, 0, 0); }
        }
        .metric-highlight {
            animation: pulse 2s infinite;
        }
        
        /* Add a high-tech grid overlay to the main background */
        .stApp:after {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                linear-gradient(rgba(10, 15, 22, 0) 95%, rgba(0, 102, 204, 0.08) 100%),
                linear-gradient(90deg, rgba(10, 15, 22, 0) 95%, rgba(0, 102, 204, 0.08) 100%);
            background-size: 20px 20px;
            pointer-events: none; /* so it doesn't block interaction */
            z-index: -1;
        }
        
        /* Slick loading animation */
        .stSpinner > div {
            border-color: """ + KERRY_ORANGE + """ transparent transparent !important;
            filter: drop-shadow(0 0 8px """ + KERRY_ORANGE + """50);
        }
        
        /* Ensure sidebar buttons are properly spaced */
        [data-testid="stSidebar"] .stButton {
            margin-bottom: 8px;  /* Reduced from 15px */
            position: relative;
            z-index: 1; /* Lower than logout but still positioned */
        }
        
        /* Extra space for the bottom button */
        [data-testid="stSidebar"] .stButton:last-child {
            margin-bottom: 60px; /* Reduced from 130px but still enough for logout */
        }
        
        /* Full width sidebar buttons */
        [data-testid="stSidebar"] .stButton button {
            width: 100%;
        }
        
        /* Compact styles for sidebar elements */
        [data-testid="stSidebar"] .stRadio > div {
            padding: 0.3rem !important;
        }
        
        [data-testid="stSidebar"] div[role="radiogroup"] {
            padding: 0.3rem;
            margin-bottom: 0.5rem;
        }
        
        [data-testid="stSidebar"] .stSelectbox {
            margin-bottom: 0.5rem;
        }
        
        [data-testid="stSidebar"] hr {
            margin-top: 0.5rem !important;
            margin-bottom: 0.5rem !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stHeader"] {
            margin-top: 0.5rem;
            margin-bottom: 0.5rem;
        }
    </style>
    """, unsafe_allow_html=True)

def show_kerry_header():
    """Display Kerry Logistics header with logo"""
    header_html = """
    <div class="page-title">
        <h1>Kerry Logistics Fleet Intelligence Tracker</h1>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

def display_metric_card(label, value, unit="", highlight=False):
    """Display a metric in a styled card"""
    highlight_class = "metric-highlight" if highlight else ""
    
    # Format the value to 2 decimal places if it's a distance in km
    if unit == "km" and isinstance(value, (int, float, str)):
        try:
            # Convert to float if it's a string representing a number
            if isinstance(value, str):
                value = float(value)
            # Format to 2 decimal places
            value = f"{value:.2f}"
        except (ValueError, TypeError):
            # Keep original value if it can't be converted
            pass
    
    # Clean HTML with properly closed tags
    metric_html = f"""
    <div class="metric-card {highlight_class}">
        <div class="metric-value">{value} {unit}</div>
        <div class="metric-label">{label}</div>
    </div>"""
    
    return metric_html

def display_metrics_row(metrics_dict, highlight_keys=None):
    """Display a row of metric cards
    
    Args:
        metrics_dict: A dictionary of {label: (value, unit)}
        highlight_keys: List of keys to highlight with pulsing animation
    """
    if highlight_keys is None:
        highlight_keys = []
    
    # Create a cleaner HTML structure with no extra divs
    metrics_html = '<div class="metrics-row">'
    for label, (value, unit) in metrics_dict.items():
        highlight = label in highlight_keys
        metrics_html += display_metric_card(label, value, unit, highlight)
    metrics_html += '</div>'
    st.markdown(metrics_html, unsafe_allow_html=True)

def get_marker_icon_color(marker_type):
    """Return the appropriate color for map markers based on the marker type"""
    if marker_type == "original":
        return ORIGINAL_ROUTE_COLOR
    elif marker_type == "processed":
        return PROCESSED_ROUTE_COLOR
    elif marker_type == "angle_filtered":
        return ANGLE_FILTERED_COLOR
    else:
        return KERRY_BLUE  # Default color 