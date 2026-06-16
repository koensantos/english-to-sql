# English to SQL

A natural language to SQL query tool built with Flask and Ollama. Upload any CSV file and query it in plain English — no SQL knowledge required.

## Demo

1. Upload a CSV file
2. Type a question like *"what is the average damage done per hero?"*
3. The app generates and runs the SQL query, returning the results instantly

## Features

- **CSV upload** — load any CSV into a temporary in-memory SQLite database
- **Natural language queries** — powered by Llama 3.2 running locally via Ollama
- **Auto schema detection** — automatically reads table structure and column names
- **Query execution** — generates SQL and runs it, displaying results in the browser
- **Session-based storage** — database lives only for the duration of your session, no data is persisted

## Tech Stack

- **Backend:** Python, Flask
- **Database:** SQLite (in-memory), Pandas
- **LLM:** Llama 3.2 via Ollama (runs locally, no API key needed)
- **Frontend:** HTML/Jinja2

## Project Structure

```
english-to-sql/
├── app.py          # Flask routes and session handling
├── database.py     # CSV ingestion and SQLite query execution
├── llm.py          # Ollama integration and SQL generation
├── schema.py       # Auto schema extraction from SQLite
├── .env            # Environment variables (not committed)
├── .gitignore
└── templates/
    └── main.html
```

## Getting Started

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed and running

### Installation

1. Clone the repository
```bash
git clone https://github.com/your-username/english-to-sql.git
cd english-to-sql
```

2. Install dependencies
```bash
pip install flask pandas ollama python-dotenv
```

3. Pull the Llama model
```bash
ollama pull llama3.2
```

4. Run the app
```bash
python app.py
```

5. Open your browser at `http://localhost:5000`

## Usage

1. Upload a `.csv` file using the upload form
2. The app detects the schema automatically
3. Type a natural language question about your data
4. View the generated SQL query and results

### Example queries

- *"Show me the top 5 rows"*
- *"What is the average value of each column?"*
- *"How many rows have X greater than 100?"*

## How It Works

1. The CSV is read into a Pandas DataFrame and loaded into an in-memory SQLite database
2. The schema (table name, column names, types, sample row) is extracted and passed to the LLM as context
3. Llama 3.2 generates a valid SQL query from the natural language input
4. The query is executed on the SQLite database and results are returned to the frontend

## Notes

- Only `.csv` files are supported
- The in-memory database is tied to the Flask session and is not persisted between sessions
- Ollama must be running locally before starting the Flask app (`ollama serve`)