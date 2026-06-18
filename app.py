import flask
from werkzeug.utils import secure_filename
import os
from database import create_database_from_csv, run_query, get_column_names, get_non_empty_columns
from schema import extract_schema, get_schema_stats
from llm import generate_sql, generate_sql_with_retry
from flask import session

import csv
import secrets
from io import StringIO

app = flask.Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Needed for session management
ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_query_history():
    return flask.session.get('query_history', [])


def add_query_history(natural_query, sql_query):
    history = flask.session.get('query_history', [])
    history.append({'natural_query': natural_query, 'sql_query': sql_query})
    flask.session['query_history'] = history


def is_numeric(value):
    """Check if a value is numeric."""
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def detect_chart_data(results, columns):
    """Detect if results are suitable for charting and generate chart data."""
    if not results or len(results) == 0:
        return None, False
    
    num_cols = len(columns)
    
    # Case 1: Single row with single numeric value
    if len(results) == 1 and num_cols == 1 and is_numeric(results[0][0]):
        return {
            'type': 'gauge',  # We'll use a simple bar for now
            'labels': [columns[0]],
            'data': [float(results[0][0])],
            'label': columns[0],
            'title': columns[0]
        }, True
    
    # Case 2: Two columns - one categorical, one numeric (ideal for bar/line chart)
    if num_cols == 2 and len(results) > 1:
        # Check if second column is numeric
        if all(is_numeric(row[1]) for row in results):
            labels = [str(row[0]) for row in results]
            data = [float(row[1]) for row in results]
            
            chart_type = 'bar' if len(results) <= 10 else 'line'
            
            return {
                'type': chart_type,
                'labels': labels,
                'data': data,
                'label': columns[1],
                'title': f'{columns[0]} vs {columns[1]}'
            }, True
    
    # Case 3: Multiple rows with single numeric column
    if num_cols == 1 and all(is_numeric(row[0]) for row in results):
        if len(results) <= 20:
            labels = [f'Row {i+1}' for i in range(len(results))]
            data = [float(row[0]) for row in results]
            
            return {
                'type': 'line',
                'labels': labels,
                'data': data,
                'label': columns[0],
                'title': columns[0]
            }, True
    
    return None, False


@app.route("/")
def index():
    has_data = 'csv_content' in flask.session
    schema = None
    if has_data:
        conn = create_database_from_csv(flask.session['csv_content'])
        schema = extract_schema(conn)
        stats = get_schema_stats(conn)

    return flask.render_template(
        "main.html",
        schema = schema,
        stats = stats if has_data else None,
        has_data=has_data,
        query_history=get_query_history(),
        show_editor=False,
        natural_query=None,
        sql_query=None,
        results=None,
        columns=None,
        is_chartable=False,
        chart_data=None
    )

@app.route("/upload", methods=["POST"])
def upload_csv():
    """Handle CSV file upload and create in-memory database."""
    
    # Check if file is in request
    if 'file' not in flask.request.files:
        flask.flash('No file selected', category='error')
        return flask.redirect(flask.url_for('index'))
    
    file = flask.request.files['file']
    
    if file.filename == '':
        flask.flash('No file selected', category='error')
        return flask.redirect(flask.url_for('index'))
    
    if not allowed_file(file.filename):
        flask.flash('Only CSV files are allowed', category='error')
        return flask.redirect(flask.url_for('index'))
    
    try:
        # Read CSV content and store in session
        csv_content = file.read().decode('utf-8')
        flask.session['csv_content'] = csv_content
        
        flask.flash(f'CSV file "{secure_filename(file.filename)}" loaded successfully!', category='success')
    except Exception as e:
        flask.flash(f'Error loading CSV: {str(e)}', category='error')
    
    return flask.redirect(flask.url_for('index'))

@app.route("/query", methods=["POST"])
def submit_query():
    """Convert natural language query to SQL and show it in editor."""
    
    if 'csv_content' not in flask.session:
        flask.flash('Please upload a CSV file first', category='error')
        return flask.redirect(flask.url_for('index'))
    
    query_text = flask.request.form.get('query', '').strip()
    
    if not query_text:
        flask.flash('Please enter a query', category='error')
        return flask.redirect(flask.url_for('index'))
    
    try:
        # Create database connection from session CSV
        db_connection = create_database_from_csv(flask.session['csv_content'])
        
        # Extract schema
        db_schema = extract_schema(db_connection)
        
        # Generate SQL from natural language
        sql_query = generate_sql(db_schema, query_text)
        
        # If the query is empty or does not contain a valid SQL statement, raise an error
        if not sql_query or not any(keyword in sql_query.upper() for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH']):
            raise ValueError("Generated SQL query is invalid or empty.")
        
        # Store SQL and natural query for editing
        flask.session['generated_sql'] = sql_query
        flask.session['current_natural_query'] = query_text
        
        flask.flash(f'SQL query generated! Edit it below if needed, then click "Execute SQL".', category='info')
        return flask.render_template(
            "main.html",
            schema=db_schema,
            has_data=True,
            sql_query=sql_query,
            natural_query=query_text,
            query_history=get_query_history(),
            show_editor=True,
            results=None,
            columns=None,
            is_chartable=False,
            chart_data=None
        )
    except Exception as e:
        # Display error message to user
        flask.flash(f'Error generating query: {str(e)}', category='error')
        return flask.redirect(flask.url_for('index'))

@app.route("/execute_sql", methods=["POST"])
def execute_sql():
    """Execute the SQL query from the editor."""
    
    if 'csv_content' not in flask.session:
        flask.flash('Please upload a CSV file first', category='error')
        return flask.redirect(flask.url_for('index'))
    
    sql_query = flask.request.form.get('sql', '').strip()
    natural_query = flask.session.get('current_natural_query', 'Manual SQL')
    
    if not sql_query:
        flask.flash('Please enter a SQL query', category='error')
        return flask.redirect(flask.url_for('index'))
    
    try:
        # Create database connection
        db_connection = create_database_from_csv(flask.session['csv_content'])
        db_schema = extract_schema(db_connection)
        
        # Run the query
        query_result = run_query(db_connection, sql_query)
        
        # If error, offer retry
        if isinstance(query_result, str) and query_result.lower().startswith('error'):
            flask.flash(f'Query error: {query_result}. You can edit and retry.', category='error')
            return flask.render_template(
                "main.html",
                schema=db_schema,
                has_data=True,
                sql_query=sql_query,
                natural_query=natural_query,
                query_history=get_query_history(),
                show_editor=True,
                results=None,
                columns=None,
                is_chartable=False,
                chart_data=None
            )
        
        # Unpack results
        results, columns_from_query = query_result
        if not columns_from_query:
            columns = get_column_names(db_connection)
        else:
            columns = columns_from_query
        
        # Filter non-empty columns
        columns, results = get_non_empty_columns(results, columns)
        
        # Detect chartable data
        chart_data, is_chartable = detect_chart_data(results, columns)
        
        # Add to history
        add_query_history(natural_query, sql_query)
        flask.session['last_sql_query'] = sql_query
        
        flask.flash(f'Query executed successfully!', category='success')
        return flask.render_template(
            "main.html",
            schema=db_schema,
            has_data=True,
            sql_query=sql_query,
            results=results,
            columns=columns,
            natural_query=natural_query,
            query_history=get_query_history(),
            show_editor=False,
            is_chartable=is_chartable,
            chart_data=chart_data
        )
    except Exception as e:
        flask.flash(f'Error executing query: {str(e)}', category='error')
        return flask.redirect(flask.url_for('index'))

@app.route("/download_csv", methods=["GET"])
def download_csv():
#Allows the user to download the results of their query as a CSV file
#We get results and columns from the session, create a CSV string, and send it as a downloadable file
    sql_query_string = flask.session.get('last_sql_query')
    if not sql_query_string:
        flask.flash('No query results available to download', category='error')
        return flask.redirect(flask.url_for('index'))
    
    new_csv_content = ""
    try:
        db_conn = create_database_from_csv(flask.session['csv_content'])
        query_result = run_query(db_conn, sql_query_string)

        if isinstance(query_result, str) and query_result.lower().startswith('error'):
            raise ValueError(f"Cannot download results due to query error: {query_result}")

        results, columns = query_result
        if not columns:
            columns = get_column_names(db_conn)

        # Filter to only include non-empty columns
        columns, results = get_non_empty_columns(results, columns)
        # Create CSV string
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)  # Write header
        writer.writerows(results)  # Write data rows
        new_csv_content = output.getvalue()
        output.close()

        return flask.Response(
            new_csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment;filename=query_results.csv'}
        )
    except Exception as e:
        flask.flash(f'Error generating CSV: {str(e)}', category='error')
        return flask.redirect(flask.url_for('index'))

@app.route("/history/run/<int:index>", methods=["GET"])
def run_history(index):
    if 'csv_content' not in flask.session:
        flask.flash('Please upload a CSV file first', category='error')
        return flask.redirect(flask.url_for('index'))

    history = get_query_history()
    if index < 0 or index >= len(history):
        flask.flash('Requested history item does not exist', category='error')
        return flask.redirect(flask.url_for('index'))

    entry = history[index]
    query_text = entry['natural_query']
    sql_query = entry['sql_query']

    try:
        db_connection = create_database_from_csv(flask.session['csv_content'])
        db_schema = extract_schema(db_connection)

        query_result = run_query(db_connection, sql_query)
        if isinstance(query_result, str) and query_result.lower().startswith('error'):
            raise ValueError(f"Query failed: {query_result}")

        results, columns_from_query = query_result
        if not columns_from_query:
            columns = get_column_names(db_connection)
        else:
            columns = columns_from_query

        columns, results = get_non_empty_columns(results, columns)

        # Detect chartable data
        chart_data, is_chartable = detect_chart_data(results, columns)

        flask.flash('Query from history executed successfully!', category='success')
        return flask.render_template(
            "main.html",
            schema=db_schema,
            has_data=True,
            sql_query=sql_query,
            results=results,
            columns=columns,
            natural_query=query_text,
            query_history=history,
            show_editor=False,
            is_chartable=is_chartable,
            chart_data=chart_data
        )
    except Exception as e:
        flask.flash(f'Error executing historical query: {str(e)}', category='error')
        return flask.redirect(flask.url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)

