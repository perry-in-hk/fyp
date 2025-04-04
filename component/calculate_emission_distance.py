import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import re
import pandas as pd
import math
from geopy.distance import geodesic
import streamlit as st

def initialize_firestore():
    if not firebase_admin._apps:
        cred = credentials.Certificate('fyp-gps.json')
        firebase_admin.initialize_app(cred)

    return firestore.client()

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

def calculate_total_emission_and_distance(start_date, end_date):
    db = initialize_firestore()
    total_emission = 0
    total_distance = 0
    routes_count = 0

    start_date = datetime.datetime.strptime(start_date, '%d-%m-%Y')
    end_date = datetime.datetime.strptime(end_date, '%d-%m-%Y')
    
    # Use the correct database collection
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
                #print(f"Processing route: {doc_id}, date: {doc_date}")
                
                if start_date <= doc_date <= end_date:
                    #print(f"Including document with ID {doc_id}")
                    data = doc.to_dict()
                    emission = data.get('co2_emissions_kg', 0)
                    distance = data.get('total_distance_km', 0)
                    
                    # Make sure we only add valid numeric values
                    if isinstance(emission, (int, float)) and isinstance(distance, (int, float)):
                        total_emission += emission
                        total_distance += distance
                        routes_count += 1
                    
            except (ValueError, IndexError) as e:
                print(f"Error processing document {doc_id}: {e}")
                continue
    
    print(f"Calculated totals from {routes_count} routes within the date range")
    return total_emission, total_distance, routes_count

