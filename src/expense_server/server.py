"""
FastMCP Server for Expense Tracker
Production-ready MCP tools for expense management
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastmcp import FastMCP
from datetime import datetime
import logging
from typing import Optional
from bson import ObjectId

# Import database modules
from src.expense_server.database.connection import get_database
from src.expense_server.database.models import (
    ExpenseCreate,
    VALID_CATEGORIES,
    VALID_PAYMENT_METHODS,
    SUPPORTED_CURRENCIES,
    CURRENCY_SYMBOLS,
    CATEGORY_SUBCATEGORIES,
)

# Import utility modules
from src.expense_server.utils.currency import (
    convert_to_usd,
    format_amount_with_symbol,
)
from src.expense_server.utils.validators import (
    validate_and_fix_category,
    infer_subcategory_from_description,
    normalize_payment_method,
    infer_payment_subcategory,
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
    
    Converts amounts to USD for storage while preserving original currency.
    
    VALID CATEGORIES:
    {', '.join(VALID_CATEGORIES)}
    
    Category inference keywords:
    - food: groceries, restaurant, coffee, pizza, burger, meal, lunch, dinner
    - transport: fuel, gas, taxi, uber, bus, train, parking, ride
    - healthcare: doctor, hospital, medicine, pharmacy, dentist, checkup
    - utilities: electricity, internet, water, phone, bill
    - entertainment: movie, netflix, game, concert, music
    - education: book, course, tuition, school, class
    - shopping: clothes, laptop, electronics, gift, shopping
    - housing: rent, mortgage, furniture, repair
    - personal: haircut, gym, spa, salon, fitness
    
    VALID PAYMENT METHODS:
    {', '.join(VALID_PAYMENT_METHODS)}
    
    Payment method keywords:
    - "gpay", "google pay" -> payment_method="upi"
    - "phonepe" -> payment_method="upi"
    - "paytm" -> payment_method="upi"
    - "card" -> payment_method="credit_card"
    - "cash" -> payment_method="cash"
    
    SUPPORTED CURRENCIES:
    {', '.join(SUPPORTED_CURRENCIES)}
    
    Examples:
    "Bought groceries 800 rupees" -> category="food", description="Bought groceries"
    "Doctor checkup 500 rupees paid by gpay" -> category="healthcare", payment_method="upi"
    "Filled fuel 2000 rupees" -> category="transport", description="Filled fuel"
    
    Args:
        amount: Amount in original currency
        currency: Currency code (INR, USD, EUR, GBP)
        category: Main category
        description: What the expense was for
        payment_method: How it was paid (default: cash)
        payment_subcategory: Specific app/card (optional)
        subcategory: Specific type (optional, auto-inferred)
        date: Date in YYYY-MM-DD format (defaults to today)
    
    Returns:
        Success message with expense details
    """
    
    try:
        logger.info(f"Adding expense: {amount} {currency} for {description}")
        logger.info(f"Received - category: '{category}', payment_method: '{payment_method}'")
        
        # Use hardcoded test user
        user_id = TEST_USER_ID
        
        # Store original payment method before normalization
        original_payment_method = payment_method
        
        # Validate and fix category using validator utility
        validated_category = validate_and_fix_category(category, description)
        if validated_category != category.lower():
            logger.info(f"Category corrected: '{category}' -> '{validated_category}'")
        
        # Normalize payment method using validator utility
        normalized_payment_method = normalize_payment_method(payment_method)
        
        # Infer subcategory from description using validator utility
        inferred_subcategory = infer_subcategory_from_description(validated_category, description)
        
        # Infer payment subcategory using validator utility
        inferred_payment_subcategory = infer_payment_subcategory(
            normalized_payment_method,
            original_payment_method,
            description
        )
        
        logger.info(f"Final values - category: '{validated_category}', subcategory: '{inferred_subcategory}'")
        logger.info(f"Final payment - method: '{normalized_payment_method}', subcategory: '{inferred_payment_subcategory}'")
        
        # Convert currency to USD using currency utility
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
        
        # Create expense data with validated/inferred values
        expense_data = {
            "user_id": user_id,
            "amount": amount_usd,
            "original_amount": amount,
            "original_currency": currency,
            "user_currency": currency,
            "exchange_rate": exchange_rate,
            "category": validated_category,
            "subcategory": inferred_subcategory,
            "description": description,
            "date": expense_date,
            "payment_method": normalized_payment_method,
            "payment_subcategory": inferred_payment_subcategory,
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
            f"Category: {validated_category}"
        )
        
        if inferred_subcategory:
            success_message += f" > {inferred_subcategory}"
        
        success_message += f"\nDescription: {description}"
        success_message += f"\nPayment: {normalized_payment_method}"
        
        if inferred_payment_subcategory:
            success_message += f" ({inferred_payment_subcategory})"
        
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
    Get recent expenses for the user with detailed formatting.
    
    Use this tool when the user asks to:
    - "show my expenses"
    - "list my expenses"
    - "what did I spend"
    - "show my recent expenses"
    - "get my food expenses" (with category filter)
    - "show last 5 expenses" (with limit)
    
    This tool returns a formatted list with:
    - Description and amount in original currency
    - Category and subcategory breakdown
    - Payment method details
    - Date information
    - Total amount in USD
    
    Args:
        limit: Maximum number of expenses to return (default: 10, max: 50)
               Use this when user says "last 5 expenses" or "show 20 expenses"
        
        category: Filter by specific category (optional, lowercase)
                  Valid categories: food, transport, healthcare, utilities, 
                  entertainment, education, shopping, housing, personal
                  Use this when user says "show food expenses" or "healthcare spending"
    
    Returns:
        Formatted string with expense details including:
        - Numbered list of expenses
        - Original amount with currency symbol
        - Category > subcategory
        - Payment method (with subcategory if applicable)
        - Date in readable format
        - Total in USD
    
    Examples:
        get_expenses(limit=10) - Show last 10 expenses
        get_expenses(limit=5) - Show last 5 expenses
        get_expenses(category="food") - Show all food expenses
        get_expenses(limit=3, category="healthcare") - Show last 3 healthcare expenses
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
    
    Args:
        description: Description of the expense to delete
    
    Returns:
        Success message or error
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



