import os
from fpdf import FPDF
from selenium import webdriver
import time
from geopy.distance import geodesic
import datetime
from PIL import Image

def save_map(map_obj, path):
    map_obj.save(path)
    return path

def capture_map_screenshot(map_path, screenshot_path):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    driver.get('file:///' + os.path.abspath(map_path))
    time.sleep(2)
    driver.save_screenshot(screenshot_path)
    driver.quit()

class PDF(FPDF):
    def __init__(self, route_name):
        # Use standard encoding with default fonts
        super().__init__()
        self.route_name = route_name
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
        self.cell(0, 10, 'ESG Report - Route Carbon Emissions Analysis', 0, 0, 'R')
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
        self.cell(0, 10, title, 0, 1)
        
        # Short line under the title
        self.set_draw_color(255, 102, 0)  # Orange
        self.line(self.l_margin, self.get_y(), self.l_margin + 50, self.get_y())
        
        self.ln(5)

    def section_title(self, title):
        self.set_font("Arial", 'B', 12)
        self.set_text_color(0, 51, 102)  # Dark blue
        self.cell(0, 10, title, 0, 1)
        self.ln(2)

    def formatted_cell(self, w, h, txt, border=0, align='L', fill=False):
        self.set_font("Arial", '', 10)
        self.set_text_color(0, 0, 0)  # Black text
        self.cell(w, h, txt, border, 1, align, fill)

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

    def add_executive_summary(self, route_details, estimated_result):
        self.chapter_title("Executive Summary")
        
        self.set_font("Arial", '', 11)
        self.set_text_color(0, 0, 0)
        
        summary_text = (
            f"This ESG report analyzes the carbon emissions for route '{self.route_name}'. "
            f"The report provides a comprehensive assessment of the environmental impact "
            f"based on precise GPS tracking and emissions calculation methodology aligned "
            f"with the GHG Protocol and ISO 14064 standards.\n\n"
        )
        
        if estimated_result:
            co2 = estimated_result.get('co2_emissions_kg', 'N/A')
            distance = estimated_result.get('total_distance_km', 0)
            
            if co2 != 'N/A':
                co2_per_km = float(co2) / float(distance) if float(distance) > 0 else 0
                summary_text += (
                    f"Key findings indicate total CO2 emissions of {co2:.2f} kg over a distance of "
                    f"{distance:.2f} km, resulting in an emission efficiency of {co2_per_km:.2f} kg/km. "
                )
            
            if route_details and route_details.get('Truck_Model'):
                summary_text += (
                    f"The vehicle used was a {route_details.get('Truck_Model')} with "
                    f"{route_details.get('Fuel Type', 'standard')} fuel type. "
                )
                
        summary_text += (
            f"This report is part of Kerry Logistics' commitment to environmental sustainability "
            f"and responsible logistics operations."
        )
        
        self.multi_cell(0, 6, summary_text)
        self.ln(5)

def generate_single_pdf(route_name, track_list, processed_track_list, route_details, estimated_result, map_obj):
    current_dir = os.path.dirname(os.path.abspath(__file__))  # Get the current directory
    reports_dir = os.path.join(current_dir, "../esg_single_route_reports")
    os.makedirs(reports_dir, exist_ok=True)  # Ensure the reports directory exists

    pdf = PDF(route_name)
    pdf.alias_nb_pages()  # For page numbering
    pdf.add_page()
    pdf.set_title(f"Kerry Logistics ESG Report - {route_name}")
    
    # 1. Executive Summary Section
    pdf.add_executive_summary(route_details, estimated_result)
    
    # 2. Route Details Section
    pdf.chapter_title("Route Details")
    
    if route_details:
        details_data = []
        details_data.append(("Route ID", route_name))
        
        for key, value in route_details.items():
            if key not in ['_id', 'id'] and value is not None:  # Skip internal IDs and empty values
                # Format keys for better display
                display_key = key.replace('_', ' ').title()
                details_data.append((display_key, value))
        
        pdf.add_metric_table(details_data)
    else:
        pdf.formatted_cell(0, 10, "No route details available for this route.")
    
    # 3. Carbon Emissions Section
    pdf.chapter_title("Carbon Emissions Analysis")

    if estimated_result:
        emissions_data = []
        co2 = estimated_result.get('co2_emissions_kg', 'N/A')
        
        if co2 != 'N/A':
            emissions_data.append(("CO2 Emissions", f"{co2:.2f} kg"))
        else:
            emissions_data.append(("CO2 Emissions", "N/A"))
            
        distance = estimated_result.get('total_distance_km', 0)
        emissions_data.append(("Total Distance", f"{distance:.2f} km"))
        
        if co2 != 'N/A' and distance > 0:
            co2_per_km = float(co2) / float(distance)
            emissions_data.append(("Emissions per km", f"{co2_per_km:.2f} kg/km"))
            
        pdf.add_metric_table(emissions_data)
        
        # Add emissions methodology explanation
        pdf.section_title("Emissions Calculation Methodology")
        methodology_text = (
            "Carbon emissions are calculated based on the vehicle specifications, route characteristics, "
            "and fuel consumption estimates. The methodology follows the Greenhouse Gas Protocol's "
            "Scope 1 direct emissions reporting guidelines and ISO 14064 standards. "
            "The calculation considers factors including total distance, vehicle weight, "
            "payload, fuel efficiency, road gradients, and emission factors specific to the fuel type."
        )
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(0, 5, methodology_text)
        pdf.ln(5)
    else:
        pdf.formatted_cell(0, 10, "No emissions data available for this route.")
    
    # 4. Route Comparison Section
    pdf.chapter_title("Route Efficiency Analysis")
    pdf.set_font("Arial", '', 10)

    # Calculate distances
    total_distance = sum(geodesic(track_list[i], track_list[i + 1]).meters for i in range(len(track_list) - 1))
    pdf.formatted_cell(0, 10, "Original Route Distance: {:.2f} km".format(total_distance/1000))
    
    if processed_track_list:
        # Use total_distance_km from processed data if available
        if route_details and 'filtered_version' in route_details:
            filtered_data = route_details['filtered_version']
            if filtered_data and 'total_distance_km' in filtered_data:
                total_distance_processed = filtered_data['total_distance_km'] * 1000  # Convert to meters
            else:
                total_distance_processed = sum(geodesic(processed_track_list[i], processed_track_list[i + 1]).meters for i in range(len(processed_track_list) - 1))
        else:
            total_distance_processed = sum(geodesic(processed_track_list[i], processed_track_list[i + 1]).meters for i in range(len(processed_track_list) - 1))
            
        pdf.formatted_cell(0, 10, "Optimized Route Distance: {:.2f} km".format(total_distance_processed/1000))
        
        # Calculate efficiency improvement
        if total_distance > 0:
            improvement = (total_distance - total_distance_processed) / total_distance * 100
            pdf.formatted_cell(0, 10, "Distance Improvement: {:.2f}%".format(improvement))
            
            if improvement > 0:
                # Calculate CO2 savings if we have emissions data
                if estimated_result and 'co2_emissions_kg' in estimated_result:
                    co2 = float(estimated_result['co2_emissions_kg'])
                    co2_savings = co2 * improvement / 100
                    pdf.formatted_cell(0, 10, "Estimated CO2 Savings: {:.2f} kg".format(co2_savings))
    else:
        pdf.formatted_cell(0, 10, "No optimized route data available for comparison.")
    
    pdf.ln(5)
    
    # 5. Route Map Visualization
    pdf.chapter_title("Route Visualization")
    
    map_path = os.path.join(reports_dir, 'map.html')
    screenshot_path = os.path.join(reports_dir, 'map_screenshot.png')
    save_map(map_obj, map_path)
    capture_map_screenshot(map_path, screenshot_path)
    
    # Add map legend
    pdf.section_title("Map Legend")
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(255, 0, 0)  # Red color
    pdf.cell(40, 10, "Original Route", 0, 0)
    
    pdf.set_text_color(0, 0, 255)  # Blue color
    pdf.cell(0, 10, "Optimized Route", 0, 1)
    
    pdf.set_text_color(0, 0, 0)  # Reset text color
    pdf.ln(5)
    
    # Add the map image to the PDF
    pdf.image(screenshot_path, x=15, y=pdf.get_y(), w=180)
    pdf.ln(130)  # Space for the map image
    
    # 6. Environmental Impact Section
    pdf.add_page()
    pdf.chapter_title("Environmental Impact & ESG Contribution")
    
    pdf.set_font("Arial", '', 10)
    impact_text = (
        "Kerry Logistics is committed to reducing its environmental footprint and supporting "
        "global climate action. This route analysis contributes to our ESG goals in the following ways:\n\n"
        
        "- Carbon Footprint Transparency: Provides accurate measurement of logistics emissions\n"
        "- Route Optimization: Identifies opportunities to reduce unnecessary travel distance\n"
        "- Vehicle Efficiency: Evaluates the performance of our fleet for potential improvements\n"
        "- Emissions Targets: Supports our science-based targets for emissions reduction\n"
        "- Stakeholder Engagement: Offers transparent reporting to clients and stakeholders\n\n"
        
        "This report aligns with the GHG Protocol Corporate Standard and contributes to Kerry Logistics' "
        "disclosure commitments under the Task Force on Climate-related Financial Disclosures (TCFD) "
        "and CDP (formerly Carbon Disclosure Project)."
    )
    pdf.multi_cell(0, 6, impact_text)
    pdf.ln(5)
    
    # Save PDF with ascii encoding
    pdf_output_path = os.path.join(reports_dir, f"Kerry_Logistics_ESG_Report_{route_name}.pdf")
    
    try:
        # Try with explicit ASCII encoding for compatibility
        pdf.output(pdf_output_path, 'F')
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        # Fallback to alternative method if available
        try:
            with open(pdf_output_path, 'wb') as f:
                f.write(pdf.output(dest='S').encode('latin-1'))
        except Exception as e2:
            print(f"Fallback method also failed: {str(e2)}")
            # Create a simplified emergency version of the PDF
            emergency_pdf = PDF(route_name)
            emergency_pdf.add_page()
            emergency_pdf.set_font('Arial', 'B', 16)
            emergency_pdf.cell(0, 10, 'Kerry Logistics ESG Report', 0, 1, 'C')
            emergency_pdf.set_font('Arial', '', 12)
            emergency_pdf.cell(0, 10, f'Route: {route_name}', 0, 1)
            emergency_pdf.cell(0, 10, f'Date: {datetime.datetime.now().strftime("%d %b %Y")}', 0, 1)
            if estimated_result:
                emergency_pdf.cell(0, 10, f'CO2 Emissions: {estimated_result.get("co2_emissions_kg", "N/A")} kg', 0, 1)
                emergency_pdf.cell(0, 10, f'Total Distance: {estimated_result.get("total_distance_km", 0):.2f} km', 0, 1)
            emergency_pdf.output(pdf_output_path)

    return pdf_output_path
