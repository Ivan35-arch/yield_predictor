import streamlit as st
import joblib
import requests
import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder, StandardScaler
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Load the model and preprocessors
model = joblib.load('yield_predictor_model.pkl')
encoder = joblib.load('encoder.pkl')
scaler = joblib.load('scaler.pkl')

# API Keys (use Streamlit secrets in production)
OPENWEATHER_API_KEY = st.secrets.get("OPENWEATHER_API_KEY", "your_openweather_api_key")
# For elevation, we can use open-elevation.org which doesn't require API key

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host=st.secrets.get("DB_HOST", "localhost"),
        database=st.secrets.get("DB_NAME", "yield_database"),
        user=st.secrets.get("DB_USER", "user"),
        password=st.secrets.get("DB_PASS", "password")
    )

# Function to get weather data
def get_weather_data(lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temperature = data['main']['temp']
        rainfall = data.get('rain', {}).get('1h', 0)  # Rainfall in last hour, default 0
        return temperature, rainfall
    else:
        st.error("Failed to fetch weather data")
        return None, None

# Function to get elevation
def get_elevation(lat, lon):
    url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['results'][0]['elevation']
    else:
        st.error("Failed to fetch elevation data")
        return None

# Function to get county from lat/lon (simple reverse geocoding using Nominatim)
def get_county(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
    response = requests.get(url, headers={'User-Agent': 'YieldPredictorApp/1.0'})
    if response.status_code == 200:
        data = response.json()
        address = data.get('address', {})
        county = address.get('county') or address.get('state') or address.get('city')
        return county
    else:
        st.error("Failed to fetch location data")
        return None

# Function to log to database
def log_prediction(crop_type, season, county, lat, lon, soil_ph, soil_moisture, fertilizer_usage, temperature, rainfall, altitude, prediction):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO predictions (crop_type, season, county, latitude, longitude, soil_ph, soil_moisture, fertilizer_usage, temperature, rainfall, altitude, yield_prediction)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (crop_type, season, county, lat, lon, soil_ph, soil_moisture, fertilizer_usage, temperature, rainfall, altitude, prediction))
    conn.commit()
    cur.close()
    conn.close()

# Streamlit app
st.title("Crop Yield Predictor")

st.sidebar.header("User Inputs")

# Crop data
crop_type = st.sidebar.selectbox("Crop Type", ["Maize", "Beans", "Wheat", "Sorghum", "Millet"])
season = st.sidebar.selectbox("Season", ["Long Rains", "Short Rains"])

# Location
lat = st.sidebar.number_input("Latitude", value=-0.0236, format="%.4f")
lon = st.sidebar.number_input("Longitude", value=37.9062, format="%.4f")

# Soil data
soil_ph = st.sidebar.number_input("Soil pH", min_value=0.0, max_value=14.0, value=6.5)
soil_moisture = st.sidebar.number_input("Soil Moisture (%)", min_value=0.0, max_value=100.0, value=50.0)
fertilizer_usage = st.sidebar.number_input("Fertilizer Usage (kg/ha)", min_value=0.0, value=100.0)

if st.sidebar.button("Predict Yield"):
    # Get county
    county = get_county(lat, lon)
    if not county:
        st.error("Could not determine county from location")
        st.stop()

    # Get weather data
    temperature, rainfall = get_weather_data(lat, lon)
    if temperature is None:
        st.error("Could not fetch weather data")
        st.stop()

    # Get elevation
    altitude = get_elevation(lat, lon)
    if altitude is None:
        st.error("Could not fetch elevation data")
        st.stop()

    # Prepare input data
    input_data = pd.DataFrame({
        'crop_type': [crop_type],
        'season': [season],
        'county': [county],
        'soil_ph': [soil_ph],
        'soil_moisture': [soil_moisture],
        'fertilizer_usage': [fertilizer_usage],
        'temperature': [temperature],
        'rainfall': [rainfall],
        'altitude': [altitude]
    })

    # Encode categoricals
    cat_data = input_data[['crop_type', 'season', 'county']]
    encoded_cat = encoder.transform(cat_data)
    encoded_df = pd.DataFrame(encoded_cat.toarray(), columns=encoder.get_feature_names_out(['crop_type', 'season', 'county']))

    # Combine
    num_data = input_data[['soil_ph', 'soil_moisture', 'fertilizer_usage', 'temperature', 'rainfall', 'altitude']]
    full_input = pd.concat([encoded_df, num_data], axis=1)

    # Scale
    input_scaled = scaler.transform(full_input)

    # Predict
    prediction = model.predict(input_scaled)[0]

    # Display results
    st.success(f"Predicted Yield: {prediction:.2f} kg/ha")

    # Log to database
    try:
        log_prediction(crop_type, season, county, lat, lon, soil_ph, soil_moisture, fertilizer_usage, temperature, rainfall, altitude, prediction)
        st.info("Prediction logged to database")
    except Exception as e:
        st.error(f"Failed to log to database: {e}")

    # Display fetched data
    st.subheader("Fetched Data")
    st.write(f"Temperature: {temperature} °C")
    st.write(f"Rainfall: {rainfall} mm")
    st.write(f"Altitude: {altitude} m")
    st.write(f"County: {county}")