# from fastmcp import FastMCP
# import random
# import json

# mcp= FastMCP("Simple Calculator Server")


# @mcp.tool
# def add(a:int, b:int)-> int:
#     """Add two numbers together
    
#     Args:
#         a: First number
#         b: Second number
    
#     Returns:
#         The sum of a and b
#     """
#     return a+b

# @mcp.resource("info://server")
# def server_info()-> str:
#     """Get information about this server"""
#     info={
#         "name":"Simple Calculator Server",
#         "version":"1.0.0",
#         "description":"A basic MCP server with math tools",
#         "tools":["add"],
#         "author":"Akshit dahiya"
#     }
#     return json.dumps(info,indent=2)



# if __name__ == "__main__":
#     mcp.run(transport="http",host="0.0.0.0",port=8000)



# can use only if we have pro plan else we havev to use proxy server
import os
import json
import sqlite3
import tempfile
import aiosqlite
from fastmcp import FastMCP

# 1. Environment-aware Configuration
# Use a data directory if provided by the cloud host, otherwise fallback to temp
DATA_DIR = os.environ.get("DATA_DIR", tempfile.gettempdir())
DB_PATH = os.path.join(DATA_DIR, "expenses.db")
# Locate categories relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATEGORIES_PATH = os.path.join(BASE_DIR, "categories.json")

print(f"Server starting. Database path: {DB_PATH}")

mcp = FastMCP("ExpenseTracker")

# 2. Synchronous Database Initialization
def init_db():
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        with sqlite3.connect(DB_PATH) as c:
            # WAL mode is great for performance but can fail on certain Network File Systems
            # We use 'DELETE' (default) for maximum compatibility in cloud environments
            c.execute("PRAGMA journal_mode=DELETE")
            c.execute("""
                CREATE TABLE IF NOT EXISTS expenses(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT DEFAULT '',
                    note TEXT DEFAULT ''
                )
            """)
            print("Database initialized successfully")
    except Exception as e:
        print(f"Critical: Database initialization error: {e}")
        raise

init_db()

# 3. MCP Tools (Async)
@mcp.tool()
async def add_expense(date: str, amount: float, category: str, subcategory: str = "", note: str = ""):
    '''Add a new expense entry (date format: YYYY-MM-DD).'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
                (date, amount, category, subcategory, note)
            )
            expense_id = cur.lastrowid
            await c.commit()
            return {"status": "success", "id": expense_id, "message": "Expense added successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def list_expenses(start_date: str, end_date: str):
    '''List expense entries within an inclusive date range (YYYY-MM-DD).'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            c.row_factory = aiosqlite.Row
            async with await c.execute(
                "SELECT * FROM expenses WHERE date BETWEEN ? AND ? ORDER BY date DESC",
                (start_date, end_date)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def summarize_expenses(start_date: str, end_date: str, category: str = None):
    '''Summarize total spending by category for a date range.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            c.row_factory = aiosqlite.Row
            query = """
                SELECT category, SUM(amount) AS total, COUNT(*) as count 
                FROM expenses WHERE date BETWEEN ? AND ?
            """
            params = [start_date, end_date]
            if category:
                query += " AND category = ?"
                params.append(category)
            
            query += " GROUP BY category ORDER BY total DESC"
            
            async with await c.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 4. MCP Resources
@mcp.resource("expense:///categories")
def get_categories() -> str:
    '''Get the list of allowed expense categories.'''
    default_categories = {
        "categories": ["Food", "Transport", "Housing", "Utilities", "Health", "Entertainment", "Other"]
    }
    try:
        if os.path.exists(CATEGORIES_PATH):
            with open(CATEGORIES_PATH, "r") as f:
                return f.read()
        return json.dumps(default_categories, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

# 5. Cloud-Ready Entry Point
if __name__ == "__main__":
    # Cloud providers use the PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    # 'http' transport for cloud web services, 'stdio' for local/CLI use
    mcp.run(transport="http", host="0.0.0.0", port=port)


    
# for running in claude to bypass remote server

# from fastmcp import FastMCP

# # Create a proxy to your remote FastMCP Cloud server
# # FastMCP Cloud uses Streamable HTTP (default), so just use the /mcp URL
# mcp = FastMCP.as_proxy(
#     "https://political-purple-bedbug.fastmcp.app/mcp",  # Standard FastMCP Cloud URL
#     name="Akshit Server Proxy"
# )

# if __name__ == "__main__":
#     # This runs via STDIO, which Claude Desktop can connect to
#     mcp.run()