# English to SQL

A natural language to SQL query tool built with Flask and the Groq API. Upload any CSV file and query it in plain English — no SQL knowledge required.

**🔗 Live Demo:** [https://english-to-sql-cwbx.onrender.com]
*(Free tier — first load after inactivity may take ~30 seconds to wake up)*

## Screenshots 
<img width="1155" height="772" alt="image" src="https://github.com/user-attachments/assets/80367ab0-1609-4fbe-8e86-04dde58e97ba" />
<img width="1138" height="215" alt="image" src="https://github.com/user-attachments/assets/5fde160d-58fa-4896-8fec-21493bdfc62e" />
<img width="1133" height="617" alt="image" src="https://github.com/user-attachments/assets/f0c393f9-a5e2-4e2b-b204-95556da47904" />
<img width="1192" height="276" alt="image" src="https://github.com/user-attachments/assets/e0db8140-2e6e-4c3d-9c42-e3ab4f66693b" />


## Demo

1. Upload a CSV file
2. Type a question like *"what is the average damage done per hero?"*
3. The app generates and runs the SQL query, returning results instantly
4. Made a mistake or want to revisit something? Pull it up from query history or download results as a CSV

## Features

- **CSV upload** — load any CSV into a temporary in-memory SQLite database
- **Natural language queries** — powered by Llama 3.3 70B via the Groq API
- **Auto schema detection** — automatically reads table structure and column names
- **Self-correcting query generation** — if a generated query fails, the error is sent back to the LLM, which retries with that context until it succeeds (up to 3 attempts)
- **Query history** — view and re-run past queries from the current session
- **CSV export** — download query results without storing large data in the session
- **Session-based storage** — database lives only for the duration of your session, no data is persisted

## Tech Stack

- **Backend:** Python, Flask
- **Database:** SQLite (in-memory), Pandas
- **LLM:** Llama 3.3 70B via the Groq API
- **Frontend:** HTML/Jinja2
- **Deployment:** Render

## Project Structure

```
english-to-sql/
├── app.py            # Flask routes and session handling
├── database.py       # CSV ingestion and SQLite query execution
├── llm.py            # Groq integration, SQL generation, and self-correction
├── schema.py         # Auto schema extraction from SQLite
├── requirements.txt
├── runtime.txt        # Pins Python version for deployment
├── .env               # Environment variables (not committed)
├── .gitignore
└── templates/
    └── main.html
```

## Getting Started

### Prerequisites

- Python 3.11+
- A free [Groq API key](https://console.groq.com)

### Installation

1. Clone the repository
```bash
git clone https://github.com/koensantos/english-to-sql.git
cd english-to-sql
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Add your API key to a `.env` file
```
GROQ_API_KEY=your-key-here
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
5. Re-run or revisit past queries from the query history panel
6. Download results as a CSV if needed

### Example queries

- *"Show me the top 5 rows"*
- *"What is the average value of each column?"*
- *"How many rows have X greater than 100?"*

## How It Works

1. The CSV is read into a Pandas DataFrame and loaded into an in-memory SQLite database
2. The schema (table name, column names, types, sample row) is extracted and passed to the LLM as context
3. Llama 3.3 generates a SQL query from the natural language input
4. The query is executed against the SQLite database
5. If execution fails, the error message is sent back to the LLM along with the original query and question, prompting it to generate a corrected version — this repeats up to 3 times
6. Successful queries and their SQL are saved to session-based history for review or re-execution
7. Results are returned to the frontend and can be exported as a CSV

## Notes

- Only `.csv` files are supported
- The in-memory database is tied to the Flask session and is not persisted between sessions
- A valid `GROQ_API_KEY` must be set as an environment variable for the app to function
