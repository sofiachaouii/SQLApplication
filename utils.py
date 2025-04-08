import sqlite3
import pandas as pd
import logging
from typing import List, Dict, Optional
import os
from datetime import datetime

# Set up logging
logging.basicConfig(
    filename='error_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_db_connection(db_name: str = 'spreadsheet.db') -> sqlite3.Connection:
    """Create and return a database connection."""
    return sqlite3.connect(db_name)

def infer_schema(df: pd.DataFrame) -> Dict[str, str]:
    """Infer SQLite schema from pandas DataFrame."""
    type_mapping = {
        'object': 'TEXT',
        'int64': 'INTEGER',
        'float64': 'REAL',
        'datetime64[ns]': 'TEXT'
    }
    
    schema = {}
    for column in df.columns:
        dtype = str(df[column].dtype)
        schema[column] = type_mapping.get(dtype, 'TEXT')
    return schema

def create_table_sql(table_name: str, schema: Dict[str, str]) -> str:
    """Generate CREATE TABLE SQL statement."""
    columns = [f"{col} {dtype}" for col, dtype in schema.items()]
    return f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"

def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    """Check if a table exists in the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

def get_table_schema(conn: sqlite3.Connection, table_name: str) -> List[Dict]:
    """Get schema information for a table."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [{'name': row[1], 'type': row[2]} for row in cursor.fetchall()]

def load_csv_to_db(csv_path: str, table_name: Optional[str] = None) -> bool:
    """Load CSV file into SQLite database with schema inference."""
    try:
        # Read CSV file
        df = pd.read_csv(csv_path)
        
        # Generate table name if not provided
        if not table_name:
            table_name = os.path.splitext(os.path.basename(csv_path))[0]
        
        # Get database connection
        conn = get_db_connection()
        
        # Check if table exists
        if table_exists(conn, table_name):
            logging.warning(f"Table {table_name} already exists")
            return False
        
        # Infer schema and create table
        schema = infer_schema(df)
        create_sql = create_table_sql(table_name, schema)
        conn.execute(create_sql)
        
        # Insert data
        df.to_sql(table_name, conn, if_exists='append', index=False)
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logging.error(f"Error loading CSV: {str(e)}")
        return False

def execute_query(conn: sqlite3.Connection, query: str) -> List[Dict]:
    """Execute SQL query and return results as list of dictionaries."""
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [description[0] for description in cursor.description]
        results = cursor.fetchall()
        return [dict(zip(columns, row)) for row in results]
    except Exception as e:
        logging.error(f"Error executing query: {str(e)}")
        return []

def list_tables(conn: sqlite3.Connection) -> List[str]:
    """List all tables in the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return [row[0] for row in cursor.fetchall()] 