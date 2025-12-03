"""
Test MLflow SQLite info

Running command:
    python tests/test_mlflow_sqlite.py

Optional: 
- List all tables with schema
    python tests/test_mlflow_sqlite.py tables
- Show table schema
    python tests/test_mlflow_sqlite.py schema [table_name]
    ex. python tests/test_mlflow_sqlite.py schema spans

"""

import sqlite3
from pathlib import Path


def test_mlflow_sqlite():
    """Check for MLflow SQLite info"""
    
    db_path = Path("mlflow.db")

    # Check if the file exists
    if not db_path.exists():
        print("❌ mlflow.db does not exist!")
        print("   Please run crewai run to generate some traces.")
        return

    # Connect to the database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("=" * 60)
    print("📊 MLflow SQLite Database")
    print("=" * 60)
    
    # 1. Check all tables
    print("\n📋 Tables:")
    print("-" * 40)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    for table in tables:
        # Get all tables row count
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  • {table[0]}: {count} rows")

    # 2. Check experiments
    print("\n🧪 Experiments:")
    print("-" * 40)
    try:
        cursor.execute("""
            SELECT experiment_id, name, lifecycle_stage 
            FROM experiments 
            ORDER BY experiment_id
        """)
        experiments = cursor.fetchall()
        for exp in experiments:
            print(f"  • ID: {exp[0]}, Name: {exp[1]}, Stage: {exp[2]}")
    except sqlite3.OperationalError as e:
        print(f"  ⚠️ experiments table did not exist or structure changed: {e}")

    # 3. Check spans (detailed steps)
    print("\n🔍 Spans (Show recent 5):")
    print("-" * 40)
    try:
        cursor.execute("""
            SELECT trace_id, span_id, name, parent_span_id, type, status,
                   start_time_unix_nano, end_time_unix_nano
            FROM spans 
            ORDER BY start_time_unix_nano DESC 
            LIMIT 5
        """)
        spans = cursor.fetchall()
        
        if spans:
            for span in spans:
                trace_id, span_id, name, parent_id, span_type, status, start_ns, end_ns = span

                duration_ms = (end_ns - start_ns) / 1_000_000 if end_ns and start_ns else 0
                print(f"\n  📍 {name} ({span_type})")
                print(f"     trace:    {trace_id}")
                print(f"     span_id:  {span_id[:30]}...")
                print(f"     parent:   {parent_id[:30] if parent_id else 'ROOT'}...")
                print(f"     status:   {status}")
                print(f"     duration: {duration_ms:.0f}ms ({duration_ms/1000:.1f}s)")
        else:
            print("  (No spans)")
            
    except sqlite3.OperationalError as e:
        print(f"  ⚠️ spans table query failed: {e}")

    # 4. Check trace_info
    print("\n📝 Trace Info (Show recent 5):")
    print("-" * 40)
    try:
        cursor.execute("""
            SELECT request_id, experiment_id, timestamp_ms, execution_time_ms, status
            FROM trace_info
            ORDER BY timestamp_ms DESC
            LIMIT 5
        """)
        traces = cursor.fetchall()
        
        if traces:
            for trace in traces:
                request_id, exp_id, ts, exec_time, status = trace
                print(f"\n  🔗 Trace: {request_id}")
                print(f"     experiment_id: {exp_id}")
                print(f"     status: {status}")
                print(f"     execution_time: {exec_time}ms ({exec_time/1000:.1f}s)")
        else:
            print("  (No traces)")
            
    except sqlite3.OperationalError as e:
        print(f"  ⚠️ trace_info table query failed: {e}")

    # 5. Check database size
    print("\n💾 Database Info:")
    print("-" * 40)
    size_bytes = db_path.stat().st_size
    size_kb = size_bytes / 1024
    size_mb = size_kb / 1024
    print(f"  File: {db_path}")
    print(f"  Size: {size_bytes:,} bytes ({size_kb:.1f} KB / {size_mb:.2f} MB)")

    # Close connection
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("=" * 60)


def show_table_schema(table_name: str = "trace_info"):
    """
    Show schema for a specific table.
    
    Args:
        table_name: Name of the table to inspect (default: trace_info)
        
    Note:
        MLflow uses these trace-related tables:
        - trace_info: Main trace metadata
        - trace_tags: Trace tags/labels
        - trace_request_metadata: Request metadata
        - spans: Detailed execution spans
        
    """
    
    db_path = Path("mlflow.db")
    if not db_path.exists():
        print("❌ mlflow.db does not exist!")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
        (table_name,)
    )
    if not cursor.fetchone():
        print(f"❌ Table '{table_name}' does not exist!")
        print("\n� Available trace-related tables:")
        print("   - trace_info (main trace data)")
        print("   - trace_tags")
        print("   - trace_request_metadata")
        print("   - spans (detailed execution steps)")
        conn.close()
        return
    
    print(f"\n�📋 Schema for table '{table_name}':")
    print("-" * 40)
    
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        if columns:
            for col in columns:
                # col: (cid, name, type, notnull, dflt_value, pk)
                print(f"  {col[1]:30} {col[2]:15} {'NOT NULL' if col[3] else ''} {'PK' if col[5] else ''}")
        else:
            print("  (No columns found)")
            
    except Exception as e:
        print(f"  ⚠️ Error: {e}")
    
    conn.close()


def list_all_tables_with_schema():
    """List all tables with their schema/structure."""
    
    db_path = Path("mlflow.db")
    if not db_path.exists():
        print("❌ mlflow.db does not exist!")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        print(f"\n{'='*60}")
        print(f"Table: {table_name}")
        print("=" * 60)
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        for col in columns:
            print(f"  {col[1]:30} {col[2]:15}")
    
    conn.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "schema":
            if len(sys.argv) > 2:
                show_table_schema(sys.argv[2])
            else:
                list_all_tables_with_schema()
        elif sys.argv[1] == "tables":
            list_all_tables_with_schema()
    else:
        test_mlflow_sqlite()
