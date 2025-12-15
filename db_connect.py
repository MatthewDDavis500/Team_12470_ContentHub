import mysql.connector
from mysql.connector import pooling
import os
from dotenv import load_dotenv
load_dotenv() 

# This file sets up a connection pool to a MySQL database using environment variables for configuration.
# I'm loading environment variables from a .env file as it doesn't let me push secrets to GitHub.
db_config = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'connect_timeout': 10
}

print("--- DEBUGGING DB CONFIG ---")
print(f"Host: {db_config['host']}")
print(f"User: {db_config['user']}")
print(f"Port: {db_config['port']}")
print("---------------------------")

# This is to create a pool (Keeps 3 connections open and ready to use)
# This should run once when the app starts.
try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="widget_pool",
        pool_size=3,  # Keep 3 lines open
        pool_reset_session=True,
        **db_config
    )
    print(">> Database Connection Pool Created")
except Exception as e:
    print(f"Error creating pool: {e}")
    connection_pool = None

# This is a helper function to get a connection from the pool
"""
    Instead of connecting to the cloud every time (Slow),
    we just borrow a connection from the pool (Instant).
"""
def get_db_connection():

    if connection_pool:
        return connection_pool.get_connection()
    else:
        # Fallback if pool failed
        return mysql.connector.connect(**db_config)