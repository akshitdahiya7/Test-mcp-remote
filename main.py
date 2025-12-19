from fastmcp import FastMCP
import random
import json

mcp= FastMCP("Simple Calculator Server")


@mcp.tool
def add(a:int, b:int)-> int:
    """Add two numbers together
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        The sum of a and b
    """
    return a+b

@mcp.resource("info://server")
def server_info()-> str:
    """Get information about this server"""
    info={
        "name":"Simple Calculator Server",
        "version":"1.0.0",
        "description":"A basic MCP server with math tools",
        "tools":["add"],
        "author":"Akshit dahiya"
    }
    return json.dumps(info,indent=2)



if __name__ == "__main__":
    mcp.run(transport="http",host="0.0.0.0",port=8000)
