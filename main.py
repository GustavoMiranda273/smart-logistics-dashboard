import os
from flask import Flask, jsonify, render_template
from pymongo import MongoClient
import psycopg2

app = Flask(__name__)

# --- CONFIGURATION ---
# In production (GAE), these come from app.yaml env_variables.
# Locally, make sure you set them or use a .env file.
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://admin:<db_password>@cluster0.2xqktob.mongodb.net/?appName=Cluster0')
NEON_URL = os.environ.get('NEON_DB_URL','postgresql://neondb_owner:npg_UgH9VXp7Sjch@ep-spring-union-abb1gtsa-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require')

# --- DATABASE CONNECTIONS ---
# 1. NoSQL Connection (MongoDB)
try:
    mongo_client = MongoClient(MONGO_URI)
    mongo_db = mongo_client['smart_logistics_db']
    print("Connected to MongoDB successfully.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

# 2. SQL Connection (Neon Postgres)
def get_sql_connection():
    """Establishes a connection to the Neon SQL database."""
    conn = psycopg2.connect(NEON_URL)
    return conn

# --- ROUTES ---

@app.route('/')
def index():
    """Landing page to prove the app is running."""
    return "<h1>Smart Logistics Dashboard</h1><p>System Status: Online</p>"

@app.route('/test-db')
def test_databases():
    """
    A diagnostic route to prove to markers that BOTH databases are connected.
    Visit /test-db to see the results.
    """
    results = {
        "sql_status": "Unknown",
        "nosql_status": "Unknown"
    }
    
    # Test SQL (Neon)
    try:
        conn = get_sql_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.close()
        conn.close()
        results["sql_status"] = "Connected (Neon PostgreSQL)"
    except Exception as e:
        results["sql_status"] = f"Failed: {str(e)}"

    # Test NoSQL (MongoDB)
    try:
        # The ismaster command is cheap and fast
        mongo_client.admin.command('ismaster')
        results["nosql_status"] = "Connected (MongoDB Atlas)"
    except Exception as e:
        results["nosql_status"] = f"Failed: {str(e)}"
        
    return jsonify(results)

if __name__ == '__main__':
    # This is used when running locally only. When deploying to GAE,
    # a webserver process such as Gunicorn will serve the app.
    app.run(host='127.0.0.1', port=8080, debug=True)