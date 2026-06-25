import sqlite3
import pandas as pd
import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the Groq client 
# We'll import this client into our agent.py in the next step
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def init_db_from_df(df: pd.DataFrame) -> sqlite3.Connection:
    """
    Creates an in-memory SQLite database and loads the transactions DataFrame.
    """
    # Create a connection to an in-memory database
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    
    # Push the dataframe to a table named 'transactions'
    # We use index=False so the pandas index doesn't become a weird column
    df.to_sql('transactions', conn, index=False, if_exists='replace')
    
    return conn

def get_table_schema(conn: sqlite3.Connection, table_name: str = 'transactions') -> str:
    """
    Retrieves the table schema AND unique categories/types so we can inject it into the LLM prompt.
    """
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    
    schema_str = f"Table: {table_name}\nColumns:\n"
    for col in columns:
        schema_str += f"- {col[1]} ({col[2]})\n"
        
    # Fetch unique categories
    try:
        cursor.execute(f"SELECT DISTINCT category FROM {table_name} WHERE category IS NOT NULL;")
        categories = [row[0] for row in cursor.fetchall()]
        schema_str += f"\nExact Available Categories in 'category' column:\n{', '.join(categories)}\n"
    except Exception:
        pass 
        
    # --- NEW: Fetch unique types (Debit/Credit) ---
    try:
        cursor.execute(f"SELECT DISTINCT type FROM {table_name} WHERE type IS NOT NULL;")
        types = [row[0] for row in cursor.fetchall()]
        schema_str += f"\nExact Available Values in 'type' column:\n{', '.join(types)}\n"
    except Exception:
        pass
        
    return schema_str

# --- Quick Test Block ---
if __name__ == "__main__":
    # Create a dummy dataframe to test the engine
    dummy_data = pd.DataFrame({
        "date": ["2024-03-01", "2024-03-02"],
        "vendor": ["ZOMATO", "UBER"],
        "amount": [450.0, 200.0],
        "type": ["Debit", "Debit"],
        "category": ["Food & Coffee", "Transport"]
    })
    
    test_conn = init_db_from_df(dummy_data)
    schema = get_table_schema(test_conn)
    
    print("Database Initialized!")
    print("\nSchema extracted for the LLM:")
    print(schema)
    
    # Test Groq API Key
    try:
        models = groq_client.models.list()
        print("\nGroq API Key is valid! Ready for Step 2.")
    except Exception as e:
        print(f"\nGroq Error: {e}")