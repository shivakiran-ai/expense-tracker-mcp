"""
FastMCP Server for Expense Tracker
Production-ready MCP tools for expense management
"""

import sys
from pathlib import Path

# Add project root to Python path (CRITICAL FIX!)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastmcp import FastMCP
from datetime import datetime
import logging
from typing import Optional
from bson import ObjectId

# Import Day 1 modules
from src.expense_server.database.connection import get_database
from src.expense_server.database.models import (
    ExpenseCreate,
    VALID_CATEGORIES,
    VALID_PAYMENT_METHODS,
    SUPPORTED_CURRENCIES,
    CURRENCY_SYMBOLS,
    CATEGORY_SUBCATEGORIES,
    get_subcategories_for_category,
)
from src.expense_server.utils.currency import (
    convert_to_usd,
    format_amount_with_symbol,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastMCP server
mcp = FastMCP("Expense Tracker")

# Hardcoded test user for Day 2-5
TEST_USER_ID = "test_user_123"

logger.info("Expense Tracker MCP Server initialized")
logger.info(f"Test User ID: {TEST_USER_ID}")


# ============================================
# HELPER FUNCTIONS
# ============================================

def normalize_subcategory(category: str, subcategory: Optional[str]) -> str:
    """
    Normalize subcategory to valid value or default to "other".
    Simple and clean - no complex logic.
    
    Args:
        category: Main category
        subcategory: Subcategory provided by Claude
    
    Returns:
        Valid subcategory or "other"
    """
    # If no subcategory provided, use "other"
    if not subcategory:
        logger.info(f"No subcategory provided, using 'other'")
        return "other"
    
    # Get valid subcategories for this category
    valid_subcats = CATEGORY_SUBCATEGORIES.get(category, [])
    
    if not valid_subcats:
        logger.warning(f"No valid subcategories for category '{category}', using 'other'")
        return "other"
    
    # Normalize input
    subcat_lower = subcategory.lower().strip()
    
    # If exact match, use it
    if subcat_lower in valid_subcats:
        logger.info(f"Valid subcategory: '{subcat_lower}'")
        return subcat_lower
    
    # Check if any valid subcategory is contained in the provided one
    # Example: "doctor visit" contains "doctor"
    for valid in valid_subcats:
        if valid in subcat_lower:
            logger.info(f"Matched '{subcat_lower}' to '{valid}'")
            return valid
    
    # No match found, use "other"
    logger.info(f"No match for '{subcategory}', using 'other'")
    return "other"


# ============================================
# TOOL 1: ADD EXPENSE
# ============================================

@mcp.tool()
async def add_expense(
    amount: float,
    currency: str,
    category: str,
    description: str,
    payment_method: str = "cash",
    payment_subcategory: Optional[str] = None,
    subcategory: Optional[str] = None,
    date: Optional[str] = None
) -> str:
    f"""
    Add a new expense to the tracker.
    
    Automatically converts amounts to USD for storage while preserving
    the original amount and currency for display.
    
    CATEGORY INFERENCE - Use keywords from description:
    
    "food" keywords: dinner, lunch, breakfast, meal, restaurant, cafe, groceries, supermarket, food, pizza, burger
    "transport" keywords: gas, fuel, petrol, uber, taxi, cab, bus, train, parking, ride
    "utilities" keywords: electricity, internet, wifi, phone, water, bill
    "healthcare" keywords: doctor, hospital, medicine, pharmacy, dentist, clinic, checkup
    "entertainment" keywords: movie, cinema, netflix, spotify, concert, game
    "education" keywords: course, book, class, training, tuition, school
    "shopping" keywords: clothes, electronics, laptop, phone, shirt, gift
    "housing" keywords: rent, mortgage, repair, furniture
    "personal" keywords: haircut, salon, gym, spa
    
    VALID CATEGORIES:
    {', '.join(VALID_CATEGORIES)}
    
    VALID SUBCATEGORIES BY CATEGORY:
    Food: {', '.join(CATEGORY_SUBCATEGORIES['food'])}
    Transport: {', '.join(CATEGORY_SUBCATEGORIES['transport'])}
    Education: {', '.join(CATEGORY_SUBCATEGORIES['education'])}
    Entertainment: {', '.join(CATEGORY_SUBCATEGORIES['entertainment'])}
    Shopping: {', '.join(CATEGORY_SUBCATEGORIES['shopping'])}
    Utilities: {', '.join(CATEGORY_SUBCATEGORIES['utilities'])}
    Healthcare: {', '.join(CATEGORY_SUBCATEGORIES['healthcare'])}
    Housing: {', '.join(CATEGORY_SUBCATEGORIES['housing'])}
    Personal: {', '.join(CATEGORY_SUBCATEGORIES['personal'])}
    
    VALID PAYMENT METHODS:
    {', '.join(VALID_PAYMENT_METHODS)}
    
    SUPPORTED CURRENCIES:
    {', '.join(SUPPORTED_CURRENCIES)}
    
    EXAMPLES:
    User: "bought groceries for 500 rupees" → category="food", subcategory="groceries"
    User: "doctor checkup 500 rupees" → category="healthcare", subcategory="doctor"
    User: "filled gas 2000 rupees using phonepe" → category="transport", subcategory="fuel", payment_method="upi", payment_subcategory="phonepe"
    User: "movie ticket 400 rupees" → category="entertainment", subcategory="movies"
    
    Args:
        amount: Amount in original currency
        currency: Currency code (INR, USD, GBP, EUR, etc.)
        category: Main category from valid list
        description: What the expense was for
        payment_method: How it was paid (default: cash)
        payment_subcategory: Specific card/app name (optional)
        subcategory: Subcategory from valid list (optional)
        date: Date in YYYY-MM-DD format (defaults to today)
    
    Returns:
        Success message with expense details
    """
    
    try:
        logger.info(f"Adding expense: {amount} {currency} for {description}")
        
        # Use hardcoded test user
        user_id = TEST_USER_ID
        
        # Convert currency to USD
        logger.info(f"Converting {amount} {currency} to USD...")
        amount_usd, exchange_rate = convert_to_usd(amount, currency)
        logger.info(f"Converted: {amount} {currency} = ${amount_usd} USD (rate: {exchange_rate})")
        
        # Parse date if provided
        expense_date = datetime.now()
        if date:
            try:
                expense_date = datetime.strptime(date, "%Y-%m-%d")
                logger.info(f"Using provided date: {date}")
            except ValueError:
                logger.warning(f"Invalid date format '{date}', using today")
        
        # Normalize subcategory
        normalized_subcategory = normalize_subcategory(category, subcategory)
        
        # Create expense data
        expense_data = {
            "user_id": user_id,
            "amount": amount_usd,
            "original_amount": amount,
            "original_currency": currency,
            "user_currency": currency,
            "exchange_rate": exchange_rate,
            "category": category,
            "subcategory": normalized_subcategory,
            "description": description,
            "date": expense_date,
            "payment_method": payment_method,
            "payment_subcategory": payment_subcategory,
        }
        
        logger.info("Validating expense data...")
        
        # Validate with Pydantic
        expense = ExpenseCreate(**expense_data)
        logger.info("Validation passed")
        
        # Save to database
        logger.info("Saving to database...")
        db = await get_database()
        result = await db.expenses.insert_one(expense.model_dump())
        
        expense_id = str(result.inserted_id)
        logger.info(f"Saved successfully with ID: {expense_id}")
        
        # Format success message
        symbol = CURRENCY_SYMBOLS.get(currency, currency)
        formatted_amount = format_amount_with_symbol(amount, currency)
        
        success_message = (
            f"Expense added successfully!\n\n"
            f"Amount: {formatted_amount}\n"
            f"Category: {category}"
        )
        
        if normalized_subcategory:
            success_message += f" > {normalized_subcategory}"
        
        success_message += f"\nDescription: {description}"
        success_message += f"\nPayment: {payment_method}"
        
        if payment_subcategory:
            success_message += f" ({payment_subcategory})"
        
        success_message += f"\nStored as: ${amount_usd} USD"
        
        if exchange_rate != 1.0:
            success_message += f"\nExchange rate: 1 {currency} = {exchange_rate} USD"
        
        logger.info("Expense added successfully")
        return success_message
        
    except Exception as e:
        error_msg = f"Failed to add expense: {str(e)}"
        logger.error(error_msg)
        logger.exception("Full error details:")
        return error_msg


# ============================================
# TOOL 2: GET EXPENSES
# ============================================

@mcp.tool()
async def get_expenses(
    limit: int = 10,
    category: Optional[str] = None
) -> str:
    """
    Get recent expenses for the user.
    
    Returns a formatted list of expenses with all details needed for
    the user to review their spending.
    
    Args:
        limit: Maximum number of expenses to return (default: 10, max: 50)
        category: Filter by category (optional)
    
    Returns:
        Formatted list of expenses with descriptions, amounts, categories, and dates
    """
    
    try:
        logger.info(f"Getting expenses (limit: {limit}, category: {category})")
        
        # Validate limit
        if limit > 50:
            limit = 50
        if limit < 1:
            limit = 10
        
        # Use hardcoded test user
        user_id = TEST_USER_ID
        
        # Build query
        query = {"user_id": user_id}
        if category:
            query["category"] = category.lower()
        
        # Get expenses from database
        db = await get_database()
        expenses = await db.expenses.find(query).sort("date", -1).limit(limit).to_list(length=limit)
        
        if not expenses:
            if category:
                return f"No expenses found in category '{category}'"
            return "No expenses found. Add your first expense to get started!"
        
        logger.info(f"Found {len(expenses)} expenses")
        
        # Format output
        if category:
            result = f"Your {category.title()} Expenses ({len(expenses)}):\n\n"
        else:
            result = f"Your Recent Expenses ({len(expenses)}):\n\n"
        
        total_usd = 0
        
        for i, exp in enumerate(expenses, 1):
            # Get original amount and currency
            orig_amount = exp.get('original_amount', exp['amount'])
            orig_currency = exp.get('original_currency', 'USD')
            symbol = CURRENCY_SYMBOLS.get(orig_currency, orig_currency)
            
            # Format date
            exp_date = exp.get('date', datetime.now())
            if isinstance(exp_date, datetime):
                date_str = exp_date.strftime("%b %d, %Y")
            else:
                date_str = str(exp_date)[:10]
            
            # Build expense line
            result += f"{i}. {exp['description']} - {symbol}{orig_amount:.2f}\n"
            result += f"   Category: {exp['category']}"
            
            if exp.get('subcategory'):
                result += f" > {exp['subcategory']}"
            
            result += f"\n   Payment: {exp['payment_method']}"
            
            if exp.get('payment_subcategory'):
                result += f" ({exp['payment_subcategory']})"
            
            result += f"\n   Date: {date_str}\n\n"
            
            # Add to total
            total_usd += exp['amount']
        
        # Add total
        result += f"Total: ${total_usd:.2f} USD"
        
        if category:
            result += f" ({category} expenses)"
        
        return result
        
    except Exception as e:
        error_msg = f"Failed to get expenses: {str(e)}"
        logger.error(error_msg)
        logger.exception("Full error details:")
        return error_msg


# ============================================
# TOOL 3: DELETE EXPENSE
# ============================================

@mcp.tool()
async def delete_expense(
    description: str
) -> str:
    """
    Delete an expense by its description.
    
    Searches for an expense matching the description and deletes it.
    If multiple expenses match, shows a list and asks user to be more specific.
    
    Args:
        description: Description of the expense to delete (e.g., "pizza", "coffee", "uber")
    
    Examples:
        User: "delete the pizza expense" → description="pizza"
        User: "remove coffee" → description="coffee"
        User: "delete my uber ride" → description="uber"
    
    Returns:
        Success message with deleted expense details, or error if not found
    """
    
    try:
        logger.info(f"Deleting expense with description: {description}")
        
        # Use hardcoded test user
        user_id = TEST_USER_ID
        
        db = await get_database()
        
        # Find expenses matching description (case-insensitive)
        expenses = await db.expenses.find({
            "user_id": user_id,
            "description": {"$regex": description, "$options": "i"}
        }).to_list(length=10)
        
        # No matches found
        if not expenses:
            logger.info(f"No expenses found matching '{description}'")
            return f"No expense found matching '{description}'. Please check the description and try again."
        
        # Multiple matches found
        if len(expenses) > 1:
            logger.info(f"Multiple expenses found matching '{description}'")
            
            result = f"Multiple expenses found matching '{description}':\n\n"
            
            for i, exp in enumerate(expenses, 1):
                orig_amount = exp.get('original_amount', exp['amount'])
                orig_currency = exp.get('original_currency', 'USD')
                symbol = CURRENCY_SYMBOLS.get(orig_currency, orig_currency)
                
                exp_date = exp.get('date', datetime.now())
                if isinstance(exp_date, datetime):
                    date_str = exp_date.strftime("%b %d, %Y")
                else:
                    date_str = str(exp_date)[:10]
                
                result += f"{i}. {exp['description']} - {symbol}{orig_amount:.2f}\n"
                result += f"   Category: {exp['category']} | Date: {date_str}\n\n"
            
            result += "Please be more specific about which expense to delete."
            return result
        
        # Exact match found - delete it
        expense = expenses[0]
        
        # Get details before deleting
        orig_amount = expense.get('original_amount', expense['amount'])
        orig_currency = expense.get('original_currency', 'USD')
        symbol = CURRENCY_SYMBOLS.get(orig_currency, orig_currency)
        category = expense['category']
        desc = expense['description']
        
        # Delete the expense
        result = await db.expenses.delete_one({"_id": expense["_id"]})
        
        if result.deleted_count > 0:
            logger.info(f"Successfully deleted expense: {desc}")
            return f"Deleted expense: {desc} ({symbol}{orig_amount:.2f}) from {category}"
        else:
            logger.error(f"Failed to delete expense: {desc}")
            return f"Failed to delete expense. Please try again."
        
    except Exception as e:
        error_msg = f"Failed to delete expense: {str(e)}"
        logger.error(error_msg)
        logger.exception("Full error details:")
        return error_msg


# ============================================
# ENTRY POINT
# ============================================

if __name__ == "__main__":
    logger.info("Starting Expense Tracker MCP Server...")
    mcp.run()