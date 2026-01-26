import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from pymongo import MongoClient
import psycopg2

app = Flask(__name__)
app.secret_key = "super_secret_key_for_logistics"

# --- PASTE YOUR CONNECTIONS HERE ---
# Replace with your REAL strings again!
NEON_URL = "postgresql://neondb_owner:npg_UgH9VXp7Sjch@ep-spring-union-abb1gtsa-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require" 
MONGO_URI = "mongodb+srv://admin:0TQJPY1aZXO0BspG@cluster0.2xqktob.mongodb.net/?appName=Cluster0"
# -----------------------------------

# --- DATABASE CONNECTIONS ---

# 1. Connect to NoSQL (MongoDB)
try:
    mongo_client = MongoClient(MONGO_URI)
    mongo_db = mongo_client['smart_logistics_db']
    print("MongoDB Connected.")
except Exception as e:
    print(f"MongoDB Error: {e}")

# 2. Helper for SQL (Neon)
def get_sql_connection():
    return psycopg2.connect(NEON_URL)

def init_sql_table():
    """Creates the table in Neon if it doesn't exist."""
    try:
        conn = get_sql_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS deliveries (
                id SERIAL PRIMARY KEY,
                driver_name VARCHAR(100),
                destination VARCHAR(200),
                status VARCHAR(50)
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("SQL Table checked/created.")
    except Exception as e:
        print(f"SQL Init Error: {e}")

# Run table creation once on startup
init_sql_table()

# --- ROUTES ---

@app.route('/')
def index():
    """
    Main Dashboard Route.
    Fetches delivery data from SQL and calculates real-time statistics
    for the status cards.
    """
    deliveries = []
    # Default counts (if database is empty)
    counts = {"total": 0, "transit": 0, "delivered": 0}
    
    try:
        conn = get_sql_connection()
        cur = conn.cursor()
        
        # 1. Fetch all deliveries
        cur.execute("SELECT * FROM deliveries ORDER BY id DESC")
        deliveries = cur.fetchall()
        
        # 2. Calculate Statistics
        cur.execute("SELECT COUNT(*) FROM deliveries")
        counts["total"] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM deliveries WHERE status='In Transit'")
        counts["transit"] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM deliveries WHERE status='Delivered'")
        counts["delivered"] = cur.fetchone()[0]
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Fetch Error: {e}")

    return render_template('dashboard.html', deliveries=deliveries, counts=counts)

@app.route('/about')
def about():
    """Renders the About Us page."""
    return render_template('about.html')

@app.route('/create-delivery', methods=['POST'])
def create_delivery():
    """
    Handles form submission.
    1. Saves relational data to Neon PostgreSQL.
    2. Saves audit logs to MongoDB Atlas.
    """
    driver = request.form['driver']
    destination = request.form['destination']
    
    # 1. Save to SQL
    try:
        conn = get_sql_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO deliveries (driver_name, destination, status) VALUES (%s, %s, %s) RETURNING id",
            (driver, destination, "In Transit")
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        # 2. Save Audit Log to NoSQL
        log_entry = {
            "related_delivery_id": new_id,
            "event": "DELIVERY_CREATED",
            "timestamp": datetime.datetime.now(),
            "notes": f"Driver {driver} assigned to {destination}."
        }
        mongo_db.logs.insert_one(log_entry)
        
    except Exception as e:
        print(f"Create Error: {e}")

    flash("New delivery created successfully!", "success")    

    return redirect(url_for('index'))

@app.route('/delete/<int:id>', methods=['POST'])
def delete_delivery(id):
    try:
        conn = get_sql_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM deliveries WHERE id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Delete Error: {e}")
    
    flash("Delivery deleted.", "danger")

    return redirect(url_for('index'))

@app.route('/complete/<int:id>', methods=['POST'])
def complete_delivery(id):
    try:
        conn = get_sql_connection()
        cur = conn.cursor()
        cur.execute("UPDATE deliveries SET status = 'Delivered' WHERE id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Update Error: {e}")

    flash("Delivery marked as completed.", "success")
    
    return redirect(url_for('index'))

@app.route('/test-db')
def test_databases():
    """Displays the System Status UI Page."""
    sql_status = "Unknown"
    nosql_status = "Unknown"

    # Test SQL
    try:
        conn = get_sql_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.close()
        conn.close()
        sql_status = "Connected Successfully"
    except Exception as e:
        sql_status = f"Connection Failed: {str(e)}"

    # Test NoSQL
    try:
        mongo_client.admin.command('ping')
        nosql_status = "Connected Successfully"
    except Exception as e:
        nosql_status = f"Connection Failed: {str(e)}"

    return render_template('status.html', sql_status=sql_status, nosql_status=nosql_status)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/api/deliveries')
def api_get_deliveries():
    """REST API: Returns JSON data for external systems."""
    try:
        conn = get_sql_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, driver_name, destination, status FROM deliveries")
        rows = cur.fetchall()
        
        data = []
        for row in rows:
            data.append({
                "id": row[0],
                "driver": row[1],
                "destination": row[2],
                "status": row[3]
            })
            
        cur.close()
        conn.close()
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)