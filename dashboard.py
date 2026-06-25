import streamlit as st
import pandas as pd
import re
import io

# Import our AI backend
from core.database import init_db_from_df
from core.agent import ask_copilot

# --- 1. THE EXPANDED BRAIN ---
CATEGORY_MAP = {
    # Food & Coffee
    'STARBUCKS': 'Food & Coffee', 'ZOMATO': 'Food & Coffee', 'CAFE COFFEE DAY': 'Food & Coffee',
    'SUBWAY': 'Food & Coffee', 'MCDONALDS': 'Food & Coffee', 'DOMINOS': 'Food & Coffee',
    'LOCAL TEA SHOP': 'Food & Coffee', 'CHAI SUTTA BAR': 'Food & Coffee',

    # Groceries
    'SWIGGY INSTAMART': 'Groceries', 'BIGBASKET': 'Groceries', 'D-MART': 'Groceries', 
    'BLINKIT': 'Groceries', 'LOCAL SUPERMART': 'Groceries', 'ZEPTO': 'Groceries',

    # Transport
    'UBER': 'Transport', 'OLA CABS': 'Transport', 'RAPIDO': 'Transport', 
    'DELHI METRO': 'Transport', 'NEMMA METRO': 'Transport',
    
    # Bills & Utilities
    'PAYTM BILL PAY': 'Bills & Utilities', 'BSES YAMUNA POWER': 'Bills & Utilities', 
    'VODAFONE IDEA': 'Bills & Utilities', 'AIRTEL PREPAID': 'Bills & Utilities', 
    'MTNL DELHI': 'Bills & Utilities', 'JIO RECHARGE': 'Bills & Utilities', 
    'ACT FIBERNET': 'Bills & Utilities',

    # Subscriptions
    'NETFLIX': 'Subscriptions', 'SPOTIFY AB': 'Subscriptions', 'GOOGLE PLAY': 'Subscriptions',
    'AMAZON PRIME': 'Subscriptions', 'DISNEY+ HOTSTAR': 'Subscriptions', 
    'THE HINDU NEWS': 'Subscriptions', 'YOUTUBE PREMIUM': 'Subscriptions',

    # Shopping
    'AMAZON SVCS': 'Shopping', 'FLIPKART': 'Shopping', 'MYNTRA': 'Shopping',
    'ZARA': 'Shopping', 'H&M': 'Shopping', 'DELL INDIA': 'Tech/Hardware',
    'RELIANCE TRENDS': 'Shopping',
    
    # Housing & Travel
    'PROPERTY RENTALS': 'Housing', 'IKEA': 'Housing',
    'AIRBNB': 'Travel', 'MAKE MY TRIP': 'Travel', 'GOIBIBO': 'Travel', 'INDIGO FLIGHT': 'Travel',

    # Fuel & Auto
    'SHELL PETROL': 'Fuel & Auto', 'INDIAN OIL': 'Fuel & Auto', 
    'MARUTI SUZUKI SVC': 'Fuel & Auto', 'BHARAT PETROLEUM': 'Fuel & Auto',
    
    # Health & Entertainment
    'APOLLO PHARMACY': 'Health & Wellness', 'CULT FIT': 'Health & Wellness', 'NETMEDS': 'Health & Wellness',
    'BOOKMYSHOW': 'Entertainment', 'PVR CINEMAS': 'Entertainment',
    
    # Finance & Income
    'SALARY': 'Income', 'FREELANCE': 'Income', 
    'REFUND': 'Refunds/Reimbursements', 'CASHBACK': 'Refunds/Reimbursements',
    'ATM WITHDRAWAL': 'Bank/Finance', 'BANK FEE': 'Bank/Finance',
}

def format_indian_currency(number):
    """Formats a number into the Indian numbering system."""
    s = f"{number:.2f}"
    parts = s.split('.')
    integer_part = parts[0]
    decimal_part = parts[1]
    sign = "-" if integer_part.startswith('-') else ""
    if sign: integer_part = integer_part[1:]
    
    l = len(integer_part)
    if l <= 3:
        formatted_integer = integer_part
    else:
        last_three = integer_part[-3:]
        other_digits = integer_part[:-3]
        other_digits_with_commas = ','.join([other_digits[max(i-2, 0):i] for i in range(len(other_digits), 0, -2)][::-1])
        formatted_integer = other_digits_with_commas + ',' + last_three
    return f"₹{sign}{formatted_integer}.{decimal_part}"

def parse_transaction(email_body):
    """Extracts data with bulletproof regex and strict typing."""
    # Matches Rs., INR, or $ just in case bad data slips through
    amount_re = re.search(r"(Rs\.|INR|\$)\s*([\d,]+\.?\d{2})", email_body, re.IGNORECASE)
    date_re = re.search(r"on\s+(\d{1,2}-[A-Za-z]{3}-\d{4})", email_body, re.IGNORECASE)
    
    # Strict Type Mapping
    type_ = "Debit"
    body_lower = email_body.lower()
    if "credit" in body_lower or "received" in body_lower or "credited" in body_lower or "refund" in body_lower:
        type_ = "Credit"
        
    vendor = "Other"
    email_upper = email_body.upper()
    
    # Map Vendor
    for key in CATEGORY_MAP.keys():
        if key in email_upper:
            vendor = key
            break
            
    # Hard overrides for tricky credit formats
    if type_ == "Credit":
        if "SALARY" in email_upper: vendor = "SALARY"
        elif "FREELANCE" in email_upper: vendor = "FREELANCE"
        elif "REFUND" in email_upper: vendor = "REFUND"
            
    if amount_re and date_re:
        amount_str = amount_re.group(2).replace(",", "")
        amount = float(amount_str)
        date = date_re.group(1).upper()
        return {"date": date, "vendor": vendor, "amount": amount, "type": type_}
    return None

def process_data(raw_data_list):
    processed_data = []
    for email in raw_data_list:
        if email.strip():
            data = parse_transaction(email)
            if data:
                processed_data.append(data)
    
    if not processed_data:
        return pd.DataFrame(columns=["date", "vendor", "amount", "type", "category"])

    df = pd.DataFrame(processed_data)
    df['category'] = df['vendor'].map(CATEGORY_MAP).fillna('Other')
    df['date'] = pd.to_datetime(df['date'], format='%d-%b-%Y')
    df = df.sort_values(by='date')
    return df

# --- Streamlit UI ---
st.set_page_config(layout="wide", page_title="Finance Co-Pilot")
st.title("📊 Bank Transaction Visualizer & AI Co-Pilot")

uploaded_file = st.file_uploader("Upload your transactions.txt file", type=["txt"])

if uploaded_file is not None:
    string_io = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
    raw_data_list = string_io.read().splitlines()
    df = process_data(raw_data_list)
    
    # Force the database connection to refresh if a new file is uploaded
    if "db_conn" not in st.session_state or st.button("Refresh Database Engine"):
        st.session_state.db_conn = init_db_from_df(df)
        st.success("Database Engine Initialized with latest data!")

    expenses_df = df[df['type'] == 'Debit'].copy()
    income_df = df[df['type'] == 'Credit'].copy()

    # Dashboard Elements
    st.header("Key Metrics")
    total_spent = expenses_df['amount'].sum()
    total_income = income_df['amount'].sum()
    net_flow = total_income - total_spent

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Spent", format_indian_currency(total_spent))
    m2.metric("Total Income", format_indian_currency(total_income))
    m3.metric("Net Cash Flow", format_indian_currency(net_flow))
    
    st.divider()
    
    st.header("Expense Dashboard")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Spending by Category")
        category_spending = expenses_df.groupby('category')['amount'].sum()
        st.bar_chart(category_spending)
    with col2:
        st.subheader("Spending Over Time")
        daily_spending = expenses_df.set_index('date').resample('D')['amount'].sum()
        st.line_chart(daily_spending)

    st.divider()

    # --- AI Co-Pilot Chat Interface ---
    st.header("💬 Financial Co-Pilot")
    st.markdown("Ask me anything about your spending habits, trends, or specific transactions.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "metadata" in message:
                with st.expander("Agent Reasoning (SQL & Raw Data)"):
                    st.code(message["metadata"]["sql_used"], language="sql")
                    st.text(message["metadata"]["raw_data"])

    if prompt := st.chat_input("E.g., How much did I spend on Zomato this month?"):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Thinking & querying database..."):
                response_data = ask_copilot(prompt, st.session_state.db_conn)
                st.markdown(response_data["answer"])
                
                with st.expander("Agent Reasoning (SQL & Raw Data)"):
                    st.code(response_data["sql_used"], language="sql")
                    st.text(response_data["raw_data"])
                    
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response_data["answer"],
            "metadata": response_data
        })

else:
    st.info("Please upload a .txt file to get started.")