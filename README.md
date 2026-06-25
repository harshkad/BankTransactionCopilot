> [!IMPORTANT]
> This project is a significant upgrade to my original [Bank Transaction Visualizer](https://github.com/harshkad/BankTransactionVisualizer) made in mid 2025. While the previous version focused on static dashboard visualizations, this version introduces an Agentic AI Co-Pilot, now skip the charts and simply chat with your transaction history.

<br>

### Bank Transaction Co-Pilot

A simple web app that turns messy bank text alerts into a beautiful financial dashboard and lets you chat with your expenses.

<br>

###  About The Project

This project implements an **Agentic Text-to-SQL Architecture**. It allows users to drop a raw text file (`.txt`) of unstructured transaction histories (SMS/Email alerts) into a clean Streamlit interface. The application extracts the data deterministically using regular expressions, structures it using Pandas, spins up an in-memory SQLite database, and hands over control to a dynamic LLM agent powered by Groq. Users can chat with their finances using pure natural language (e.g., *"how much did I spent on food and coffee"* or *"what was my highest single expense"*), getting instant, accurate, and grounded answers.

<br>

### System Architecture & Workflow

Rather than passing raw text data directly to the LLM or embedding it into a vector store (which fails at calculations like mathematical aggregations or group-by filtering), this system separates **reasoning** from **computation**:

```text
[Raw .txt File] ──> [Regex & Pandas Pipeline] ──> [In-Memory SQLite Database]
                                                            │
                                                     (Schema Extracted)
                                                            ▼
[Natural Language Query] ───────────────────────────> [Groq Agent Engine]
                                                            │
                                                    (Generates Strict SQL)
                                                            ▼
[Natural Language Response] <── [Llama 3.1 Synthesis] <── [SQL Execution Output]

```

1. **Ingestion & Extraction:** Reads unstructured string logs line-by-line and extracts transactions via advanced pattern matching (Regex).
2. **Deterministic Modeling:** Cleans, types, and maps vendors to explicit behavioral categories inside a unified Pandas DataFrame.
3. **Database Engine Initialization:** Migrates the live DataFrame into an isolated, multi-thread safe in-memory SQLite database instance at runtime.
4. **Dynamic Schema Injection:** Queries the live database system metadata (`PRAGMA table_info`) alongside unique categorical strings and feeds this fresh blueprint into the agent prompt.
5. **Agentic Inference:** Utilizes `llama-3.3-70b-versatile` via the ultra-fast Groq API at a low temperature to construct syntactically correct SQLite statements.
6. **Programmatic Execution:** Safely runs the generated SQL string directly against the local database, completely eliminating mathematical hallucinations.
7. **Conversational Synthesis:** Hands the hard output rows over to a highly conversational `llama-3.1-8b-instant` block to structure a friendly, Indian-currency localized user response.

<br>

### Key Features

* **Smart Chat:** Type however you want! It understands typos, lowercase letters, and casual texting (e.g., *"spent on food"*).
* **Indian Currency:** Automatically shows all money with the proper Indian formatting and Rupee symbol (₹).
* **Privacy First:** Your data is processed live in your computer's memory and is never permanently stored or shared.
* **Dashboard Charts:** See your spending broken down by categories and tracked over time on a clean timeline.

<br>

### Project Structure

```text
bank-copilot/
├── data/
│   └── transactions.txt     # Sample structured text alerts
├── core/
│   ├── __init__.py
│   ├── database.py          # SQLite memory instances & runtime schema extraction
│   └── agent.py             # Groq LLM orchestration and query compilation
├── .env                     # App environment configuration variables
├── requirements.txt         # Project runtime dependencies
└── dashboard.py             # Core Streamlit application entrypoint & user interface

```

<br>

### Quick Start

#### Prerequisites

* Python 3.10+ installed on your system.
* A Groq Cloud API Key (Get one free from [console.groq.com](https://console.groq.com/)).

> [!WARNING]
> This project will not work without Groq Cloud API Key. Go and get it for free from above link

#### Installation & Execution

1. Clone this repository:
```bash
git clone [https://github.com/harshkad/BankTransactionCopilot.git](https://github.com/harshkad/BankTransactionCopilot.git)
cd BankTransactionCopilot

```


2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt

```


3. Configure your API credentials inside a new `.env` file in the root folder:
```env
GROQ_API_KEY=your_actual_groq_api_key_here

```


4. Run the Streamlit interface:
```bash
streamlit run dashboard.py

```


The application will deploy instantly at `http://localhost:8501`
