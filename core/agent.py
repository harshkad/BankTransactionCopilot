import os
import sqlite3
import pandas as pd
from groq import Groq
import re
from dotenv import load_dotenv

# We import the schema generator from our previous step
from core.database import get_table_schema, init_db_from_df

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
# Using Llama 3 70B for the agent as it's excellent at coding/SQL
# Using the latest Llama 3.3 70B versatile model for coding/SQL
MODEL_NAME = "llama-3.3-70b-versatile"

def generate_sql(question: str, schema: str) -> str:
    """
    Asks the LLM to translate a natural language question into an SQL query.
    """
    prompt = f"""
    You are an expert SQL data analyst working with a SQLite database. 
    Your job is to write a SQL query to answer the user's question.
    
    Here is the schema for the database:
    {schema}
    
    Rules:
    1. Only use the columns listed in the schema.
    2. The user's input might have typos, lowercase letters, bad grammar, or missing punctuation. Understand the core intent.
    3. When filtering by string columns (like category or vendor), ALWAYS use case-insensitive matching. For example, use: LOWER(category) LIKE LOWER('%food%').
    4. Intelligently map the user's informal terms (e.g., "food", "travel") to the exact 'Available Categories' provided in the schema.
    5. For the 'type' column, ONLY use the Exact Available Values provided in the schema (e.g., 'Debit' or 'Credit'). NEVER use words like 'expense'.
    6. Return ONLY the raw SQL query. Do not include markdown formatting like ```sql.
    7. Do not include any explanations or conversational text. Just the code.
    
    User Question: "{question}"
    SQL Query:
    """
    
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=MODEL_NAME,
        temperature=0.1, 
    )
    
    raw_sql = response.choices[0].message.content.strip()
    clean_sql = re.sub(r'```sql\n|\n```|```', '', raw_sql).strip()
    return clean_sql

def execute_sql(conn: sqlite3.Connection, query: str) -> str:
    """
    Executes the generated SQL against our database and formats the results.
    """
    try:
        # We use pandas to run the query because it naturally formats 
        # the output into a nice readable string for the next LLM step.
        result_df = pd.read_sql_query(query, conn)
        
        if result_df.empty:
            return "No data found for this query."
            
        return result_df.to_string(index=False)
        
    except Exception as e:
        return f"SQL Error: {str(e)}"

def generate_final_response(question: str, raw_data: str) -> str:
    """
    Takes the raw data from the database and turns it into a natural response.
    """
    prompt = f"""
    You are a helpful, encouraging Personal Finance AI. 
    A user asked you a question about their spending, and you queried their database to find the answer.
    
    User Question: "{question}"
    Database Result: 
    {raw_data}
    
    Rules for your response:
    1. Answer the question naturally and concisely using ONLY the provided database result.
    2. ALWAYS format monetary values using the Indian Rupee symbol (₹) and the Indian numbering format. Never use the dollar sign ($).
    3. Do not mention SQL, databases, or how you got the data. Just give them the answer naturally.
    """
    
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
        temperature=0.5, 
    )
    
    return response.choices[0].message.content.strip()

def ask_copilot(question: str, conn: sqlite3.Connection) -> dict:
    """
    The master function that orchestrates the whole agentic workflow.
    """
    schema = get_table_schema(conn)
    
    # Step 1: Think (Write SQL)
    sql_query = generate_sql(question, schema)
    
    # Step 2: Act (Run SQL)
    data_result = execute_sql(conn, sql_query)
    
    # Step 3: Respond (Draft text)
    final_text = generate_final_response(question, data_result)
    
    # We return the query and data as well for debugging or showing the user in the UI later
    return {
        "answer": final_text,
        "sql_used": sql_query,
        "raw_data": data_result
    }

# --- Quick Test Block ---
if __name__ == "__main__":
    # Create the same dummy dataframe from Step 1 to test
    dummy_data = pd.DataFrame({
        "date": ["2024-03-01", "2024-03-02", "2024-03-05"],
        "vendor": ["ZOMATO", "UBER", "SWIGGY INSTAMART"],
        "amount": [450.0, 200.0, 1250.0],
        "type": ["Debit", "Debit", "Debit"],
        "category": ["Food & Coffee", "Transport", "Groceries"]
    })
    
    test_conn = init_db_from_df(dummy_data)
    
    print("Agent Initialized. Testing a query...\n")
    
    test_question = "How much did I spend on Groceries in total?"
    print(f"User: {test_question}")
    
    result = ask_copilot(test_question, test_conn)
    
    print("\n--- Agent Inner Monologue ---")
    print(f"Generated SQL: {result['sql_used']}")
    print(f"Database Output:\n{result['raw_data']}")
    
    print("\n--- Final Output to User ---")
    print(f"Co-pilot: {result['answer']}")
