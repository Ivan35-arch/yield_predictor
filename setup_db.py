import psycopg2

# Connect to PostgreSQL
conn = psycopg2.connect(
    host="your_host",
    database="yield_database",
    user="your_user",
    password="your_password"
)

# Create table
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    crop_type VARCHAR(50),
    season VARCHAR(50),
    county VARCHAR(50),
    latitude FLOAT,
    longitude FLOAT,
    soil_ph FLOAT,
    soil_moisture FLOAT,
    fertilizer_usage FLOAT,
    temperature FLOAT,
    rainfall FLOAT,
    altitude FLOAT,
    yield_prediction FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")
conn.commit()
cur.close()
conn.close()

print("Database table created.")