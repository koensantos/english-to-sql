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

def get_schema_stats(conn):
    # This function returns statistics describing the schema.
    #I.E: number of columns, number of rows, if there are null values, data types, etc.
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    num_columns = 0
    num_rows = 0
    has_null_values = False
    data_types = set()

    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        num_columns += len(columns)
        for column in columns:
            data_types.add(column[2])
        
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        num_rows += cursor.fetchone()[0]
        
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE " + " OR ".join([f"{col[1]} IS NULL" for col in columns]) + ";")
        if cursor.fetchone()[0] > 0:
            has_null_values = True


    stats = {
        "num_columns": num_columns,
        "num_rows": num_rows,
        "has_null_values": has_null_values,
        "data_types": list(data_types)
    }
    return stats