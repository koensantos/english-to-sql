# Creates a temporary SQL Database for testing purposes
import sqlite3
import pandas as pd
from io import StringIO

def create_database_from_csv(csv_content):
    """Load CSV content into an in-memory SQLite database using pandas.
    
    Args:
        csv_content: String content of the CSV file
        
    Returns:
        sqlite3 connection object with data loaded
    """
    # Read CSV using pandas
    df = pd.read_csv(StringIO(csv_content))
    
    # Create in-memory database
    conn = sqlite3.connect(':memory:')
    
    # Write dataframe to SQL (table name 'data')
    df.to_sql('data', conn, index=False, if_exists='replace')
    
    return conn

def run_query(conn, query):
    """Execute a SQL query on the database.
    
    Args:
        conn: sqlite3 connection object
        query: SQL query string
        
    Returns:
        List of tuples containing query results, or error string if query fails
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        # Get column names from cursor description when available
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
        else:
            columns = []
        return rows, columns
    except Exception as e:
        return f"error: {str(e)}"

def get_column_names(conn, table_name='data'):
    """Get column names from a table.
    
    Args:
        conn: sqlite3 connection object
        table_name: Name of the table (default 'data')
        
    Returns:
        List of column names
    """
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    return [col[1] for col in columns]

def get_non_empty_columns(results, columns):
    """Filter columns and results to only include columns with at least one non-empty value.
    
    Args:
        results: List of tuples (query results)
        columns: List of column names
        
    Returns:
        Tuple of (filtered_columns, filtered_results)
    """
    if not results or not columns:
        return columns, results
    
    # Find which columns have at least one non-empty value
    non_empty_indices = []
    for col_idx in range(len(columns)):
        has_data = False
        for row in results:
            if col_idx < len(row) and row[col_idx] is not None and str(row[col_idx]).strip() != '':
                has_data = True
                break
        if has_data:
            non_empty_indices.append(col_idx)
    
    # Filter columns and results
    filtered_columns = [columns[i] for i in non_empty_indices]
    filtered_results = [tuple(row[i] for i in non_empty_indices) for row in results]
    
    return filtered_columns, filtered_results