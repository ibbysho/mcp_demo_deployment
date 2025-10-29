from fastmcp import FastMCP
from typing import Any, Optional
import sqlite3
import os
from datetime import datetime, timedelta
from fastmcp import FastMCP, Context
from fastmcp.exceptions import ResourceError

mcp = FastMCP("technova-customer-support")
APP_LOG_PATH = os.path.join(os.path.dirname(__file__), "logs", "app.log")
LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "technova.db")


def get_db_connection():
    """
    Create a connection to the SQLite database.
    Returns a connection with row factory set to return dictionaries.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    return conn


def get_customer(customer_id: str) -> Optional[dict]:
    """
    Retrieve customer information from the database by ID.
    
    Args:
        customer_id: Unique identifier for the customer (e.g., ACM001)
        
    Returns:
        Dictionary containing customer data or None if not found
    """
    conn = get_db_connection()
    try:
        # SQL query joins customers and subscriptions tables
        query = """
        SELECT c.*, s.plan, s.seats, s.renewal_date, s.status as subscription_status, s.monthly_value
        FROM customers c
        LEFT JOIN subscriptions s ON c.id = s.customer_id
        WHERE c.id = ?
        """
        result = conn.execute(query, (customer_id,)).fetchone()
        if result:
            # Convert sqlite3.Row to a regular dictionary
            return dict(result)
        return None
    finally:
        # Ensure connection is closed even if an exception occurs
        conn.close()


def get_support_tickets(customer_id: str, timeframe: str) -> list:
    """
    Retrieve support tickets for a customer within the specified timeframe.
    
    Args:
        customer_id: Unique identifier for the customer
        timeframe: Period to look back (7days, 30days, 90days)
        
    Returns:
        List of ticket dictionaries ordered by creation date
    """
    conn = get_db_connection()
    try:
        # Calculate the date range based on timeframe parameter
        today = datetime.now()
        
        if timeframe == "7days":
            start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        elif timeframe == "90days":
            start_date = (today - timedelta(days=90)).strftime("%Y-%m-%d")
        else:  # Default to 180 days
            start_date = (today - timedelta(days=180)).strftime("%Y-%m-%d")
        
        # SQL query joins support_tickets and contacts tables
        query = """
        SELECT t.*, c.name as contact_name, c.title as contact_title
        FROM support_tickets t
        LEFT JOIN contacts c ON t.contact_id = c.id
        WHERE t.customer_id = ? AND t.created_date >= ?
        ORDER BY t.created_date DESC
        """
        results = conn.execute(query, (customer_id, start_date)).fetchall()
        
        # Convert sqlite3.Row objects to regular dictionaries
        return [dict(row) for row in results]
    finally:
        conn.close()


def format_support_summary(customer: dict, tickets: list, timeframe: str) -> str:
    """
    Format customer and ticket data into a readable summary.
    
    Args:
        customer: Dictionary containing customer data
        tickets: List of ticket dictionaries
        timeframe: Period of time covered (e.g., "30days")
        
    Returns:
        Formatted text summary with customer info and ticket details
    """
    if not customer:
        return "Customer not found."
    
    if not tickets:
        return f"No support tickets found for {customer['name']} in the last {timeframe}."
    
    # Analyze tickets by status and priority
    open_tickets = [t for t in tickets if t["status"] == "Open"]
    resolved_tickets = [t for t in tickets if t["status"] == "Resolved"]
    high_priority = [t for t in tickets if t["priority"] in ["High", "Critical"]]
    
    # Start building the summary with customer name and timeframe
    summary = f"Support Summary for {customer['name']} ({timeframe}):\n\n"
    
    # Customer information section
    summary += "CUSTOMER INFORMATION:\n"
    summary += f"Industry: {customer['industry']}\n"
    summary += f"Size: {customer['size']}\n"
    summary += f"Subscription: {customer['plan']} ({customer['seats']} seats)\n"
    summary += f"Renewal Date: {customer['renewal_date']}\n"
    summary += f"Subscription Status: {customer['subscription_status']}\n\n"
    
    # Ticket statistics section
    summary += "SUPPORT SUMMARY:\n"
    summary += f"- Total tickets: {len(tickets)}\n"
    summary += f"- Open tickets: {len(open_tickets)}\n"
    summary += f"- Resolved tickets: {len(resolved_tickets)}\n"
    summary += f"- High/Critical priority: {len(high_priority)}\n\n"
    
    # Individual ticket details section
    summary += "RECENT TICKETS:\n"
    for ticket in tickets:
        resolved_text = f"Resolved: {ticket['resolved_date']}" if ticket['resolved_date'] else "Still Open"
        
        summary += f"- [{ticket['priority']}] {ticket['subject']} ({ticket['status']})\n"
        summary += f"  Created: {ticket['created_date']} | {resolved_text}\n"
        summary += f"  Reported by: {ticket['contact_name']}, {ticket['contact_title']}\n"
        summary += f"  Description: {ticket['description']}\n\n"
    
    return summary    


def setup_logs_directory():
    """Create logs directory and sample files if they don't exist."""
    try:
        # Create logs directory
        os.makedirs(LOGS_DIR, exist_ok=True)
        
     
        print(f"Logs directory setup complete: {LOGS_DIR}")
        
    except Exception as e:
        print(f"Error setting up logs directory: {e}")


# ============== MCP TOOLS ==============

@mcp.tool()
def generate_support_summary(customer_id: str, timeframe: str = "30days") -> str:
    """
    Generate a concise summary of recent support tickets for a customer.
    This function is exposed as an MCP tool for client applications.
    
    Args:
        customer_id: The unique ID of the customer (e.g., ACM001, GLX002, UMB003)
        timeframe: Lookback period for support tickets (7days, 30days, 90days)
        
    Returns:
        Formatted summary text with customer and ticket information
    """
    try:
        # Step 1: Retrieve customer information from database
        customer = get_customer(customer_id)
        if not customer:
            return f"Error: Customer with ID {customer_id} not found."
        
        # Step 2: Retrieve support tickets for the specified timeframe
        tickets = get_support_tickets(customer_id, timeframe)
        
        # Step 3: Format the data into a readable summary
        return format_support_summary(customer, tickets, timeframe)
    except Exception as e:
        # Handle any unexpected errors
        return f"Error generating support summary: {str(e)}"

# ============== MCP RESOURCES ==============
@mcp.resource(uri="file:///logs/app.log", name="app_logs", description="TechNova Application Logs")
async def get_app_logs() -> str:
    """Server application logs for the TechNova customer support system."""
    try:

        with open(APP_LOG_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            return "# TechNova Application Logs\n# Log file is empty\n"

        # Add metadata header with file information
        file_stats = os.stat(APP_LOG_PATH)
        header = f"""# TechNova Application Logs
# File: {APP_LOG_PATH}
# Size: {file_stats.st_size:,} bytes
# Last Modified: {datetime.fromtimestamp(file_stats.st_mtime).isoformat()}
# Retrieved: {datetime.now().isoformat()}

"""

        return header + content

    except Exception as e:
        raise ResourceError(f"Error reading application logs: {str(e)}")

@mcp.resource(uri="file:///logs/customer_{customer_id}.log")
async def get_customer_logs(customer_id: str) -> str:
    """Activity logs specific to a customer with validation and metadata."""
    try:

        # Validate customer_id format for security
        if not customer_id or len(customer_id) > 20:
            raise ResourceError(f"Invalid customer ID length: {customer_id}")

        if not customer_id.replace('_', '').replace('-', '').isalnum():
            raise ResourceError(f"Invalid customer ID format: {customer_id}")

        customer_log_path = os.path.join(LOGS_DIR, f"customer_{customer_id}.log")

        with open(customer_log_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            return f"# Customer {customer_id} Activity Log\n# Log file exists but is empty\n"

        file_stats = os.stat(customer_log_path)
        header = f"""# Customer {customer_id} Activity Log
# File: {customer_log_path}
# Size: {file_stats.st_size:,} bytes
# Last Modified: {datetime.fromtimestamp(file_stats.st_mtime).isoformat()}
# Retrieved: {datetime.now().isoformat()}

"""

        return header + content

    except Exception as e:
        raise ResourceError(f"Error reading customer logs for {customer_id}: {str(e)}")

# ============== MCP PROMPTS ==============

@mcp.prompt(
    name="customer_issue_summary",
    description="Create a comprehensive customer issue summary from logs and support data",
    tags={"customer", "summary", "support"}
)
def customer_issue_summary(customer_id: str, timeframe: str = "24hours") -> str:
    """Generate a prompt with customer logs injected server-side."""

    # Server-side resource injection - fetch customer logs
    customer_log_path = os.path.join(LOGS_DIR, f"customer_{customer_id}.log")
    app_log_path = APP_LOG_PATH

    customer_logs = ""
    app_logs = ""

    try:
        # Read customer-specific logs
        if os.path.exists(customer_log_path):
            with open(customer_log_path, "r", encoding="utf-8") as f:
                customer_logs = f.read()
        else:
            customer_logs = f"No customer logs found for {customer_id}"

        # Read application logs
        if os.path.exists(app_log_path):
            with open(app_log_path, "r", encoding="utf-8") as f:
                app_logs = f.read()
        else:
            app_logs = "No application logs found"

    except Exception as e:
        customer_logs = f"Error reading customer logs: {str(e)}"
        app_logs = f"Error reading application logs: {str(e)}"

    # Inject logs directly into the prompt
    return f"""Based on logs for customer {customer_id}, create a comprehensive issue briefing for the support team.

=== APPLICATION LOGS ===
{app_logs}

=== CUSTOMER {customer_id} LOGS ===
{customer_logs}

=== END OF LOGS ===

Analyze the last {timeframe} and include:


**Technical Issues:**
- Authentication and access problems
- API and integration failures
- System errors affecting this customer
- Performance or availability issues

**Business Impact:**
- How long has the customer been affected?
- What business processes are disrupted?
- Revenue or operational impact assessment
- Customer satisfaction risk level

**Resolution Strategy:**
- Immediate actions needed
- Escalation requirements
- Expected timeline for resolution
- Communication plan for customer

Format as a structured briefing document that a senior support agent can quickly understand and act upon."""


if __name__ == "__main__":
    mcp.run(transport="http")
