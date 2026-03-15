# Crop Yield Predictor

A Streamlit app that predicts crop yield based on user inputs and real-time weather data.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up PostgreSQL database and run `setup_db.py` to create the table.

3. Get API keys:
   - OpenWeatherMap API key: https://openweathermap.org/api
   - For elevation, we use open-elevation.org (no key needed)

4. Update `.streamlit/secrets.toml` with your API keys and database credentials.

## Running Locally

```
streamlit run app.py
```

## Deployment

### Streamlit Cloud

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo.
4. Set the main file path to `app.py`
5. Add secrets in the app settings.

### Other Platforms

The app can be deployed on Heroku, AWS, etc., with appropriate configurations.

## Features

- User inputs: Crop type, season, location (lat/lon), soil data
- Fetches real-time weather (temperature, rainfall) and elevation
- Predicts yield using trained RandomForest model
- Logs all predictions to PostgreSQL database