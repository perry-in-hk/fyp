import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from pykalman import KalmanFilter
import osmnx as ox
import json
import logging
from component.emission import calculate_co2_emissions
import googlemaps
import math
import streamlit as st

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

def retrieve_data_from_firestore(collection_name):
    db = init_firebase()
    docs = db.collection(collection_name).stream()
    
    data = []
    for doc in docs:
        data.append(doc.to_dict())

    df = pd.DataFrame(data)

    # Print the DataFrame to inspect its structure
    print("Retrieved DataFrame Structure:\n", df.head())
    print("Columns in DataFrame:", df.columns.tolist())

    if 'timestamp' not in df.columns:
        num_points = len(df)
        start_time = pd.Timestamp.now() - pd.Timedelta(seconds=5*num_points)
        df['timestamp'] = pd.date_range(start=start_time, periods=num_points, freq='5S')
    else:
        df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Extract latitude and longitude from the coordinates column
    if 'coordinates' in df.columns:
        df['latitude'] = df['coordinates'].apply(lambda x: x[0]['latitude'] if x else None)
        df['longitude'] = df['coordinates'].apply(lambda x: x[0]['longitude'] if x else None)

        # Drop the coordinates column if not needed
        df.drop(columns=['coordinates'], inplace=True)

    return df

def haversine_distance(df):
    R = 6371e3  # Earth radius in meters
    lat = np.radians(df['latitude'])
    lon = np.radians(df['longitude'])
    
    lat_prev = lat.shift()
    lon_prev = lon.shift()
    dlat = lat - lat_prev
    dlon = lon - lon_prev
    
    a = np.sin(dlat / 2)**2 + np.cos(lat_prev) * np.cos(lat) * np.sin(dlon / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c

def clean_gps_data(raw_df, google_api_key=None):
    # Layer 0: Preprocessing
    if raw_df.empty:
        return pd.DataFrame(), 0.0, 0.0, pd.DataFrame()  # 添加空嘅角度可靠性DataFrame
    
    df = raw_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.sort_values('timestamp', inplace=True)

    # Check if required columns exist
    if 'latitude' not in df.columns or 'longitude' not in df.columns:
        logging.error("Error: 'latitude' or 'longitude' columns are missing.")
        return pd.DataFrame(), 0.0, 0.0, pd.DataFrame()

    # 新增: 角度過濾（喺異常檢測之前）
    print("開始角度過濾...")
    df_angle_filtered, df_with_angle_marks = filter_by_angle(df, angle_threshold=90)
    
    # 打印角度標記嘅統計
    print(f"角度標記為 'X' 嘅點: {sum(df_with_angle_marks['angle_reliability'] == 'X')}")
    print(f"角度標記為 'Y' 嘅點: {sum(df_with_angle_marks['angle_reliability'] == 'Y')}")
    
    # 使用過濾後嘅數據繼續處理
    df = df_angle_filtered
    
    # Layer 1: Outlier Detection
    # ... existing code ...
    from sklearn.ensemble import IsolationForest
    coords = df[['latitude', 'longitude']].values
    iso_forest = IsolationForest(contamination=0.05)
    df['is_outlier'] = iso_forest.fit_predict(coords)
    df = df[df['is_outlier'] == 1].drop(columns=['is_outlier'])
    
    # Layer 2: Temporal Validation
    df['time_diff'] = df['timestamp'].diff().dt.total_seconds().fillna(0)
    df = df[df['time_diff'] > 0]
    
    logging.info("DataFrame before calculating distance:\n %s", df)

    df['distance'] = haversine_distance(df)
    df['speed'] = df['distance'] / df['time_diff']
    df = df[(df['speed'] < 25) & (df['time_diff'] > 0)]  # 25 m/s (90 km/h) threshold
    total_time = df['time_diff'].sum()
    
    total_distance_km = df['distance'].sum() / 1000  # Convert from meters to kilometers

    # Layer 3: Geospatial Validation using Google Maps
    try:
        if df.empty:
            logging.warning("No data available for geospatial validation.")
            return df, total_time, total_distance_km, df_with_angle_marks  # Return if the DataFrame is empty
        
        import googlemaps
        
        if not google_api_key:
            logging.error("Google Maps API key is required for map matching")
            raise ValueError("Google Maps API key is required but not provided")
        
        # Initialize Google Maps client
        gmaps = googlemaps.Client(key=google_api_key)
        
        logging.info("Using Google Maps API for map matching")
        
        # Google Maps Roads API has a limit on points per request (usually 100)
        # So we'll process in batches
        batch_size = 90  # Slightly less than the limit to be safe
        snapped_points = []
        
        # If we have too many points, sample them to stay within Google's limits
        # Roads API has a limit of 100 points per request and daily quota limits
        if len(df) > 500:
            logging.info(f"Too many points ({len(df)}), sampling down to 500 to avoid API quota issues")
            sample_indices = np.linspace(0, len(df)-1, 500, dtype=int)
            df_sampled = df.iloc[sample_indices].copy()
        else:
            df_sampled = df.copy()
        
        for i in range(0, len(df_sampled), batch_size):
            batch = df_sampled.iloc[i:min(i+batch_size, len(df_sampled))]
            
            # Format points for Google Maps API - Note they need to be in lat,lng order
            path = [[float(row['latitude']), float(row['longitude'])] 
                   for _, row in batch.iterrows()]
            
            logging.info(f"Sending {len(path)} points to Google Maps Roads API")
            
            # Call the snap to roads API
            result = gmaps.snap_to_roads(
                path,
                interpolate=True  # Add points along the road
            )
            
            # Add snapped points to our list
            for point in result:
                snapped_points.append({
                    'latitude': point['location']['latitude'],
                    'longitude': point['location']['longitude']
                })
            
            logging.info(f"Processed {min(i+batch_size, len(df_sampled))}/{len(df_sampled)} points with Google Maps Roads API")
        
        # Create a new DataFrame with the snapped points
        snapped_df = pd.DataFrame(snapped_points)
        
        if len(snapped_df) > 0:
            # Create timestamps for snapped points
            # We'll create timestamps that are evenly distributed across the original timeframe
            original_start = df['timestamp'].min()
            original_end = df['timestamp'].max()
            duration = (original_end - original_start).total_seconds()
            
            timestamps = []
            for i in range(len(snapped_df)):
                fraction = i / (len(snapped_df) - 1) if len(snapped_df) > 1 else 0
                seconds = duration * fraction
                timestamps.append(original_start + pd.Timedelta(seconds=seconds))
            
            snapped_df['timestamp'] = timestamps
            
            # Calculate time differences for the snapped points
            snapped_df['time_diff'] = snapped_df['timestamp'].diff().dt.total_seconds().fillna(0)
            
            # Use the snapped points for further processing
            df = snapped_df
            
            # Recalculate distances and total distance
            df['distance'] = haversine_distance(df)
            total_distance_km = df['distance'].sum() / 1000
            total_time = df['time_diff'].sum()
            
            logging.info(f"Successfully snapped {len(df)} points to roads using Google Maps API")
        else:
            logging.warning("No points were returned from Google Maps API. Using original points.")
    
    except Exception as e:
        logging.error(f"Error during Google Maps geospatial validation: {str(e)}")
        logging.error("Map matching failed. Continuing with original points.")

    # Layer 4: Smoothing & Filtering
    if not df.empty:
        from pykalman import KalmanFilter
        kf = KalmanFilter(transition_matrices=np.eye(2),
                          observation_matrices=np.eye(2),
                          initial_state_mean=df[['latitude', 'longitude']].values[0])
        smoothed, _ = kf.smooth(df[['latitude', 'longitude']].values)
        df[['latitude', 'longitude']] = smoothed
    else:
        logging.warning("Warning: No data after filtering")

    # Layer 5: Data Interpolation
    df.set_index('timestamp', inplace=True)
    logging.info("DataFrame before resampling:\n %s", df)  # Check before resampling
    df = df.resample('5S').mean(numeric_only=True)  # 5-second frequency and calculate mean for numeric columns
    df = df.ffill()  # Forward fill to fill NaN values

    for col in ['latitude', 'longitude']: 
        df[col] = df[col].interpolate(method='linear')

    # 返回多一個參數，即角度可靠性標記後嘅數據
    return df.reset_index(), total_time, total_distance_km, df_with_angle_marks

def add_elevation_data(df, max_batch_size=50, requests_per_second=15, max_retries=3):
    """Fetch elevation data in batches and control request rate automatically."""
    import requests
    import time
    from requests.exceptions import RequestException
    
    # Calling API
    base_url = 'https://api.open-elevation.com/api/v1/lookup'
    total_points = len(df)
    df['elevation'] = 0.0  
    
    for i in range(0, total_points, max_batch_size):
        batch = df.iloc[i:i + max_batch_size]
        locations = [{'latitude': row['latitude'], 'longitude': row['longitude']} 
                     for _, row in batch.iterrows()]
        
        success = False
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    base_url,
                    json={'locations': locations},
                    timeout=10  # Timeout after 10 seconds
                )
                response.raise_for_status()
                
                elevations = [r['elevation'] for r in response.json()['results']]
                df.loc[batch.index, 'elevation'] = elevations
                print(f"Successfully processed {min(i + max_batch_size, total_points)}/{total_points} points")
                success = True
                break  # Exit the retry loop on success
                
            except RequestException as e:
                print(f"Batch {i // max_batch_size + 1} attempt {attempt + 1} failed: {str(e)}")
                time.sleep(2 ** attempt)  # Exponential backoff
                
        if not success:
            print(f"Warning: Batch {i // max_batch_size + 1} ultimately failed, using default values")
            df.loc[batch.index, 'elevation'] = 0.0
        
        # Limit API calling speed
        if i + max_batch_size < total_points:
            time.sleep(1 / requests_per_second)
    
    return df

def analyze_elevation(df):
    """Analyze and return elevation data"""
    if 'elevation' not in df.columns:
        raise ValueError("DataFrame must include elevation row")
    
    df = df.sort_values('timestamp').reset_index(drop=True)
    df['elevation_diff'] = df['elevation'].diff().fillna(0)
    
    positive = df[df['elevation_diff'] > 0]['elevation_diff'].sum()
    negative = df[df['elevation_diff'] < 0]['elevation_diff'].sum()
    
    return {
        'total_ascent': round(abs(positive), 2),
        'total_descent': round(abs(negative), 2),
        'max_elevation': round(df['elevation'].max(), 2),
        'min_elevation': round(df['elevation'].min(), 2)
    }

def calculate_angle(p1, p2, p3):
    """
    改進計算三個連續GPS點之間嘅角度
    返回角度（度數）並打印調試信息
    添加異常處理
    """
    import math
    import numpy as np
    
    try:
        # 喺計算前輸出點嘅坐標，幫助調試
        print(f"計算角度: 點1={p1}, 點2={p2}, 點3={p3}")
        
        # 將經緯度轉換為弧度
        lat1, lon1 = math.radians(float(p1[0])), math.radians(float(p1[1]))
        lat2, lon2 = math.radians(float(p2[0])), math.radians(float(p2[1]))
        lat3, lon3 = math.radians(float(p3[0])), math.radians(float(p3[1]))
        
        # 計算方位角（heading）從點1到點2
        y1 = math.sin(lon2 - lon1) * math.cos(lat2)
        x1 = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1)
        bearing1 = math.atan2(y1, x1)
        
        # 計算方位角從點2到點3
        y2 = math.sin(lon3 - lon2) * math.cos(lat3)
        x2 = math.cos(lat2) * math.sin(lat3) - math.sin(lat2) * math.cos(lat3) * math.cos(lon3 - lon2)
        bearing2 = math.atan2(y2, x2)
        
        # 計算角度差（轉向角）
        angle_diff_rad = bearing2 - bearing1
        
        # 標準化到 [-π, π]
        while angle_diff_rad > math.pi:
            angle_diff_rad -= 2.0 * math.pi
        while angle_diff_rad < -math.pi:
            angle_diff_rad += 2.0 * math.pi
        
        # 我哋要計算嘅係轉彎角度，唔係直行角度
        # 所以我哋需要計算 |π - |angle_diff_rad||
        turning_angle_rad = abs(math.pi - abs(angle_diff_rad))
        
        # 弧度轉角度
        turning_angle_deg = math.degrees(turning_angle_rad)
        
        # 輸出調試信息
        print(f"方位角 1->2: {math.degrees(bearing1):.2f}°, 方位角 2->3: {math.degrees(bearing2):.2f}°")
        print(f"轉向角度: {turning_angle_deg:.2f}°")
        
        return turning_angle_deg
    
    except Exception as e:
        print(f"角度計算中發生錯誤: {str(e)}")
        # 返回一個預設角度，唔會觸發過濾
        return 180.0

def filter_by_angle(df, angle_threshold=90):
    """
    基於三個連續點之間嘅角度過濾GPS數據
    加入更多調試信息，並確保正確處理角度值
    """
    if len(df) < 3:
        df['angle_reliability'] = 'Y'
        df['angle_value'] = None
        return df, df
    
    # 初始化角度可靠性列
    df['angle_reliability'] = 'Y'
    df['angle_value'] = float('nan')  # 使用 NaN 而唔係 None
    
    try:
        # 計算每組三個連續點之間嘅角度
        for i in range(len(df) - 2):
            try:
                p1 = (df.iloc[i]['latitude'], df.iloc[i]['longitude'])
                p2 = (df.iloc[i+1]['latitude'], df.iloc[i+1]['longitude'])
                p3 = (df.iloc[i+2]['latitude'], df.iloc[i+2]['longitude'])
                
                # 檢查座標係咪有效
                if (None in p1 or None in p2 or None in p3 or
                    pd.isna(p1[0]) or pd.isna(p1[1]) or 
                    pd.isna(p2[0]) or pd.isna(p2[1]) or 
                    pd.isna(p3[0]) or pd.isna(p3[1])):
                    print(f"跳過點 {i+1} 因為座標包含 None 或 NaN")
                    continue
                
                angle = calculate_angle(p1, p2, p3)
                
                # 存儲角度值以便查看
                df.loc[df.index[i+1], 'angle_value'] = float(angle)
                
                # 如果角度小於閾值，標記呢三個點為 "X"
                if angle < angle_threshold:
                    df.loc[df.index[i:i+3], 'angle_reliability'] = 'X'
                    print(f"標記為不可靠 (X): 點 {i}, {i+1}, {i+2} 嘅角度為 {angle:.2f}°")
            
            except Exception as e:
                print(f"計算點 {i+1} 嘅角度時出錯: {str(e)}")
                # 繼續處理下一組點
        
        # 創建一個新嘅DataFrame，只保留標記為 "Y" 嘅點
        filtered_df = df[df['angle_reliability'] == 'Y'].copy()
        
        removed_count = len(df) - len(filtered_df)
        print(f"已根據角度可靠性移除 {removed_count} 個點 ({removed_count/len(df)*100:.1f}%)")
        
    except Exception as e:
        print(f"角度過濾過程中發生錯誤: {str(e)}")
        # 如果整個過程出錯，返回原始數據
        filtered_df = df.copy()
    
    return filtered_df, df

# Main function
if __name__ == "__main__":
    # First, process the GPS data
    collection_name = "processed_routes"
    raw_data = retrieve_data_from_firestore(collection_name)

    if not raw_data.empty:
        # Clean the GPS data
        cleaned_data, total_time, total_distance, angle_reliability_data = clean_gps_data(raw_data, "YOUR_API_KEY_HERE")
        
        # Add elevation data
        cleaned_data = add_elevation_data(cleaned_data)
        elevation_stats = analyze_elevation(cleaned_data)
        
        # Calculate emissions
        # Example parameters (you should adjust these based on your vehicle)
        fuel_efficiency = 3.0  # km/L (example for a heavy truck)
        payload_weight = 10.0  # tonnes
        max_payload = 25.0    # tonnes
        co2_emission_factor = 2640  # g/L (diesel)
        
        emissions = calculate_co2_emissions(
            distance=total_distance,
            fuel_efficiency=fuel_efficiency,
            total_elevation_gain=elevation_stats['total_ascent'],
            total_elevation_loss=elevation_stats['total_descent'],
            payload_weight=payload_weight,
            max_payload=max_payload,
            co2_emission_factor=co2_emission_factor,
            total_time=total_time
        )
        
        print(f"\nResults:")
        print(f"Distance: {total_distance:.2f} km")
        print(f"Time: {total_time/3600:.2f} hours")
        print(f"Total Ascent: {elevation_stats['total_ascent']} m")
        print(f"Total Descent: {elevation_stats['total_descent']} m")
        print(f"CO2 Emissions: {emissions:.2f} kg")

        # The processed data is uploaded to the collection specified by 'processed_collection' variable
        db = init_firebase()
        doc_ref = db.collection(collection_name).document(filtered_route_name)
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
    else:
        print("No Data")
