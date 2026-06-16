import re
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def clean_sql_response(sql_text):
    """Shared cleanup logic for extracting SQL from LLM responses."""
    sql_text = sql_text.strip()

    # Remove markdown code blocks if present
    sql_text = re.sub(r'^```(?:sql)?\s*\n', '', sql_text, flags=re.MULTILINE)
    sql_text = re.sub(r'\n```\s*$', '', sql_text, flags=re.MULTILINE)

    # Remove explanatory lines
    lines = sql_text.split('\n')
    sql_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.lower().startswith(('here', 'the', 'this', 'note:', 'explanation:')):
            sql_lines.append(line)
    sql_text = '\n'.join(sql_lines).strip()

    # Extract from first SQL keyword onward
    sql_upper = sql_text.upper()
    for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH']:
        idx = sql_upper.find(keyword)
        if idx >= 0:
            sql_text = sql_text[idx:].strip()
            break

    return sql_text


def generate_sql(schema, query):
    """Generate SQL query from natural language using Groq."""
    prompt = f"""Given the following database schema:
{schema}

Generate ONLY a valid SQL query (no explanation) for the following request:
{query}

Respond with ONLY the SQL query, nothing else."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
    )

    sql_text = response.choices[0].message.content
    return clean_sql_response(sql_text)


def generate_sql_with_retry(schema, query, bad_sql, error_message, max_retries=3):
    """Generate SQL query with retries, passing error context back to Groq."""
    for attempt in range(max_retries):
        prompt = f"""Given the following database schema:
{schema}

The user asked: {query}

You previously generated this SQL query:
{bad_sql}

It failed with this error:
{error_message}

Please fix the SQL query. Respond with ONLY the corrected SQL, nothing else."""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
        )

        sql_text = clean_sql_response(response.choices[0].message.content)

        if sql_text:
            return sql_text

    raise ValueError(f"Failed to fix SQL query after {max_retries} attempts. Last error: {error_message}")