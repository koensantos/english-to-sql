def extract_schema(conn):
    """Extract database schema from SQLite connection.
    
    Args:
        conn: sqlite3 connection object
        
    Returns:
        String describing the database schema
    """
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    schema = ""
    for table in tables:
        table_name = table[0]
        schema += f"Table: {table_name}\n"
        
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        for column in columns:
            column_name = column[1]
            column_type = column[2]
            schema += f"  - {column_name} ({column_type})\n"
        
        # Show sample data
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
        sample = cursor.fetchone()
        if sample:
            schema += f"  (Sample: {sample})\n"
    
    return schema.strip()