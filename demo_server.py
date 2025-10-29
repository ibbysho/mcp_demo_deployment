from http import server
from fastmcp import FastMCP
import feedparser

mcp = FastMCP(name="FreeCodeCamp Feed Searcher")

@mcp.tool()
def fcc_news_search(query:str, max_results:int=3):
    """Search FreeCodeCamp news feed via RSS by title/description"""
    feed = feedparser.parse("https://www.freecodecamp.org/news/rss/")
    results = []
    query_lower = query.lower()
    for entry in feed.entries:
        title = entry.get("title", "")
        description = entry.get("description", "")
        if query_lower in title.lower() or query_lower in description.lower():
            results.append({"title":title, "url":entry.get("link", "")})
        if len(results) >= max_results:
            break #unlikely to occur

    return results or [{"message":"No results found"}]

@mcp.tool()
def fcc_youtube_search(query:str, max_results:int=3):
    """Search FreeCodeCamp Youtube channnel via RSS by title"""
    feed = feedparser.parse("https://www.youtube.com/feeds/videos.xml?channel_id=UC8butISFwT-Wl7EV0hUK0BQ")
    results = []
    query_lower = query.lower()
    for entry in feed.entries:
        title = entry.get("title", "")
        if query_lower in title.lower():
            results.append({"title":title, "url":entry.get("link", "")})
        if len(results) >= max_results:
            break #unlikely to occur
    return results or [{"message":"No videos found"}]


@mcp.tool()
def GEHC_youtube_search(query:str, max_results:int=3):
    """Search GEHC Youtube channel via RSS by title"""
    feed = feedparser.parse("https://www.youtube.com/feeds/videos.xml?channel_id=UC04R4GsgwjtoI28q7F3YrLw")
    results = []
    query_lower = query.lower()
    for entry in feed.entries:
        title = entry.get("title", "")
        if query_lower in title.lower():
            results.append({"title":title, "url":entry.get("link", "")})
        if len(results) >= max_results:
            break #unlikely to occur
    return results or [{"message":"No videos found"}]

@mcp.tool()
def capgemini_news_search(query:str, max_results:int=3):
    """Search Capgemini news feed via RSS by title/description"""
    feed = feedparser.parse("https://www.capgemini.com/news/rss/")
    results = []
    query_lower = query.lower()
    for entry in feed.entries:
        title = entry.get("title", "")
        description = entry.get("description", "")
        if query_lower in title.lower() or query_lower in description.lower():
            results.append({"title":title, "url":entry.get("link", "")})
        if len(results) >= max_results:
            break #unlikely to occur

    return results or [{"message":"No results found"}]
@mcp.tool()
async def greet_user_formal_tool(name:str) -> str:
    """
    A tool that returns a greeting message in a very formal tone
    Args:
        name (str): The name of the person to greet.
    Returns:
        str: A formal greeting message for the given name.
    """
    return f"Good day to you, {name}. I trust this message finds you well."

@mcp.tool()
async def greet_user_street_style_tool(name:str) -> str:
    """
    A tool that returns a greeting message in street style
    Args:
        name (str): The name of the person to greet.
    Returns:
        str: A street style greeting message for the given name.
    """
    return f"Yo {name}! Wassup? You good?"

@mcp.prompt
def greet_user_prompt(name: str) -> str:
    """Generates a message asking for a greeting"""
    return f"""
    Return a greeting message for a user called '{name}'. 
    if the user is called 'Laurent', use a formal style, else use a street style.
    """

@mcp.prompt
def email(tone: str, context: str) -> str:
    """Generate an email based on the given tone and context."""
    return f"""
   Generate a {tone} email for {context},
    """

@mcp.prompt
def analyze_excel(file_path: str) -> str:
    """Analyze the Excel file at the given file path."""
    return f"""
   Analyze the Excel file at {file_path} .
    """

@mcp.prompt
def code_review(language: str, focusAreas: str, codeBlock: str) -> str:
    """Analyze a code block for a given language and focus areas."""
    return f"""
Please review the following {language} code focusing on {focusAreas} for the following block of code:
```{language}
    {codeBlock}
    """
@mcp.resource("products://{category}/{product_id}")
def get_product_info(category: str, product_id: str) -> dict:
    """Retrieve detailed information about a specific product.
    
    Args:
        category: The product category (e.g., "electronics", "books")
        product_id: The unique identifier for the product
        
    Returns:
        A dictionary containing product details
    """
    # In a real application, you would query a database here
    sample_products = {
        "electronics": {
            "e123": {"name": "Smartphone XYZ", "price": 999.99, "in_stock": True},
            "e456": {"name": "Laptop ABC", "price": 1299.99, "in_stock": False}
        },
        "books": {
            "b789": {"name": "Python Programming", "price": 49.99, "in_stock": True},
            "b101": {"name": "AI Fundamentals", "price": 59.99, "in_stock": True}
        }
    }
    
    if category in sample_products and product_id in sample_products[category]:
        return {
            "product": sample_products[category][product_id],
            "category": category,
            "id": product_id
        }
    else:
        return {"error": f"Product {product_id} in category {category} not found"}

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers.

    args: a (float): The first number.
          b (float): The second number.

    returns: float: The product of the two numbers.
    """
    return a * b

@mcp.tool(
    name ="add",
    description = "Add two numbers.",
    tags = {"math", "arithmetic"}
)
def add_numbers(x: float, y: float) -> float:
    """Add two numbers.

    args: x (float): The first number.
          y (float): The second number.

    returns: float: The sum of the two numbers.
    """
    return x + y

@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract two numbers.

    args: a (float): The first number.
          b (float): The second number.

    returns: float: The difference of the two numbers.
    """
    return a - b

@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide two numbers.

    args: a (float): The first number.
          b (float): The second number.

    returns: float: The quotient of the two numbers.
    """
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b

if __name__ == "__main__":
    mcp.run(transport="http") #https://localhost:8003/mcp