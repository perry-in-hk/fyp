import streamlit as st
from component.authenticator import handle_authentication, authenticator, save_config
import folium
from streamlit_folium import folium_static
import firebase_admin
from firebase_admin import credentials, firestore
from rdp import rdp
from geopy.distance import geodesic
import os
from component.single_route_pdf import generate_single_pdf
import component.send_email as send_email
from component.calculate_emission_distance import calculate_total_emission_and_distance
from component.multi_route_pdf import generate_muti_pdf
from component.GPS_cleaning_nonML import clean_gps_data, add_elevation_data, analyze_elevation
from component.emission import calculate_co2_emissions
# Import style module
from component.style import apply_custom_styles, show_kerry_header, display_metrics_row, get_marker_icon_color
import pandas as pd
import logging
import numpy as np
from sklearn.ensemble import IsolationForest
import json

# Apply custom styling
apply_custom_styles()

# Define your Google Maps API key from Streamlit secrets
GOOGLE_MAPS_API_KEY = st.secrets["google"]["maps_api_key"]

# Initialize session state variables
if 'logout' not in st.session_state:
    st.session_state['logout'] = False

# Check authentication status
handle_authentication(st)

if st.session_state['authentication_status']:
    # Initialize Firebase if not already initialized
    if not firebase_admin._apps:
        # Use Streamlit secrets to initialize Firebase Admin SDK
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
        
        # Initialize Firebase Admin SDK with credentials from secrets
        cred = credentials.Certificate(firebase_creds)
        firebase_admin.initialize_app(cred)

    db = firestore.client()

    # Add database selection dropdown
    if 'selected_database' not in st.session_state:
        st.session_state.selected_database = "real_database_01"  # Default to real database
    
    # Display Kerry Logistics header
    show_kerry_header()
        
    # Add welcome message to sidebar - moved to the top
    st.sidebar.markdown(f"""
    <div class="sidebar-welcome">
        <h3>Welcome, {st.session_state["name"]}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation menu
    page = st.sidebar.radio("Navigation", ["Single Route", "Timed Muti Routes", "GPS Filtering"])
    st.sidebar.markdown('<hr style="border:1px solid gray; margin-top: 5px; margin-bottom: 5px;">', unsafe_allow_html=True)

    # Database selection in a collapsible section
    with st.sidebar.expander("Database Settings", expanded=False):
        st.caption("DATABASE")
        selected_database = st.selectbox(
            "", 
            ["real_database_01", "test_database_02", "test_database_01"],
            index=0 if st.session_state.selected_database == "real_database_01" 
                  else 1 if st.session_state.selected_database == "test_database_02"
                  else 2
        )
        
        st.session_state.selected_database = selected_database
        
        # Show database status
        if selected_database == "real_database_01":
            st.markdown('<div class="db-badge db-badge-warning">⚠️ Real DB - Use caution</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="db-badge db-badge-info">Test DB: {selected_database.replace("test_database_", "")}</div>', unsafe_allow_html=True)

    # Update the corresponding routes collection name
    if selected_database == "test_database_02":
        routes_collection = "test_routes_detail_02"
        processed_collection = "processed_routes"
        estimated_result_collection = "estimated_result"
    elif selected_database == "test_database_01":
        routes_collection = "test_routes_detail_01"
        processed_collection = "processed_routes"
        estimated_result_collection = "estimated_result"
    else:  # real_database_01
        routes_collection = "real_routes_detail_01"
        processed_collection = "real_processed_routes_ricky"
        estimated_result_collection = "real_estimated_result"

    def fetch_driver_ids_and_names():
        driver_info = {}
        docs = db.collection(selected_database).stream()
        for doc in docs:
            driver_id = doc.id
            driver_name_doc = db.collection('Driver_Name').document(driver_id).get()
            if driver_name_doc.exists:
                driver_name = driver_name_doc.to_dict().get("displayName", driver_id)
            else:
                driver_name = driver_id
            driver_info[driver_id] = driver_name
        return driver_info

    def fetch_and_process_data(driver_id, route_name):
        doc_ref = db.collection(selected_database).document(driver_id)
        doc = doc_ref.get()

        if doc.exists:
            data = doc.to_dict()
            if route_name in data:
                input_data = data[route_name]
            else:
                st.error(f'No such field "{route_name}" in the document!')
                st.stop()
        else:
            st.error('No such document!')
            st.stop()

        return input_data

    def fetch_route_details(route_name):
        doc_ref = db.collection(routes_collection).document(route_name)
        doc = doc_ref.get()

        if doc.exists:
            route_details = doc.to_dict()
        else:
            route_details = None

        return route_details

    def translate_data(input_data):
        track_list = []
        track_dict = {}

        if isinstance(input_data, dict):
            input_data = input_data.get('route_data', [])

        for item in input_data:
            if isinstance(item, dict) and 'latitude' in item and 'longitude' in item:
                coordinates = [item['latitude'], item['longitude']]
                track_list.append(coordinates)
                track_dict[tuple(coordinates)] = coordinates

        return track_list, track_dict

    def translate_processed_data(data):
        coordinates = data.get("coordinates", [])
        translated_coords = [(coord["latitude"], coord["longitude"]) for coord in coordinates]
        return translated_coords

    def fetch_processed_data(route_id):
        doc_ref = db.collection(processed_collection).document(route_id)
        doc = doc_ref.get()

        if doc.exists:
            processed_data = doc.to_dict()
        else:
            processed_data = []

        return processed_data

    def fetch_estimated_result(route_name):
        doc_id = route_name + "_estimated_result_version"
        doc_ref = db.collection(estimated_result_collection).document(doc_id)
        doc = doc_ref.get()

        if doc.exists:
            estimated_result = doc.to_dict()
        else:
            estimated_result = None

        return estimated_result

    if page == "Single Route":
        st.sidebar.header("Select Driver and Route")

        driver_info = fetch_driver_ids_and_names()
        driver_ids = list(driver_info.keys())

        drivers_with_names = [driver_id for driver_id in driver_ids if driver_info[driver_id] != driver_id]
        drivers_without_names = [driver_id for driver_id in driver_ids if driver_info[driver_id] == driver_id]
        sorted_driver_ids = drivers_with_names + drivers_without_names

        driver_names_display = [
            f"{driver_info[driver_id]} ({driver_id})" if driver_info[driver_id] != driver_id else f"Guest User({driver_id})"
            for driver_id in sorted_driver_ids
        ]

        driver_selection = st.sidebar.selectbox("Select Driver", driver_names_display)
        driver_id = sorted_driver_ids[driver_names_display.index(driver_selection)]

        if 'confirm_clicked' not in st.session_state:
            st.session_state.confirm_clicked = False

        if driver_id:
            doc_ref = db.collection(selected_database).document(driver_id)
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict()
                route_names = list(data.keys())
                route_name = st.sidebar.selectbox("Select Route", route_names)

                if route_name:
                    if st.sidebar.button("Confirm Selection"):
                        st.session_state.confirm_clicked = True
                        input_data = fetch_and_process_data(driver_id, route_name)
                        if input_data:
                            track_list, track_dict = translate_data(input_data)

                            epsilon = 0.0003
                            simplified_route = rdp(track_list, epsilon=epsilon)

                            mid = len(simplified_route)
                            centre = simplified_route[int(mid / 2)]

                            # Check if processed route exists
                            filtered_route_name = route_name + '_filtered_version'
                            processed_data = fetch_processed_data(filtered_route_name)
                            has_processed_route = processed_data and isinstance(processed_data, dict)
                            
                            # If processed route exists, add route selection option
                            route_display_option = "original"
                            if has_processed_route:
                                st.header("Route Display Options")
                                route_display_option = st.radio(
                                    "Select route to display:",
                                    ["original", "matched", "both"],
                                    horizontal=True,
                                    index=2  # Default to both
                                )
                            
                            map_plot = folium.Map(location=centre, zoom_start=14)

                            # Show original route if selected
                            if route_display_option in ["original", "both"]:
                                # Use Kerry branded colors for original route markers
                                original_color = get_marker_icon_color("original")
                                for point in track_list:
                                    folium.Marker(location=point, icon=folium.Icon(color=original_color)).add_to(map_plot)
                                folium.PolyLine(track_list, color=original_color).add_to(map_plot)

                            total_distance = sum(geodesic(track_list[i], track_list[i + 1]).meters for i in range(len(track_list) - 1))

                            st.header("Route Comparison")

                            filtered_route_name = route_name + '_filtered_version'
                            processed_data = fetch_processed_data(filtered_route_name)

                            if processed_data:
                                processed_track_list = translate_processed_data(processed_data)

                                if processed_track_list and route_display_option in ["matched", "both"]:
                                    # Only show the polyline for processed route, no markers
                                    processed_color = get_marker_icon_color("processed")
                                    folium.PolyLine(processed_track_list, color=processed_color).add_to(map_plot)

                                    # Get the stored total_distance_km value from processed data instead of recalculating
                                    total_distance_processed = processed_data.get('total_distance_km', 0)
                                    if total_distance_processed == 0:
                                        # Fallback to calculation if the value isn't stored
                                        total_distance_processed = sum(geodesic(processed_track_list[i], processed_track_list[i + 1]).meters for i in range(len(processed_track_list) - 1)) / 1000
                                else:
                                    st.warning("Processed route data is empty.")
                            else:
                                st.warning("No processed route found for this route ID.")

                            # Wrap map in styled container
                            st.markdown('<div class="map-container">', unsafe_allow_html=True)
                            folium_static(map_plot)
                            st.markdown('</div>', unsafe_allow_html=True)

                            estimated_result = fetch_estimated_result(route_name)
                            st.header("Carbon emission")
                            if estimated_result:
                                # Use metrics row to display carbon emission data
                                metrics = {
                                    "CO2 Emissions": (f"{estimated_result['co2_emissions_kg']:.2f}", "kg"),
                                    "Original Distance": (f"{total_distance/1000:.2f}", "km"),
                                }
                                
                                # Add processed distance if available
                                if processed_data and 'processed_track_list' in locals() and processed_track_list:
                                    metrics["Processed Distance"] = (f"{total_distance_processed:.2f}", "km")
                                
                                # Display metrics with no extra divs
                                display_metrics_row(metrics, highlight_keys=["CO2 Emissions"])
                            else:
                                st.warning("No estimated result found for this route.")
                                
                                # Still show distances even without emission data
                                metrics = {
                                    "Original Distance": (f"{total_distance/1000:.2f}", "km"),
                                }
                                
                                # Add processed distance if available
                                if processed_data and 'processed_track_list' in locals() and processed_track_list:
                                    metrics["Processed Distance"] = (f"{total_distance_processed:.2f}", "km")
                                
                                display_metrics_row(metrics)

                            route_details = fetch_route_details(route_name)
                            if route_details:
                                st.header("Route Details")
                                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                                st.write("Document ID:", route_name)
                                st.write("Serial Number:", route_details.get("Serial Number", "N/A"))
                                st.write("Truck Model:", route_details.get("Truck_Model", "N/A"))
                                st.write("Fuel Type:", route_details.get("Fuel Type", "N/A"))
                                st.write("Truck Weight:", route_details.get("Truck Weight", "N/A"))
                                st.write("Reminder:", route_details.get("Reminder", "N/A"))
                                st.markdown('</div>', unsafe_allow_html=True)
                            else:
                                st.warning("No route details found.")

                            # Add a legend to explain the route colors
                            if route_display_option in ["both"]:
                                st.markdown("""
                                <div style="background-color:#f0f0f0; padding:10px; border-radius:5px; margin:10px 0;">
                                    <p><strong>Route Legend:</strong></p>
                                    <ul style="margin-bottom:0;">
                                        <li><span style="color:red;">◼</span> Original GPS Route</li>
                                        <li><span style="color:blue;">◼</span> Map-Matched Route</li>
                                    </ul>
                                </div>
                                """, unsafe_allow_html=True)
                            elif route_display_option == "original":
                                st.markdown("""
                                <div style="background-color:#f0f0f0; padding:10px; border-radius:5px; margin:10px 0;">
                                    <p><strong>Route Legend:</strong></p>
                                    <ul style="margin-bottom:0;">
                                        <li><span style="color:red;">◼</span> Original GPS Route</li>
                                    </ul>
                                </div>
                                """, unsafe_allow_html=True)
                            else:  # matched
                                st.markdown("""
                                <div style="background-color:#f0f0f0; padding:10px; border-radius:5px; margin:10px 0;">
                                    <p><strong>Route Legend:</strong></p>
                                    <ul style="margin-bottom:0;">
                                        <li><span style="color:blue;">◼</span> Map-Matched Route</li>
                                    </ul>
                                </div>
                                """, unsafe_allow_html=True)

                    if st.sidebar.button("Generate and Send PDF Report", disabled=not st.session_state.confirm_clicked):
                        input_data = fetch_and_process_data(driver_id, route_name)
                        if input_data:
                            track_list, track_dict = translate_data(input_data)

                            epsilon = 0.0003
                            simplified_route = rdp(track_list, epsilon=epsilon)

                            mid = len(simplified_route)
                            centre = simplified_route[int(mid / 2)]

                            map_plot = folium.Map(location=centre, zoom_start=14)

                            # Get the display option that was selected (default to "both" if not set)
                            route_display_option = "both"
                            if 'route_display_option' in locals():
                                route_display_option = route_display_option
                            
                            # Show original route if selected for PDF
                            if route_display_option in ["original", "both"]:
                                for point in track_list:
                                    folium.Marker(location=point, icon=folium.Icon(color='red')).add_to(map_plot)
                                folium.PolyLine(track_list, color='red').add_to(map_plot)

                            total_distance = sum(geodesic(track_list[i], track_list[i + 1]).meters for i in range(len(track_list) - 1))

                            filtered_route_name = route_name + '_filtered_version'
                            processed_data = fetch_processed_data(filtered_route_name)

                            if processed_data:
                                processed_track_list = translate_processed_data(processed_data)

                                if processed_track_list:
                                    for point in processed_track_list:
                                        folium.Marker(location=point, icon=folium.Icon(color='blue')).add_to(map_plot)
                                    folium.PolyLine(processed_track_list, color='blue').add_to(map_plot)

                            else:
                                st.warning("Processed route data is empty.")
                            folium_static(map_plot)

                            route_details = fetch_route_details(route_name)
                            estimated_result = fetch_estimated_result(route_name)
                            st.header("Carbon emission")

                        pdf_path = generate_single_pdf(route_name, track_list, processed_track_list, route_details, estimated_result, map_plot)
                        
                        with open(pdf_path, "rb") as file:
                                pdf_bytes = file.read()


                        st.sidebar.success("PDF report generated successfully!")

                            # Create a download button
                        st.sidebar.download_button(
                                label="Download PDF",
                                data=pdf_bytes,
                                file_name=f"ESG Report for {route_name}.pdf",
                                mime="application/pdf"
                            )
                        
                        # Add spacer to prevent logout overlap
                        st.sidebar.markdown('<div style="margin-bottom:60px;"></div>', unsafe_allow_html=True)

    elif page == "Timed Muti Routes":
        # Dashboard-style layout for Multi Routes
        st.markdown("""
        <div class="page-subtitle">
            <h2>Time Period Emission Analytics</h2>
            <p class="subtitle-description">Analyze carbon emissions for all routes across all users within a specified time period.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Create a more compact date selection area with columns
        st.markdown('<div class="date-selector-container">', unsafe_allow_html=True)
        date_col1, date_col2, date_col3 = st.columns([1,1,1])
        
        with date_col1:
            st.markdown('<div class="date-label">Start Date</div>', unsafe_allow_html=True)
            start_date = st.date_input("", key="start_date")
            
        with date_col2:
            st.markdown('<div class="date-label">End Date</div>', unsafe_allow_html=True)
            end_date = st.date_input("", key="end_date")
            
        with date_col3:
            st.markdown('<div style="height: 28px"></div>', unsafe_allow_html=True)  # Spacing to align button
            calculate_button = st.button("Generate Analysis", use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Initialize session state
        if 'multi_route_calculated' not in st.session_state:
            st.session_state.multi_route_calculated = False
            
        if 'multi_emission_data' not in st.session_state:
            st.session_state.multi_emission_data = None
            
        if 'multi_distance_data' not in st.session_state:
            st.session_state.multi_distance_data = None
                
        # Calculate button action
        if calculate_button:
            if start_date and end_date:
                try:
                    with st.spinner("Analyzing all routes from all users in the specified time period..."):
                        # Convert datetime.date to string in the required format
                        start_date_str = start_date.strftime('%d-%m-%Y')
                        end_date_str = end_date.strftime('%d-%m-%Y')
                        
                        total_emission, total_distance, routes_count = calculate_total_emission_and_distance(start_date_str, end_date_str)
                        
                        # Store in session state
                        st.session_state.multi_route_calculated = True
                        st.session_state.multi_emission_data = total_emission
                        st.session_state.multi_distance_data = total_distance
                        st.session_state.routes_count = routes_count
                        
                        # Calculate days difference
                        days_diff = (end_date - start_date).days + 1  # Include both start and end dates
                        
                        # Store period info in session state
                        st.session_state.period_days = days_diff
                        st.session_state.start_date_str = start_date_str
                        st.session_state.end_date_str = end_date_str
                        
                except Exception as e:
                    st.error(f"Error calculating data: {e}")
                    st.error("Please check database connection and ensure 'real_estimated_result' collection exists.")
            else:
                st.error("Please enter both start and end dates.")
        
        # Display results if calculated
        if st.session_state.multi_route_calculated and st.session_state.multi_emission_data is not None:
            # Main metrics in a highlighted row
            st.markdown('<div class="multi-metrics-container">', unsafe_allow_html=True)
            
            # Create metrics display with columns
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            
            with metric_col1:
                metrics = {"Total CO2 Emissions": (f"{st.session_state.multi_emission_data:.2f}", "kg")}
                display_metrics_row(metrics, highlight_keys=["Total CO2 Emissions"])
                
            with metric_col2:
                metrics = {"Total Distance": (f"{st.session_state.multi_distance_data:.2f}", "km")}
                display_metrics_row(metrics)
                
            with metric_col3:
                # Calculate daily average
                if st.session_state.period_days > 0:
                    daily_avg = st.session_state.multi_emission_data / st.session_state.period_days
                    metrics = {"Daily Average": (f"{daily_avg:.2f}", "kg/day")}
                    display_metrics_row(metrics)
                
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Data source information
            st.markdown("""
            <div class="data-source-info">
                <p>This analysis includes all routes from all users in the Kerry Logistics network during the selected time period.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Data visualization section
            st.markdown("""
            <div class="analytics-container">
                <h3>Period Analytics</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Date range information
            st.markdown(f"""
            <div class="period-info">
                <span class="info-label">Period:</span> 
                <span class="info-value">{st.session_state.start_date_str}</span> to 
                <span class="info-value">{st.session_state.end_date_str}</span>
                <span class="info-label">Duration:</span>
                <span class="info-value">{st.session_state.period_days} days</span>
                <span class="info-label">Routes Analyzed:</span>
                <span class="info-value">{st.session_state.routes_count}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Performance indicators
            st.markdown('<div class="performance-indicators">', unsafe_allow_html=True)
            perf_col1, perf_col2 = st.columns(2)
            
            with perf_col1:
                # Emissions per km
                emissions_per_km = st.session_state.multi_emission_data / max(st.session_state.multi_distance_data, 0.01)
                st.markdown(f"""
                <div class="indicator-card">
                    <div class="indicator-title">Emissions Efficiency</div>
                    <div class="indicator-value">{emissions_per_km:.3f} kg/km</div>
                </div>
                """, unsafe_allow_html=True)
                
            with perf_col2:
                if 'routes_count' in st.session_state and st.session_state.routes_count > 0:
                    avg_per_route = st.session_state.multi_emission_data / st.session_state.routes_count
                    st.markdown(f"""
                    <div class="indicator-card">
                        <div class="indicator-title">Average Per Route</div>
                        <div class="indicator-value">{avg_per_route:.2f} kg/route</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Monthly projection (based on daily average)
                    daily_avg = st.session_state.multi_emission_data / max(st.session_state.period_days, 1)
                    monthly_projection = daily_avg * 30
                    st.markdown(f"""
                    <div class="indicator-card">
                        <div class="indicator-title">Monthly Projection</div>
                        <div class="indicator-value">{monthly_projection:.2f} kg/month</div>
                    </div>
                    """, unsafe_allow_html=True)
                
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Export options
            st.markdown("""
            <div class="export-options">
                <h3>Export Report</h3>
            </div>
            """, unsafe_allow_html=True)
            
            export_col1, export_col2 = st.columns(2)
            
            with export_col1:
                if st.button("Generate ESG PDF Report", use_container_width=True):
                    try:
                        with st.spinner("Generating PDF report..."):
                            # Pass the routes count to the pdf generation function if available
                            routes_count = st.session_state.get('routes_count', 0)
                            
                            pdf_path_2 = generate_muti_pdf(
                                st.session_state.start_date_str, 
                                st.session_state.end_date_str, 
                                st.session_state.multi_emission_data, 
                                st.session_state.multi_distance_data,
                                routes_count
                            )
                            
                            with open(pdf_path_2, "rb") as file:
                                pdf_bytes = file.read()
                                
                            st.session_state.pdf_bytes = pdf_bytes
                            st.session_state.pdf_ready = True
                            st.success("PDF report generated successfully!")
                    except Exception as e:
                        st.error(f"Error generating PDF: {e}")
            
            with export_col2:
                if 'pdf_ready' in st.session_state and st.session_state.pdf_ready:
                    st.download_button(
                        label="Download PDF Report",
                        data=st.session_state.pdf_bytes,
                        file_name=f"ESG Report {st.session_state.start_date_str} to {st.session_state.end_date_str}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

    elif page == "GPS Filtering":
        st.sidebar.header("Filter GPS Data")
        
        driver_info = fetch_driver_ids_and_names()
        driver_ids = list(driver_info.keys())

        drivers_with_names = [driver_id for driver_id in driver_ids if driver_info[driver_id] != driver_id]
        drivers_without_names = [driver_id for driver_id in driver_ids if driver_info[driver_id] == driver_id]
        sorted_driver_ids = drivers_with_names + drivers_without_names

        driver_names_display = [
            f"{driver_info[driver_id]} ({driver_id})" if driver_info[driver_id] != driver_id else f"Guest User({driver_id})"
            for driver_id in sorted_driver_ids
        ]

        driver_selection = st.sidebar.selectbox("Select Driver", driver_names_display)
        driver_id = sorted_driver_ids[driver_names_display.index(driver_selection)]

        route_name = None
        if driver_id:
            doc_ref = db.collection(selected_database).document(driver_id)
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict()
                route_names = list(data.keys())
                route_name = st.sidebar.selectbox("Select Route", route_names)

        if driver_id and route_name:
            filtered_route_name = route_name + '_filtered_version'
            
            # Check if filtered route already exists
            existing_filtered_data = fetch_processed_data(filtered_route_name)
            
            if existing_filtered_data:
                st.success(f"Filtered route data already exists for {route_name}")
                processed_track_list = translate_processed_data(existing_filtered_data)
                
                if processed_track_list:
                    # Show the filtered route on a map
                    input_data = fetch_and_process_data(driver_id, route_name)
                    if input_data:
                        track_list, _ = translate_data(input_data)
                        
                        # Use the first point as center for the map
                        centre = processed_track_list[0] if processed_track_list else track_list[0]
                        map_plot = folium.Map(location=centre, zoom_start=14)
                        
                        # Original route in red
                        for point in track_list:
                            folium.Marker(location=point, icon=folium.Icon(color='red')).add_to(map_plot)
                        folium.PolyLine(track_list, color='red').add_to(map_plot)
                        
                        # Filtered route in blue - only show line without markers
                        folium.PolyLine(processed_track_list, color='blue').add_to(map_plot)
                        
                        # Wrap map in styled container
                        st.markdown('<div class="map-container">', unsafe_allow_html=True)
                        folium_static(map_plot)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Calculate distances
                        total_distance = sum(geodesic(track_list[i], track_list[i + 1]).meters 
                                         for i in range(len(track_list) - 1)) / 1000  # km
                                         
                        # Get the stored total_distance_km value from processed data instead of recalculating
                        total_distance_processed = existing_filtered_data.get('total_distance_km', 0)
                        if total_distance_processed == 0:
                            # Fallback to calculation if the value isn't stored
                            total_distance_processed = sum(geodesic(processed_track_list[i], processed_track_list[i + 1]).meters 
                                                for i in range(len(processed_track_list) - 1)) / 1000  # km
                                                
                        st.write(f"Original route distance: {total_distance:.2f} km")
                        st.write(f"Filtered route distance: {total_distance_processed:.2f} km")
            
            if st.sidebar.button("Filter GPS Data"):
                # First check if filtered data already exists
                if existing_filtered_data:
                    st.info("Filtered data already exists. Showing existing results.")
                else:
                    st.info("Starting GPS data filtering process...")
                    input_data = fetch_and_process_data(driver_id, route_name)
                    
                    if input_data:
                        st.info(f"Retrieved {len(input_data.get('route_data', []) if isinstance(input_data, dict) else input_data)} GPS points from Firestore")
                        
                        # Convert input data to a DataFrame for processing
                        track_list, _ = translate_data(input_data)
                        st.info(f"Translated {len(track_list)} GPS points for processing")
                        
                        # Create a DataFrame with timestamp, latitude, longitude
                        df = pd.DataFrame()
                        
                        # If input_data contains timestamps, use them; otherwise create dummy timestamps
                        if isinstance(input_data, list):
                            # Create timestamps spaced 5 seconds apart
                            timestamps = pd.date_range(start=pd.Timestamp.now() - pd.Timedelta(seconds=5*len(input_data)), 
                                                    periods=len(input_data), freq='5S')
                            df['timestamp'] = timestamps
                            df['latitude'] = [point[0] for point in track_list]
                            df['longitude'] = [point[1] for point in track_list]
                            st.info("Created DataFrame with list-based data structure")
                        else:
                            # Handle dict input with route_data
                            route_data = input_data.get('route_data', [])
                            timestamps = pd.date_range(start=pd.Timestamp.now() - pd.Timedelta(seconds=5*len(route_data)), 
                                               periods=len(route_data), freq='5S')
                            df['timestamp'] = timestamps
                            df['latitude'] = [item.get('latitude') for item in route_data if isinstance(item, dict)]
                            df['longitude'] = [item.get('longitude') for item in route_data if isinstance(item, dict)]
                            st.info("Created DataFrame with dictionary-based data structure")
                        
                        # For displaying sample of raw GPS data
                        if len(df) > 0:
                            st.write("Sample of raw GPS data:")
                            
                            # First 3 samples
                            st.write("First 3 points:")
                            st.write(df.head(3))
                            
                            # Middle 3 samples (if there are enough points)
                            if len(df) > 6:
                                st.write("...")
                                mid_index = len(df) // 2
                                middle_samples = df.iloc[mid_index-1:mid_index+2]
                                st.write(f"Middle 3 points (around index {mid_index}):")
                                st.write(middle_samples)
                            
                            # Last 3 samples
                            if len(df) > 3:
                                st.write("...")
                                st.write("Last 3 points:")
                                st.write(df.tail(3))
                            
                            st.write(f"Total: {len(df)} GPS points")
                        
                        # Clean the GPS data
                        try:
                            # 更新 clean_gps_data 調用以接收角度可靠性數據
                            with st.spinner("Cleaning GPS data - this may take a while..."):
                                cleaned_df, total_time, total_distance, angle_reliability_data = clean_gps_data(df, GOOGLE_MAPS_API_KEY)
                                st.success(f"GPS cleaning complete! Retained {len(cleaned_df)} of {len(df)} points")
                                
                                if len(cleaned_df) > 0:
                                    # Show sample of cleaned data
                                    st.write("Sample of cleaned GPS data:")
                                    
                                    # First 3 samples
                                    st.write("First 3 points:")
                                    st.write(cleaned_df.head(3))
                                    
                                    # Middle 3 samples (if there are enough points)
                                    if len(cleaned_df) > 6:
                                        st.write("...")
                                        mid_index = len(cleaned_df) // 2
                                        middle_samples = cleaned_df.iloc[mid_index-1:mid_index+2]
                                        st.write(f"Middle 3 points (around index {mid_index}):")
                                        st.write(middle_samples)
                                    
                                    # Last 3 samples
                                    if len(cleaned_df) > 3:
                                        st.write("...")
                                        st.write("Last 3 points:")
                                        st.write(cleaned_df.tail(3))
                                    
                                    st.write(f"Total: {len(cleaned_df)} GPS points after cleaning")
                                    
                                    # Add elevation data
                                    with st.spinner("Fetching elevation data from API..."):
                                        st.info(f"Processing elevation data for {len(cleaned_df)} GPS points...")
                                        cleaned_df = add_elevation_data(cleaned_df)
                                        st.success("Elevation data successfully added")
                                    
                                    # Analyze elevation
                                    with st.spinner("Analyzing elevation profile..."):
                                        elevation_stats = analyze_elevation(cleaned_df)
                                        st.success("Elevation analysis complete")
                                    
                                    # Upload to Firebase
                                    with st.spinner("Uploading processed data to Firestore..."):
                                        coordinates = [{"latitude": row['latitude'], "longitude": row['longitude']} 
                                                      for _, row in cleaned_df.iterrows()]
                                        
                                        st.info(f"Preparing to upload {len(coordinates)} GPS points to Firestore")
                                        doc_ref = db.collection(processed_collection).document(filtered_route_name)
                                        doc_ref.set({
                                            "coordinates": coordinates,
                                            "timestamp": firestore.SERVER_TIMESTAMP,
                                            "total_distance_km": total_distance,
                                            "total_time_seconds": total_time,
                                            "total_elevation_gain": elevation_stats['total_ascent'],
                                            "total_elevation_loss": elevation_stats['total_descent'],
                                            "max_elevation": elevation_stats['max_elevation'],
                                            "min_elevation": elevation_stats['min_elevation']
                                        })
                                        st.success(f"Data successfully uploaded to Firestore collection: {processed_collection}/{filtered_route_name}")
                                    
                                    # 創建地圖顯示
                                    with st.spinner("Generating map visualization..."):
                                        cleaned_coords = [(row['latitude'], row['longitude']) for _, row in cleaned_df.iterrows()]
                                        
                                        # 抽取角度過濾（但未進行地圖匹配）後嘅點
                                        angle_filtered_coords = [(row['latitude'], row['longitude']) 
                                                               for _, row in angle_reliability_data[angle_reliability_data['angle_reliability'] == 'Y'].iterrows()]
                                        
                                        centre = cleaned_coords[0] if cleaned_coords else track_list[0]
                                        map_plot = folium.Map(location=centre, zoom_start=14)
                                        
                                        # 原始路徑（紅色）
                                        st.info("Adding original route to map (red)...")
                                        original_color = get_marker_icon_color("original")
                                        for point in track_list:
                                            folium.Marker(location=point, icon=folium.Icon(color=original_color)).add_to(map_plot)
                                        folium.PolyLine(track_list, color=original_color).add_to(map_plot)
                                        
                                        # 角度過濾後路徑（綠色）
                                        st.info("Adding angle-filtered route to map (green)...")
                                        angle_filtered_color = get_marker_icon_color("angle_filtered")
                                        for point in angle_filtered_coords:
                                            folium.Marker(location=point, icon=folium.Icon(color=angle_filtered_color)).add_to(map_plot)
                                        folium.PolyLine(angle_filtered_coords, color=angle_filtered_color).add_to(map_plot)
                                        
                                        # 最終過濾和地圖匹配後路徑（藍色）- 只顯示路線，不顯示標記
                                        st.info("Adding final processed route to map (blue)...")
                                        processed_color = get_marker_icon_color("processed")
                                        folium.PolyLine(cleaned_coords, color=processed_color).add_to(map_plot)
                                        
                                        # 標記角度問題點
                                        st.info("Marking points with angle issues (X)...")
                                        for idx, row in angle_reliability_data.iterrows():
                                            # 確定點嘅顏色
                                            if row['angle_reliability'] == 'X':
                                                color = 'red'
                                                icon = 'remove'
                                            else:
                                                color = 'blue'
                                                icon = 'info'
                                            
                                            # 創建彈出信息
                                            if pd.notna(row.get('angle_value')):
                                                popup_text = f"角度: {row['angle_value']:.1f}°<br>標記: {row['angle_reliability']}"
                                            else:
                                                popup_text = f"標記: {row['angle_reliability']}"
                                            
                                            # 添加標記
                                            folium.CircleMarker(
                                                location=[row['latitude'], row['longitude']],
                                                radius=5,
                                                color=color,
                                                fill=True,
                                                fill_opacity=0.7,
                                                popup=popup_text
                                            ).add_to(map_plot)
                                        
                                        folium_static(map_plot)
                                    
                                    # 顯示有關角度過濾嘅統計
                                    st.subheader("角度過濾統計")
                                    total_x_points = sum(angle_reliability_data['angle_reliability'] == 'X')
                                    total_y_points = sum(angle_reliability_data['angle_reliability'] == 'Y')
                                    st.write(f"標記為不可靠點 (X): {total_x_points} ({total_x_points/len(angle_reliability_data)*100:.1f}%)")
                                    st.write(f"標記為可靠點 (Y): {total_y_points} ({total_y_points/len(angle_reliability_data)*100:.1f}%)")
                                    
                                    st.success(f"GPS data filtering complete! Route has been processed and stored as {filtered_route_name}")
                                    
                                    # Display statistics
                                    st.subheader("Route Statistics")
                                    # Use metrics row to display route statistics
                                    metrics = {
                                        "Distance": (f"{total_distance:.2f}", "km"),
                                        "Time": (f"{total_time/3600:.2f}", "hours"),
                                        "Total Ascent": (elevation_stats['total_ascent'], "m"),
                                        "Total Descent": (elevation_stats['total_descent'], "m")
                                    }
                                    display_metrics_row(metrics)
                                    
                                    # Second row for elevation metrics
                                    elevation_metrics = {
                                        "Max Elevation": (elevation_stats['max_elevation'], "m"),
                                        "Min Elevation": (elevation_stats['min_elevation'], "m")
                                    }
                                    display_metrics_row(elevation_metrics)
                                    
                                    st.info("You can now calculate CO2 emissions using the 'Calculate CO2 Emissions' button")
                                else:
                                    st.warning("No valid GPS points remained after cleaning. Please check the original data.")
                        except Exception as e:
                            st.error(f"Error during GPS data processing: {str(e)}")
                            import traceback
                            st.error(f"Detailed error: {traceback.format_exc()}")
                    else:
                        st.error("Could not retrieve route data from Firestore.")

            # Add button to calculate carbon emission using emission.py directly
            if st.sidebar.button("Calculate CO2 Emissions"):
                try:
                    # Get the filtered route data
                    filtered_data = fetch_processed_data(filtered_route_name)
                    
                    if filtered_data:
                        # Extract route parameters
                        total_distance = filtered_data.get('total_distance_km', 0)
                        total_time = filtered_data.get('total_time_seconds', 3600)
                        total_elevation_gain = filtered_data.get('total_elevation_gain', 0)
                        total_elevation_loss = filtered_data.get('total_elevation_loss', 0)
                        
                        # Get route details for vehicle parameters
                        route_details = fetch_route_details(route_name) or {}
                        
                        # Set default values if not found
                        fuel_efficiency = route_details.get('fuel_efficiency', 10.0)  # km/L
                        payload_weight = route_details.get('payload_weight', 5.0)  # tonnes
                        max_payload = route_details.get('max_payload', 25.0)  # tonnes
                        co2_emission_factor = route_details.get('co2_emission_factor', 2640)  # g/L (diesel)
                        
                        # Calculate emissions
                        emissions = calculate_co2_emissions(
                            distance=total_distance,
                            fuel_efficiency=fuel_efficiency,
                            total_elevation_gain=total_elevation_gain,
                            total_elevation_loss=total_elevation_loss,
                            payload_weight=payload_weight,
                            max_payload=max_payload,
                            co2_emission_factor=co2_emission_factor,
                            total_time=total_time
                        )
                        
                        # Save result to Firebase
                        result_doc_id = route_name + "_estimated_result_version"
                        db.collection(estimated_result_collection).document(result_doc_id).set({
                            'co2_emissions_kg': emissions,
                            'total_distance_km': total_distance,
                            'timestamp': firestore.SERVER_TIMESTAMP
                        })
                        
                        # Display results
                        st.success(f"CO2 Emissions calculated successfully!")
                        
                        # Use metrics row to display emissions data
                        emission_metrics = {
                            "CO2 Emissions": (f"{emissions:.2f}", "kg"),
                            "Distance": (f"{total_distance:.2f}", "km")
                        }
                        # Ensure no extra divs
                        display_metrics_row(emission_metrics, highlight_keys=["CO2 Emissions"])
                        
                        # Vehicle parameters in a styled card
                        st.subheader("Vehicle Parameters")
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.write(f"Fuel Efficiency: {fuel_efficiency} km/L")
                        st.write(f"Payload: {payload_weight} tonnes (max: {max_payload} tonnes)")
                        st.write(f"CO2 Factor: {co2_emission_factor} g/L")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Elevation analysis in a styled card
                        st.subheader("Elevation Analysis")
                        elevation_metrics = {
                            "Total Ascent": (total_elevation_gain, "m"),
                            "Total Descent": (total_elevation_loss, "m")
                        }
                        display_metrics_row(elevation_metrics)
                    else:
                        st.warning("No filtered data available. Please filter the GPS data first.")
                except Exception as e:
                    st.error(f"Error calculating emissions: {str(e)}")

    # Add a spacer to push content up away from the logout button
    st.sidebar.markdown('<div style="margin-bottom:150px;"></div>', unsafe_allow_html=True)
    
    # Use a more robust fixed-position logout container with inline styles
    st.sidebar.markdown('''
    <div class="sidebar-logout" style="position:fixed; bottom:0; left:0; width:100%; 
    background:#0A0F16; padding:15px; border-top:1px solid #2A3A4A; 
    box-shadow:0 -4px 10px rgba(0,0,0,0.3); z-index:9999; margin:0;">
    ''', unsafe_allow_html=True)
    
    # Add the logout button
    authenticator.logout("Logout", "sidebar")
    
    # Close the div
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    # Save config on exit
    save_config()
