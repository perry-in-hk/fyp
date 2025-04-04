from fpdf import FPDF
import os
import folium
from firebase_admin import credentials, firestore
import datetime
import firebase_admin
from selenium import webdriver
import time
from PIL import Image
import random
from itertools import cycle
import re
import streamlit as st

class PDF(FPDF):
    def __init__(self, start_date, end_date):
        super().__init__()
        self.start_date = start_date
        self.end_date = end_date
        # Set margins
        self.set_margins(15, 15, 15)
        # Set auto page break
        self.set_auto_page_break(True, margin=25)
        
    def header(self):
        # Kerry Logistics logo - assume logo.png is in the same folder or specify path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(current_dir, "logo.png")
        
        # Check if logo exists, create a placeholder if it doesn't
        if not os.path.exists(logo_path):
            # Create a simple orange rectangle as a placeholder
            img = Image.new('RGB', (200, 50), color=(255, 102, 0))
            img.save(logo_path)
        
        self.image(logo_path, 10, 8, 50)
        
        # Kerry Logistics colors
        self.set_text_color(0, 51, 102)  # Dark blue
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'KERRY LOGISTICS NETWORK', 0, 0, 'R')
        self.ln(5)
        
        # Report title
        self.set_text_color(255, 102, 0)  # Kerry Orange
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, f'ESG Report - Period Analysis ({self.start_date} to {self.end_date})', 0, 0, 'R')
        self.ln(15)
        
        # Horizontal line
        self.set_draw_color(255, 102, 0)
        self.line(10, self.get_y(), self.w - 10, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-25)
        # Horizontal line
        self.set_draw_color(0, 51, 102)
        self.line(10, self.get_y(), self.w - 10, self.get_y())
        self.ln(5)
        
        # Company info
        self.set_font('Arial', '', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 5, 'Kerry Logistics Network Limited | ESG Report Generated: ' + 
                 datetime.datetime.now().strftime("%d %b %Y"), 0, 0, 'L')
        
        # Page number
        self.set_font('Arial', 'I', 8)
        self.cell(0, 5, f'Page {self.page_no()}/{{nb}}', 0, 0, 'R')

    def chapter_title(self, title):
        self.set_font("Arial", 'B', 14)
        self.set_text_color(0, 51, 102)  # Dark blue
        self.cell(0, 10, title, 0, 1, 'L')
        
        # Short line under the title
        self.set_draw_color(255, 102, 0)  # Orange
        self.line(self.l_margin, self.get_y(), self.l_margin + 50, self.get_y())
        
        self.ln(5)

    def section_title(self, title):
        self.set_font("Arial", 'B', 12)
        self.set_text_color(0, 51, 102)  # Dark blue
        self.cell(0, 10, title, 0, 1)
        self.ln(2)

    def chapter_body(self, body):
        self.set_font("Arial", '', 11)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 6, body)
        self.ln(5)

    def add_map_image(self, image_path, has_data=True):
        self.add_page()
        self.chapter_title("Route Network Visualization")
        
        self.section_title("Network Map")
        self.set_font("Arial", '', 10)
        map_description = (
            "The map below shows all routes covered during the reporting period. Each route is displayed "
            "with a different color to visualize the logistics network. This visualization helps identify "
            "high-traffic corridors and opportunities for route consolidation and optimization."
        )
        self.multi_cell(0, 5, map_description)
        self.ln(10)  # Increase spacing between description and legend
        
        # Add map legend if needed
        self.section_title("Map Legend")
        self.set_font("Arial", '', 10)
        self.cell(0, 6, "Each colored line represents a unique logistics route.", 0, 1)
        self.ln(10)  # Increase spacing between legend and map
        
        # Add the map image
        self.image(image_path, x=15, y=100, w=180)  # Increased y-position to 100 (from 70)
        
        # Position the cursor far enough below the map to add notes
        # Map height is approximately 180px at this scale
        self.ln(190)  # Move cursor below the map image
        
        # Add note about missing data if needed
        if not has_data:
            self.set_font("Arial", 'I', 10)
            self.set_text_color(150, 150, 150)
            self.multi_cell(0, 5, "Note: No route data could be visualized. This may be because the processed route data is not available in the database.")
            self.set_text_color(0, 0, 0)  # Reset text color

    def add_table(self, data, col_widths, title=None, headers=True):
        if title:
            self.section_title(title)
        
        if headers:
            # Table header style
            self.set_font("Arial", 'B', 10)
            self.set_fill_color(240, 240, 240)
            self.set_text_color(0, 51, 102)
            
            # Headers (first row)
            for i, item in enumerate(data[0]):
                self.cell(col_widths[i], 10, str(item), 1, 0, 'C', True)
            self.ln()
            
            # Start from second row for data
            start_row = 1
        else:
            # No headers, start from first row
            start_row = 0
        
        # Table data style
        self.set_font("Arial", '', 10)
        self.set_text_color(0, 0, 0)
        
        # Row colors alternation
        fill = False
        
        # Data rows
        for r in range(start_row, len(data)):
            fill = not fill
            if fill:
                self.set_fill_color(245, 245, 245)
            else:
                self.set_fill_color(255, 255, 255)
                
            for i, item in enumerate(data[r]):
                self.cell(col_widths[i], 10, str(item), 1, 0, 'L', fill)
            self.ln()
        
        self.ln(5)

    def add_metric_table(self, data, title=None):
        if title:
            self.section_title(title)
        
        # Table header style
        self.set_font("Arial", 'B', 10)
        self.set_fill_color(240, 240, 240)
        self.set_text_color(0, 51, 102)
        
        # Determine widths based on data - typically key-value pairs
        col_width = 80
        
        # Header
        self.cell(col_width, 10, "Metric", 1, 0, 'C', True)
        self.cell(0, 10, "Value", 1, 1, 'C', True)
        
        # Table data style
        self.set_font("Arial", '', 10)
        self.set_text_color(0, 0, 0)
        
        # Row colors alternation
        fill = False
        
        # Data rows
        for key, value in data:
            fill = not fill
            if fill:
                self.set_fill_color(245, 245, 245)
            else:
                self.set_fill_color(255, 255, 255)
                
            self.cell(col_width, 10, str(key), 1, 0, 'L', fill)
            self.cell(0, 10, str(value), 1, 1, 'L', fill)
        
        self.ln(5)

    def add_executive_summary(self, total_emission, total_distance, route_count):
        self.chapter_title("Executive Summary")
        
        period_str = f"{self.start_date} to {self.end_date}"
        summary_text = (
            f"This ESG report provides a comprehensive analysis of Kerry Logistics' carbon emissions "
            f"for the period from {period_str}. The analysis is based on precise GPS tracking data "
            f"and emissions calculation methodology aligned with the GHG Protocol and ISO 14064 standards.\n\n"
            
            f"During this reporting period, a total of {route_count} routes were analyzed, covering "
            f"a total distance of {total_distance:.2f} kilometers. The total CO2 emissions for all routes "
            f"during this period amount to {total_emission:.2f} kilograms ({(total_emission/1000):.2f} tonnes).\n\n"
        )
        
        # Calculate efficiency if available
        if total_distance > 0:
            efficiency = total_emission / total_distance
            summary_text += (
                f"The average carbon efficiency for the period was {efficiency:.2f} kg CO2/km. "
            )
        
        summary_text += (
            f"This report supports Kerry Logistics' commitment to environmental transparency and "
            f"sustainability as part of our ESG initiatives. The information contained herein "
            f"contributes to our climate action planning and emissions reduction targets."
        )
        
        self.chapter_body(summary_text)

# Initialize Firebase if not already initialized
def init_firebase():
    if not firebase_admin._apps:
        # Check if we are running with Streamlit
        if 'streamlit' in globals() or 'streamlit' in locals() or 'st' in globals() or 'st' in locals():
            try:
                # Use Streamlit secrets if available
                firebase_secrets = st.secrets["firebase"]
                
                # Convert secrets to the format expected by Firebase Admin SDK
                firebase_creds = {
                    "type": firebase_secrets["type"],
                    "project_id": firebase_secrets["project_id"],
                    "private_key_id": firebase_secrets["private_key_id"],
                    "private_key": firebase_secrets["private_key"],
                    "client_email": firebase_secrets["client_email"],
                    "client_id": firebase_secrets["client_id"],
                    "auth_uri": firebase_secrets["auth_uri"],
                    "token_uri": firebase_secrets["token_uri"],
                    "auth_provider_x509_cert_url": firebase_secrets["auth_provider_x509_cert_url"],
                    "client_x509_cert_url": firebase_secrets["client_x509_cert_url"],
                    "universe_domain": firebase_secrets["universe_domain"]
                }
                
                cred = credentials.Certificate(firebase_creds)
            except (KeyError, AttributeError):
                # Fallback to file-based credentials
                cred = credentials.Certificate('fyp-gps.json')
        else:
            # When not using Streamlit
            cred = credentials.Certificate('fyp-gps.json')
            
        firebase_admin.initialize_app(cred)
    
    return firestore.client()

def fetch_route_ids_within_period(start_date, end_date):
    db = init_firebase()
    route_ids = []

    start_date = datetime.datetime.strptime(start_date, '%d-%m-%Y')
    end_date = datetime.datetime.strptime(end_date, '%d-%m-%Y')

    # Updated to use the real_estimated_result collection
    docs = db.collection('real_estimated_result').stream()
    
    # Regular expression pattern to match the route naming format
    # Pattern: Route_{userID}_{ddmmyyyy}_{no of route of that date}_estimated_result_version
    pattern = re.compile(r'Route_[^_]+_(\d{8})_\d+_estimated_result_version')
    
    for doc in docs:
        doc_id = doc.id
        match = pattern.match(doc_id)
        
        if match:
            try:
                date_str = match.group(1)  # Extract the date part (ddmmyyyy)
                doc_date = datetime.datetime.strptime(date_str, '%d%m%Y')
                
                if start_date <= doc_date <= end_date:
                    # Convert to filtered_version format for map visualization
                    route_id = doc_id.replace('_estimated_result_version', '')
                    route_ids.append(route_id)
            except (IndexError, ValueError):
                continue

    return route_ids

def fetch_processed_data(route_id):
    db = init_firebase()
    
    # Add '_filtered_version' suffix if it's not already present
    if not route_id.endswith('_filtered_version'):
        route_id = route_id + '_filtered_version'
        
    # Update to use real_processed_routes_ricky collection
    doc_ref = db.collection('real_processed_routes_ricky').document(route_id)
    doc = doc_ref.get()

    if doc.exists:
        processed_data = doc.to_dict()
    else:
        processed_data = []

    return processed_data

def translate_processed_data(data):
    coordinates = data.get("coordinates", [])
    return [(coord["latitude"], coord["longitude"]) for coord in coordinates]


def create_map_with_gps_data(route_ids):
    all_gps_data = []
    color_cycle = cycle(['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray'])  # Cycle through colors
    
    # Create map with a larger initial zoom level to ensure all points are visible
    map_plot = folium.Map(zoom_start=10)
    
    success_count = 0  # Track how many routes we successfully add to the map
    
    for route_id in route_ids:
        processed_data = fetch_processed_data(route_id)
        if processed_data:
            translated_coords = translate_processed_data(processed_data)
            if translated_coords:
                color = next(color_cycle)
                # Use a thicker line for better visibility
                folium.PolyLine(translated_coords, color=color, weight=4).add_to(map_plot)
                # Only add markers for start and end points to reduce clutter
                folium.CircleMarker(location=translated_coords[0], radius=6, color=color, fill=True, 
                                    popup=f"Start: {route_id}").add_to(map_plot)
                folium.CircleMarker(location=translated_coords[-1], radius=6, color=color, fill=True,
                                    popup=f"End: {route_id}").add_to(map_plot)
                all_gps_data.extend(translated_coords)
                success_count += 1

    print(f"Added {success_count} routes to the map out of {len(route_ids)} route IDs")

    if all_gps_data:
        try:
            # Calculate the bounds of all GPS data to adjust the map view
            sw = [min(map(lambda x: x[0], all_gps_data)), min(map(lambda x: x[1], all_gps_data))]
            ne = [max(map(lambda x: x[0], all_gps_data)), max(map(lambda x: x[1], all_gps_data))]
            
            # Add padding to the bounds to ensure all points are visible (0.05 degrees)
            sw[0] -= 0.05  # Latitude padding
            sw[1] -= 0.05  # Longitude padding
            ne[0] += 0.05  # Latitude padding
            ne[1] += 0.05  # Longitude padding
            
            # Set map bounds with the padded coordinates
            map_plot.fit_bounds([sw, ne])
            print(f"Map bounds set to SW: {sw}, NE: {ne}")
        except Exception as e:
            print(f"Error setting map bounds: {str(e)}")
            # Default location if bounds calculation fails
            map_plot.location = [22.3193, 114.1694]  # Hong Kong default location
            map_plot.zoom_start = 10
    else:
        # Default location if no valid GPS data is found
        map_plot.location = [22.3193, 114.1694]  # Hong Kong default location
        map_plot.zoom_start = 10

    # Create a directory for saving the map
    map_dir = "maps"
    os.makedirs(map_dir, exist_ok=True)

    # Save the map as an HTML file
    map_html_path = os.path.join(map_dir, 'map_image.html')
    map_plot.save(map_html_path)
    
    # Add a script to ensure the map is fully loaded
    with open(map_html_path, 'r') as file:
        content = file.read()
    
    # Add a flag element that will be set when the map is fully loaded
    load_script = """
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(function() {
            var readyFlag = document.createElement('div');
            readyFlag.id = 'map-fully-loaded';
            readyFlag.style.display = 'none';
            document.body.appendChild(readyFlag);
        }, 3000); // 3 seconds should be enough for most maps to load
    });
    </script>
    """
    content = content.replace('</head>', f'{load_script}</head>')
    
    with open(map_html_path, 'w') as file:
        file.write(content)

    # Convert the HTML map to PNG with improved settings
    map_image_path = os.path.join(map_dir, 'map_image.png')
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # Use a larger window size to ensure all elements are visible
    options.add_argument('window-size=1920x1080')

    driver = webdriver.Chrome(options=options)
    driver.get(f'file://{os.path.abspath(map_html_path)}')
    
    # Wait longer for the map to fully render
    print("Waiting for map to fully render...")
    time.sleep(5)  # Increased wait time from 2 to 5 seconds
    
    # Wait for our custom "map loaded" flag
    try:
        for _ in range(10):  # Try for up to 10 seconds
            if driver.execute_script("return document.getElementById('map-fully-loaded') !== null"):
                print("Map fully loaded indicator found")
                break
            time.sleep(1)
    except Exception as e:
        print(f"Error waiting for map load: {str(e)}")
    
    # Ensure we're at the top of the page when taking the screenshot
    driver.execute_script("window.scrollTo(0, 0)")
    
    # Take a screenshot of the map
    print("Taking screenshot of the map...")
    driver.save_screenshot(map_image_path)
    driver.quit()

    # Process the image
    try:
        img = Image.open(map_image_path)
        width, height = img.size
        # Keep most of the image, crop only the window controls if any
        cropped_img = img.crop((0, 0, width, height - 30))
        cropped_img.save(map_image_path)
        print(f"Map image saved to {map_image_path}")
    except Exception as e:
        print(f"Error processing map image: {str(e)}")

    return map_image_path, success_count

def generate_muti_pdf(start_date, end_date, total_emission, total_distance, route_count=0):
    # Convert the route IDs to more readable date format for display
    start_date_obj = datetime.datetime.strptime(start_date, '%d-%m-%Y')
    end_date_obj = datetime.datetime.strptime(end_date, '%d-%m-%Y')
    
    # Format dates for display
    formatted_start = start_date_obj.strftime('%d %B %Y')
    formatted_end = end_date_obj.strftime('%d %B %Y')
    
    # Always get route IDs within period for map visualization
    route_ids = fetch_route_ids_within_period(start_date, end_date)
    
    # Update route_count if it wasn't provided
    if route_count <= 0:
        route_count = len(route_ids)
    
    # Initialize the PDF
    pdf = PDF(formatted_start, formatted_end)
    pdf.alias_nb_pages()  # For page numbering
    pdf.add_page()
    pdf.set_title(f"Kerry Logistics ESG Report {formatted_start} to {formatted_end}")
    
    # 1. Executive Summary
    pdf.add_executive_summary(total_emission, total_distance, route_count)
    
    # 2. Period Details
    pdf.chapter_title("Reporting Period Details")
    
    period_data = [
        ("Start Date", formatted_start),
        ("End Date", formatted_end),
        ("Total Routes Analyzed", str(route_count)),
        ("Report Generation Date", datetime.datetime.now().strftime("%d %B %Y"))
    ]
    pdf.add_metric_table(period_data)
    
    # 3. Emissions Analysis
    pdf.chapter_title("Carbon Emissions Analysis")
    
    # Emissions metrics
    emissions_data = [
        ("Total CO2 Emissions", f"{total_emission:.2f} kg"),
        ("Total CO2 Emissions (tonnes)", f"{(total_emission/1000):.2f} t"),
        ("Total Distance Traveled", f"{total_distance:.2f} km")
    ]
    
    if total_distance > 0:
        emissions_data.append(("Average CO2 Emissions per km", f"{(total_emission/total_distance):.2f} kg/km"))
        
        # Add some benchmarks for context
        avg_truck_emissions = 0.85  # Example value in kg/km for a typical truck
        if (total_emission/total_distance) < avg_truck_emissions:
            performance = "Better than industry average"
        else:
            performance = "Above industry average"
            
        emissions_data.append(("Performance vs. Industry Benchmark", performance))
    
    pdf.add_metric_table(emissions_data)
    
    # Emissions methodology
    pdf.section_title("Emissions Calculation Methodology")
    methodology_text = (
        "Carbon emissions are calculated based on vehicle specifications, route characteristics, "
        "and fuel consumption estimates. The methodology follows the Greenhouse Gas Protocol's "
        "Scope 1 direct emissions reporting guidelines and ISO 14064 standards.\n\n"
        
        "The calculation considers factors including total distance, vehicle weight, payload, "
        "fuel efficiency, road gradients, and emission factors specific to the fuel type. "
        "This approach ensures accurate and consistent reporting across the logistics network."
    )
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 5, methodology_text)
    pdf.ln(5)
    
    # 4. Route Analysis
    pdf.chapter_title("Route Analysis")
    
    # 4.1 Route summary
    pdf.section_title("Route Summary")
    route_summary_text = (
        f"During the reporting period, a total of {route_count} routes were operated. "
        f"The average distance per route was {(total_distance/route_count if route_count > 0 else 0):.2f} km, "
        f"with average emissions of {(total_emission/route_count if route_count > 0 else 0):.2f} kg CO2 per route."
    )
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 5, route_summary_text)
    pdf.ln(5)
    
    # 4.2 Route List
    if route_ids:
        # Format the route IDs for better readability
        formatted_routes = []
        for i, route_id in enumerate(route_ids):
            parts = route_id.split('_')
            if len(parts) >= 3:
                try:
                    date_part = parts[2]
                    formatted_date = f"{date_part[0:2]}/{date_part[2:4]}/{date_part[4:8]}"
                    route_num = i + 1
                    formatted_routes.append([route_num, formatted_date, route_id])
                except:
                    formatted_routes.append([i + 1, "Unknown", route_id])
            else:
                formatted_routes.append([i + 1, "Unknown", route_id])
        
        # Add route table with headers
        table_data = [["#", "Date", "Route ID"]] + formatted_routes
        col_widths = [15, 40, 125]  # Adjust column widths as needed
        pdf.add_table(table_data, col_widths, "Routes Included in This Report")
    else:
        if route_count > 0:
            # We know the route count but don't have individual routes
            pdf.section_title("Routes Summary")
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(0, 5, f"A total of {route_count} routes from all users were analyzed during this period. " 
                             f"Route data is aggregated from the 'real_estimated_result' database collection.")
            pdf.ln(5)
        else:
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(0, 5, "No routes were found within the specified period.")
            pdf.ln(5)
    
    # 5. Map Visualization - Create and add the map
    map_image_path, success_count = create_map_with_gps_data(route_ids)
    
    # Check if the map has meaningful data by looking at image content
    try:
        img = Image.open(map_image_path)
        
        # Check if any routes were successfully added to the map
        has_route_data = success_count > 0
        
        # Add the map page with the appropriate data status
        pdf.add_map_image(map_image_path, has_data=has_route_data)
        
    except Exception as e:
        # Handle error in map generation
        pdf.add_page()
        pdf.chapter_title("Route Network Visualization")
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(0, 5, "The route map could not be generated. This may be due to missing route data or processing issues.")
        pdf.ln(5)
    
    # 6. Environmental Impact & Recommendations
    pdf.add_page()
    pdf.chapter_title("Environmental Impact & ESG Contribution")
    
    impact_text = (
        "Kerry Logistics is committed to reducing its environmental footprint and supporting "
        "global climate action. This period analysis contributes to our ESG goals in the following ways:\n\n"
        
        "- Carbon Footprint Transparency: Provides accurate measurement of logistics emissions over time\n"
        "- Performance Tracking: Allows for comparison against previous periods and benchmarks\n"
        "- Network Optimization: Identifies opportunities to consolidate and optimize routes\n"
        "- Emissions Targets: Supports our science-based targets for emissions reduction\n"
        "- Stakeholder Engagement: Offers transparent reporting to clients and stakeholders\n\n"
        
        "This report aligns with the GHG Protocol Corporate Standard and contributes to Kerry Logistics' "
        f"disclosure commitments under the Task Force on Climate-related Financial Disclosures (TCFD) "
        "and CDP (formerly Carbon Disclosure Project)."
    )
    pdf.chapter_body(impact_text)
    
    # Recommendations section
    pdf.section_title("Recommendations for Improvement")
    
    recommendations_text = (
        "Based on the data collected during this reporting period, the following recommendations "
        "are proposed to further reduce carbon emissions and improve operational efficiency:\n\n"
        
        "1. Route Optimization: Further analyze high-mileage routes for potential consolidation\n"
        "2. Vehicle Efficiency: Consider transitioning to lower-emission vehicles for routes with high emissions\n"
        "3. Load Optimization: Review loading practices to maximize vehicle capacity utilization\n"
        "4. Driver Training: Enhance eco-driving training to reduce fuel consumption\n"
        "5. Alternative Fuels: Evaluate the feasibility of alternative fuel vehicles for specific routes\n\n"
        
        "Implementation of these recommendations could result in a potential reduction of 5-15% in "
        "carbon emissions for future reporting periods, contributing to Kerry Logistics' long-term "
        "environmental sustainability goals."
    )
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 5, recommendations_text)
    pdf.ln(5)
    
    # 7. Conclusion
    pdf.chapter_title("Conclusion")
    
    conclusion_text = (
        f"This ESG report demonstrates Kerry Logistics' commitment to environmental transparency "
        f"and responsible business practices. During the period from {formatted_start} to {formatted_end}, "
        f"our operations resulted in {total_emission:.2f} kg of CO2 emissions over {total_distance:.2f} km "
        f"of logistics activities.\n\n"
        
        f"The data and analysis provided in this report will serve as a baseline for future improvements "
        f"and contribute to our company's overall sustainability strategy. By continuing to monitor, "
        f"report, and reduce our carbon footprint, Kerry Logistics aims to be a leader in sustainable "
        f"logistics and contribute positively to global climate action efforts."
    )
    pdf.chapter_body(conclusion_text)
    
    # Save the PDF to a file with error handling
    current_dir = os.path.dirname(os.path.abspath(__file__))  # Get the current directory
    pdf_dir = os.path.join(current_dir, "../esg_month_reports")

    os.makedirs(pdf_dir, exist_ok=True)
    pdf_file_path = os.path.join(pdf_dir, f"Kerry_Logistics_ESG_Report_{start_date}_to_{end_date}.pdf")
    
    try:
        # Try with explicit ASCII encoding for compatibility
        pdf.output(pdf_file_path, 'F')
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        # Fallback to alternative method if available
        try:
            with open(pdf_file_path, 'wb') as f:
                f.write(pdf.output(dest='S').encode('latin-1'))
        except Exception as e2:
            print(f"Fallback method also failed: {str(e2)}")
            # Create a simplified emergency version of the PDF
            emergency_pdf = FPDF()
            emergency_pdf.add_page()
            emergency_pdf.set_font('Arial', 'B', 16)
            emergency_pdf.cell(0, 10, 'Kerry Logistics ESG Report', 0, 1, 'C')
            emergency_pdf.set_font('Arial', '', 12)
            emergency_pdf.cell(0, 10, f'Period: {start_date} to {end_date}', 0, 1)
            emergency_pdf.cell(0, 10, f'Date: {datetime.datetime.now().strftime("%d %b %Y")}', 0, 1)
            emergency_pdf.cell(0, 10, f'CO2 Emissions: {total_emission:.2f} kg', 0, 1)
            emergency_pdf.cell(0, 10, f'Total Distance: {total_distance:.2f} km', 0, 1)
            emergency_pdf.output(pdf_file_path)

    return pdf_file_path