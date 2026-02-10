"""
Pydantic Models for Database Collections
Defines the structure and validation for all database documents
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import logging

# Setup logging
logger = logging.getLogger(__name__)


# ============================================
# PREDEFINED CATEGORIES AND SUBCATEGORIES
# ============================================

# Main categories (standardized)
VALID_CATEGORIES = [
    "food",
    "transport",
    "education",
    "entertainment",
    "shopping",
    "utilities",
    "healthcare",
    "housing",
    "personal",
    "other"
]

# Subcategories for each main category
CATEGORY_SUBCATEGORIES = {
    "food": [
        "groceries",
        "restaurants",
        "fast_food",
        "coffee",
        "snacks",
        "other"
    ],
    "transport": [
        "fuel",
        "taxi",
        "bus",
        "train",
        "parking",
        "maintenance",
        "other"
    ],
    "education": [
        "books",
        "courses",
        "tuition",
        "supplies",
        "online_learning",
        "other"
    ],
    "entertainment": [
        "movies",
        "games",
        "music",
        "hobbies",
        "events",
        "subscriptions",
        "other"
    ],
    "shopping": [
        "clothes",
        "electronics",
        "home",
        "gifts",
        "accessories",
        "other"
    ],
    "utilities": [
        "electricity",
        "water",
        "gas",
        "internet",
        "phone",
        "other"
    ],
    "healthcare": [
        "doctor",
        "medicine",
        "insurance",
        "dental",
        "vision",
        "other"
    ],
    "housing": [
        "rent",
        "mortgage",
        "maintenance",
        "furniture",
        "repairs",
        "other"
    ],
    "personal": [
        "haircut",
        "gym",
        "cosmetics",
        "spa",
        "other"
    ],
    "other": []
}


# ============================================
# PREDEFINED PAYMENT METHODS
# ============================================

# Valid payment methods (standardized)
VALID_PAYMENT_METHODS = [
    "cash",
    "credit_card",
    "debit_card",
    "upi",
    "bank_transfer",
    "mobile_wallet",
    "check",
    "crypto",
    "other"
]

# Payment subcategories (for detailed tracking)
PAYMENT_SUBCATEGORIES = {
    "credit_card": ["visa", "mastercard", "amex", "discover", "rupay", "other"],
    "debit_card": ["visa", "mastercard", "rupay", "maestro", "other"],
    "upi": ["gpay", "phonepe", "paytm", "bhim", "other"],
    "mobile_wallet": ["paypal", "apple_pay", "google_pay", "amazon_pay", "paytm_wallet", "other"],
    "bank_transfer": ["neft", "rtgs", "imps", "other"],
    "crypto": ["bitcoin", "ethereum", "usdt", "other"],
    "cash": [],
    "check": [],
    "other": []
}

# Common payment method aliases/variations (for mapping)
PAYMENT_METHOD_MAPPING = {
    "card": "credit_card",
    "cc": "credit_card",
    "credit": "credit_card",
    "visa": "credit_card",
    "mastercard": "credit_card",
    "amex": "credit_card",
    
    "debit": "debit_card",
    "dc": "debit_card",
    
    "digital": "mobile_wallet",
    "wallet": "mobile_wallet",
    "paypal": "mobile_wallet",
    
    "gpay": "upi",
    "google_pay": "upi",
    "googlepay": "upi",
    "phonepe": "upi",
    "phone_pe": "upi",
    "paytm": "upi",
    
    "online": "bank_transfer",
    "bank": "bank_transfer",
    "transfer": "bank_transfer",
    
    "cheque": "check"
}

# Payment subcategory aliases
PAYMENT_SUBCATEGORY_MAPPING = {
    # UPI
    "google_pay": "gpay",
    "googlepay": "gpay",
    "phone_pe": "phonepe",
    
    # Cards
    "visa_card": "visa",
    "master_card": "mastercard",
    "american_express": "amex",
    
    # Bank transfers
    "bank_transfer": "neft",
    "online_transfer": "imps"
}


# ============================================
# CURRENCY SUPPORT
# ============================================

# Base currency for all storage (everything converted to this)
BASE_CURRENCY = "USD"

# Supported currencies (what users can input)
SUPPORTED_CURRENCIES = [
    "INR",  # Indian Rupee
    "USD",  # US Dollar
    "EUR",  # Euro
    "GBP",  # British Pound
    "AUD",  # Australian Dollar
    "CAD",  # Canadian Dollar
    "SGD",  # Singapore Dollar
    "AED",  # UAE Dirham
    "JPY",  # Japanese Yen
    "CNY",  # Chinese Yuan
]

# Currency symbols for display
CURRENCY_SYMBOLS = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "AUD": "A$",
    "CAD": "C$",
    "SGD": "S$",
    "AED": "د.إ",
    "JPY": "¥",
    "CNY": "¥",
}

# Currency names for AI to recognize (natural language)
CURRENCY_NAMES = {
    "rupees": "INR",
    "rupee": "INR",
    "inr": "INR",
    "rs": "INR",
    
    "dollars": "USD",
    "dollar": "USD",
    "usd": "USD",
    "bucks": "USD",
    
    "pounds": "GBP",
    "pound": "GBP",
    "gbp": "GBP",
    "quid": "GBP",
    
    "euros": "EUR",
    "euro": "EUR",
    "eur": "EUR",
    
    "yen": "JPY",
    "yuan": "CNY",
}


# ============================================
# EXPENSE MODELS
# ============================================

class ExpenseBase(BaseModel):
    """
    Base expense model with common fields
    
    IMPORTANT: All amounts stored in BASE_CURRENCY (USD)
    Original currency information preserved for user display
    """
    # Stored amount (ALWAYS in USD)
    amount: float = Field(..., gt=0, description="Expense amount in USD (base currency)")
    
    # Original input (for user display)
    original_amount: Optional[float] = Field(None, description="Amount in user's original currency")
    original_currency: str = Field(default="USD", description="User's original currency code")
    exchange_rate: Optional[float] = Field(None, description="Exchange rate used (original currency to USD)")
    
    # User's preferred currency for display
    user_currency: str = Field(default="USD", description="User's preferred display currency")
    
    # Category information
    category: str = Field(..., description="Main expense category")
    subcategory: Optional[str] = Field(None, description="Subcategory for detailed classification")
    
    description: str = Field(..., min_length=1, max_length=500, description="Expense description")
    date: datetime = Field(default_factory=datetime.now, description="Expense date")
    
    # Payment information
    payment_method: str = Field(default="cash", description="Payment method used")
    payment_subcategory: Optional[str] = Field(None, description="Specific card/app used")
    
    tags: List[str] = Field(default_factory=list, description="Optional tags for categorization")
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v: str) -> str:
        """
        Validate and normalize category.
        If invalid category provided, defaults to 'other' with warning.
        """
        v_lower = v.lower().strip()
        
        # Check if category is valid
        if v_lower not in VALID_CATEGORIES:
            logger.warning(f"Invalid category '{v}' provided. Defaulting to 'other'. Valid categories: {', '.join(VALID_CATEGORIES)}")
            return "other"
        
        return v_lower
    
    @field_validator('subcategory')
    @classmethod
    def validate_subcategory(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate and normalize subcategory.
        Note: Category-subcategory relationship validated at tool level.
        """
        if v is None:
            return None
        
        return v.lower().strip()
    
    @field_validator('payment_method')
    @classmethod
    def validate_payment_method(cls, v: str) -> str:
        """
        Validate and normalize payment method.
        Maps common variations to standard payment methods.
        """
        v_lower = v.lower().strip()
        
        # Check if it's a known variation
        if v_lower in PAYMENT_METHOD_MAPPING:
            mapped = PAYMENT_METHOD_MAPPING[v_lower]
            logger.info(f"Mapped payment method '{v}' to '{mapped}'")
            return mapped
        
        # Check if it's already a valid payment method
        if v_lower in VALID_PAYMENT_METHODS:
            return v_lower
        
        # Unknown payment method, default to 'other'
        logger.warning(f"Unknown payment method '{v}', defaulting to 'other'. Valid: {', '.join(VALID_PAYMENT_METHODS)}")
        return "other"
    
    @field_validator('payment_subcategory')
    @classmethod
    def validate_payment_subcategory(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate and normalize payment subcategory.
        """
        if v is None:
            return None
        
        v_lower = v.lower().strip()
        
        # Map common aliases
        if v_lower in PAYMENT_SUBCATEGORY_MAPPING:
            return PAYMENT_SUBCATEGORY_MAPPING[v_lower]
        
        return v_lower
    
    @field_validator('original_currency', 'user_currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """
        Validate currency code
        """
        v_upper = v.upper().strip()
        
        if v_upper not in SUPPORTED_CURRENCIES:
            logger.warning(f"Unsupported currency '{v}', defaulting to 'USD'. Supported: {', '.join(SUPPORTED_CURRENCIES)}")
            return "USD"
        
        return v_upper
    
    @field_validator('tags')
    @classmethod
    def clean_tags(cls, v: List[str]) -> List[str]:
        """Clean and normalize tags"""
        return [tag.lower().strip() for tag in v if tag.strip()]
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }


class ExpenseCreate(ExpenseBase):
    """
    Model for creating a new expense
    Used when user adds an expense
    """
    user_id: str = Field(..., min_length=1, description="User identifier")
    is_recurring: bool = Field(default=False, description="Whether expense is recurring")
    recurring_frequency: Optional[str] = Field(None, description="Frequency if recurring (daily, weekly, monthly)")


class ExpenseInDB(ExpenseBase):
    """
    Model for expense as stored in database
    Includes MongoDB _id and timestamps
    """
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    is_recurring: bool = False
    recurring_frequency: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    model_config = {
        "populate_by_name": True
    }


class ExpenseUpdate(BaseModel):
    """
    Model for updating an expense
    All fields are optional
    """
    amount: Optional[float] = Field(None, gt=0)
    original_amount: Optional[float] = None
    original_currency: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    date: Optional[datetime] = None
    payment_method: Optional[str] = None
    payment_subcategory: Optional[str] = None
    tags: Optional[List[str]] = None
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        """Validate category if provided"""
        if v is None:
            return None
        
        v_lower = v.lower().strip()
        if v_lower not in VALID_CATEGORIES:
            logger.warning(f"Invalid category '{v}' provided. Defaulting to 'other'.")
            return "other"
        
        return v_lower
    
    @field_validator('subcategory')
    @classmethod
    def validate_subcategory(cls, v: Optional[str]) -> Optional[str]:
        """Validate subcategory if provided"""
        if v is None:
            return None
        return v.lower().strip()
    
    @field_validator('payment_method')
    @classmethod
    def validate_payment_method(cls, v: Optional[str]) -> Optional[str]:
        """Validate payment method if provided"""
        if v is None:
            return None
        
        v_lower = v.lower().strip()
        
        # Check mapping
        if v_lower in PAYMENT_METHOD_MAPPING:
            return PAYMENT_METHOD_MAPPING[v_lower]
        
        # Check if valid
        if v_lower in VALID_PAYMENT_METHODS:
            return v_lower
        
        # Default to 'other'
        logger.warning(f"Unknown payment method '{v}', defaulting to 'other'")
        return "other"


# ============================================
# CATEGORY MODELS
# ============================================

class CategoryBase(BaseModel):
    """
    Base category model
    Users can customize their own categories beyond predefined ones
    """
    name: str = Field(..., min_length=1, max_length=50, description="Category name")
    budget: Optional[float] = Field(None, gt=0, description="Monthly budget for category")
    color: Optional[str] = Field(None, description="Color for visualization (hex code)")
    icon: Optional[str] = Field(None, description="Icon for UI (emoji or icon name)")
    
    @field_validator('name')
    @classmethod
    def name_to_lowercase(cls, v: str) -> str:
        return v.lower().strip()


class CategoryCreate(CategoryBase):
    """
    Model for creating a category
    """
    user_id: str = Field(..., description="User identifier")


class CategoryInDB(CategoryBase):
    """
    Model for category in database
    """
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    model_config = {
        "populate_by_name": True
    }


# ============================================
# BUDGET MODELS
# ============================================

class BudgetBase(BaseModel):
    """
    Base budget model
    """
    month: str = Field(..., description="Month in YYYY-MM format")
    total_budget: float = Field(..., gt=0, description="Total monthly budget")
    currency: str = Field(default="USD", description="Budget currency")
    category_budgets: dict = Field(default_factory=dict, description="Budget per category")
    
    @field_validator('month')
    @classmethod
    def validate_month_format(cls, v: str) -> str:
        """Validate month is in YYYY-MM format"""
        try:
            datetime.strptime(v, "%Y-%m")
            return v
        except ValueError:
            raise ValueError("Month must be in YYYY-MM format (e.g., 2025-02)")


class BudgetCreate(BudgetBase):
    """
    Model for creating a budget
    """
    user_id: str = Field(..., description="User identifier")


class BudgetInDB(BudgetBase):
    """
    Model for budget in database
    """
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    spent: float = Field(default=0.0, description="Amount spent so far")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    model_config = {
        "populate_by_name": True
    }


# ============================================
# USER MODELS
# ============================================

class UserBase(BaseModel):
    """
    Base user model
    """
    email: str = Field(..., description="User email")
    full_name: Optional[str] = Field(None, description="User full name")
    country_code: Optional[str] = Field(None, description="User country code (IN, US, GB, etc.)")
    
    preferences: dict = Field(
        default_factory=lambda: {
            "currency": "USD",
            "budget_alerts": True,
            "notification_threshold": 0.8,
            "default_categories": VALID_CATEGORIES,
            "show_converted_amounts": True
        },
        description="User preferences"
    )
    
    @field_validator('email')
    @classmethod
    def email_to_lowercase(cls, v: str) -> str:
        return v.lower().strip()


class UserCreate(UserBase):
    """
    Model for creating a user
    """
    user_id: str = Field(..., description="Unique user identifier from auth")


class UserInDB(UserBase):
    """
    Model for user in database
    """
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    
    model_config = {
        "populate_by_name": True
    }


# ============================================
# VALIDATION HELPER FUNCTIONS
# ============================================

def validate_expense_data(data: dict) -> ExpenseCreate:
    """
    Validate expense data and return ExpenseCreate model
    Raises validation error if data is invalid
    """
    return ExpenseCreate(**data)


def validate_budget_data(data: dict) -> BudgetCreate:
    """
    Validate budget data and return BudgetCreate model
    """
    return BudgetCreate(**data)


def validate_category_data(data: dict) -> CategoryCreate:
    """
    Validate category data and return CategoryCreate model
    """
    return CategoryCreate(**data)


def validate_subcategory_for_category(category: str, subcategory: str) -> bool:
    """
    Validate if subcategory is valid for given category
    
    Args:
        category: Main category name
        subcategory: Subcategory name to validate
    
    Returns:
        True if valid, False otherwise
    """
    category = category.lower().strip()
    subcategory = subcategory.lower().strip()
    
    if category not in CATEGORY_SUBCATEGORIES:
        return False
    
    valid_subcategories = CATEGORY_SUBCATEGORIES[category]
    return subcategory in valid_subcategories


def validate_payment_subcategory_for_method(payment_method: str, payment_subcategory: str) -> bool:
    """
    Validate if payment subcategory is valid for given payment method
    
    Args:
        payment_method: Payment method name
        payment_subcategory: Payment subcategory to validate
    
    Returns:
        True if valid, False otherwise
    """
    payment_method = payment_method.lower().strip()
    payment_subcategory = payment_subcategory.lower().strip()
    
    if payment_method not in PAYMENT_SUBCATEGORIES:
        return False
    
    valid_subcategories = PAYMENT_SUBCATEGORIES[payment_method]
    return payment_subcategory in valid_subcategories


def get_valid_categories() -> List[str]:
    """
    Get list of valid categories
    Useful for displaying to users or in tools
    """
    return VALID_CATEGORIES.copy()


def get_subcategories_for_category(category: str) -> List[str]:
    """
    Get valid subcategories for a given category
    
    Args:
        category: Main category name
    
    Returns:
        List of valid subcategories, empty list if category invalid
    """
    category = category.lower().strip()
    return CATEGORY_SUBCATEGORIES.get(category, [])


def get_valid_payment_methods() -> List[str]:
    """
    Get list of valid payment methods
    """
    return VALID_PAYMENT_METHODS.copy()


def get_subcategories_for_payment(payment_method: str) -> List[str]:
    """
    Get valid subcategories for a given payment method
    
    Args:
        payment_method: Payment method name
    
    Returns:
        List of valid payment subcategories
    """
    payment_method = payment_method.lower().strip()
    return PAYMENT_SUBCATEGORIES.get(payment_method, [])


def get_currency_symbol(currency_code: str) -> str:
    """
    Get currency symbol for display
    
    Args:
        currency_code: Currency code (INR, USD, etc.)
    
    Returns:
        Currency symbol (₹, $, etc.)
    """
    return CURRENCY_SYMBOLS.get(currency_code.upper(), currency_code)