import os
import sqlite3
import json
from typing import Optional, Dict, Union, Any
from openai import OpenAI
from dotenv import load_dotenv
from utils import (
    get_db_connection,
    load_csv_to_db,
    execute_query,
    list_tables,
    get_table_schema
)

# Load environment variables
load_dotenv()

# Initialize OpenAI client with API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")

def get_schema_description(conn: sqlite3.Connection) -> str:
    """Get a formatted description of all table schemas."""
    tables = list_tables(conn)
    schemas = {}
    for table in tables:
        schemas[table] = get_table_schema(conn, table)
    
    return "\n".join([
        f"""- {table} ({', '.join([f"{col['name']} ({col['type']})" for col in cols])})"""
        for table, cols in schemas.items()
    ])

def process_natural_language(question: str, conn: sqlite3.Connection) -> Dict[str, Any]:
    """Process natural language input and determine intent and action."""
    try:
        schema_desc = get_schema_description(conn)
        
        # Create prompt with examples and intent descriptions
        prompt = f"""You are an AI assistant helping users interact with a spreadsheet database. Based on the user's input, either:
1. Return a command intent in JSON format
2. Generate an SQL query for data questions

Available tables and their schemas:
{schema_desc}

Intent examples:
1. List Tables Intent:
   - "Show me the tables"
   - "What tables are loaded?"
   - "Display database structure"
   - "Which tables do I have?"
   Response: {{"intent": "list_tables"}}

2. Load File Intent:
   - "Upload my data file"
   - "Load sales.csv"
   - "Import the CSV file"
   - "Can you load customer_data.csv?"
   Response: {{"intent": "load_csv", "filename": "<filename>"}}

3. Exit Intent:
   - "Quit"
   - "Exit"
   - "Bye"
   Response: {{"intent": "exit"}}

4. Data Query Intent (return SQL):
   - "Show total revenue this month"
   - "Get average price per product"
   - "What are the top selling items?"
   - "Display sales by region"
   Response: <appropriate SQL query>

User input: "{question}"

If the input matches a command intent (list_tables, load_csv, exit), return a JSON response.
If it's a data query, return only the SQL query without any JSON formatting.
"""

        # Get response from OpenAI using new client-based approach
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a database assistant that returns either JSON command intents or SQL queries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=150
        )
        
        result = response.choices[0].message.content.strip()
        
        # Try to parse as JSON first
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            # If not JSON, assume it's an SQL query
            return {"intent": "generate_sql", "query": result}
    
    except Exception as e:
        print(f"Error processing natural language: {str(e)}")
        return {"intent": "error", "message": str(e)}

def handle_intent(intent_data: Dict[str, Any], conn: sqlite3.Connection) -> None:
    """Handle different intents and execute appropriate actions."""
    intent = intent_data.get("intent")
    
    if intent == "list_tables":
        tables = list_tables(conn)
        if tables:
            print("\nAvailable tables:")
            for table in tables:
                print(f"- {table}")
        else:
            print("No tables found in database")
    
    elif intent == "load_csv":
        filename = intent_data.get("filename")
        if filename:
            if load_csv_to_db(filename):
                print(f"Successfully loaded {filename}")
            else:
                print(f"Failed to load {filename}")
        else:
            print("No filename provided")
    
    elif intent == "generate_sql":
        query = intent_data.get("query")
        if query:
            print(f"\nGenerated SQL:\n{query}")
            results = execute_query(conn, query)
            if results:
                print("\nResults:")
                for row in results:
                    print(row)
            else:
                print("No results found")
    
    elif intent == "exit":
        conn.close()
        print("Goodbye!")
        exit(0)
    
    elif intent == "error":
        print(f"Error: {intent_data.get('message', 'Unknown error')}")
    
    else:
        print("Unknown intent")

def main():
    """Main CLI interface."""
    print("Welcome to the Chat-Based Spreadsheet Tool!")
    print("You can:")
    print("- Load CSV files (e.g., 'Load sales.csv' or 'Import my data')")
    print("- View tables (e.g., 'Show tables' or 'What data do I have?')")
    print("- Query data (e.g., 'Show total revenue' or 'Get top products')")
    print("- Exit (e.g., 'quit' or 'bye')")
    
    conn = get_db_connection()
    
    while True:
        try:
            user_input = input("\nWhat would you like to do? ").strip()
            
            # Process all input through natural language understanding
            intent_data = process_natural_language(user_input, conn)
            handle_intent(intent_data, conn)
            
        except Exception as e:
            print(f"Error: {str(e)}")
            continue

if __name__ == "__main__":
    main() 