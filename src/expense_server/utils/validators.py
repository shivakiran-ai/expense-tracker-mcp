"""
Validation and Inference Utilities for Expense Tracker
Provides helper functions to validate and infer expense attributes
"""

import logging
from typing import Optional

# Import from models
from src.expense_server.database.models import (
    VALID_CATEGORIES,
    VALID_PAYMENT_METHODS,
    CATEGORY_SUBCATEGORIES,
    PAYMENT_SUBCATEGORIES,
    get_subcategories_for_category,
)

# Setup logging
logger = logging.getLogger(__name__)


# ============================================
# CATEGORY VALIDATION AND INFERENCE
# ============================================

def validate_and_fix_category(category: str, description: str) -> str:
    """
    Validate category and fix if needed by checking description.
    
    Args:
        category: Category provided by Claude
        description: Expense description
    
    Returns:
        Valid category from VALID_CATEGORIES
    
    Examples:
        validate_and_fix_category("groceries", "Bought groceries")
        Returns: "food"
        
        validate_and_fix_category("food", "Bought groceries")
        Returns: "food"
    """
    if not category:
        logger.warning("No category provided, inferring from description")
        return infer_category_from_description(description)
    
    category_lower = category.lower().strip()
    
    # If valid category, return it
    if category_lower in VALID_CATEGORIES:
        logger.info(f"Valid category: '{category_lower}'")
        return category_lower
    
    # Invalid category - try to infer from description
    logger.warning(f"Invalid category '{category}', inferring from description")
    return infer_category_from_description(description)


def infer_category_from_description(description: str) -> str:
    """
    Infer category from description keywords.
    
    Args:
        description: Expense description
    
    Returns:
        Most likely category from VALID_CATEGORIES
    
    Examples:
        infer_category_from_description("Bought groceries")
        Returns: "food"
        
        infer_category_from_description("Doctor checkup")
        Returns: "healthcare"
    """
    if not description:
        return "other"
    
    desc_lower = description.lower()
    
    # Food keywords
    if any(word in desc_lower for word in [
        "grocery", "groceries", "food", "restaurant", "cafe", "coffee",
        "lunch", "dinner", "breakfast", "meal", "pizza", "burger",
        "snack", "eat", "ate", "dining", "restaurant"
    ]):
        logger.info(f"Category inferred: 'food' from '{description}'")
        return "food"
    
    # Transport keywords
    if any(word in desc_lower for word in [
        "fuel", "gas", "petrol", "diesel", "taxi", "uber", "ola",
        "bus", "train", "metro", "parking", "ride", "transport", "cab"
    ]):
        logger.info(f"Category inferred: 'transport' from '{description}'")
        return "transport"
    
    # Healthcare keywords
    if any(word in desc_lower for word in [
        "doctor", "hospital", "clinic", "medicine", "pharmacy",
        "medical", "health", "dentist", "dental", "checkup", "dr"
    ]):
        logger.info(f"Category inferred: 'healthcare' from '{description}'")
        return "healthcare"
    
    # Utilities keywords
    if any(word in desc_lower for word in [
        "electricity", "electric", "power", "internet", "wifi",
        "water", "phone", "mobile", "bill", "utility"
    ]):
        logger.info(f"Category inferred: 'utilities' from '{description}'")
        return "utilities"
    
    # Entertainment keywords
    if any(word in desc_lower for word in [
        "movie", "cinema", "netflix", "spotify", "prime", "game",
        "concert", "show", "entertainment", "music", "film"
    ]):
        logger.info(f"Category inferred: 'entertainment' from '{description}'")
        return "entertainment"
    
    # Education keywords
    if any(word in desc_lower for word in [
        "book", "course", "class", "tuition", "school", "college",
        "education", "learning", "study"
    ]):
        logger.info(f"Category inferred: 'education' from '{description}'")
        return "education"
    
    # Shopping keywords
    if any(word in desc_lower for word in [
        "clothes", "shirt", "pants", "dress", "shoes", "laptop",
        "phone", "electronics", "gift", "shopping", "mall"
    ]):
        logger.info(f"Category inferred: 'shopping' from '{description}'")
        return "shopping"
    
    # Housing keywords
    if any(word in desc_lower for word in [
        "rent", "mortgage", "furniture", "repair", "home", "house"
    ]):
        logger.info(f"Category inferred: 'housing' from '{description}'")
        return "housing"
    
    # Personal keywords
    if any(word in desc_lower for word in [
        "haircut", "salon", "barber", "gym", "fitness", "spa"
    ]):
        logger.info(f"Category inferred: 'personal' from '{description}'")
        return "personal"
    
    logger.info(f"No category match for '{description}', using 'other'")
    return "other"


# ============================================
# SUBCATEGORY INFERENCE
# ============================================

def infer_subcategory_from_description(category: str, description: str) -> str:
    """
    Infer subcategory with intelligent singular/plural handling.
    
    Handles:
    - "movie" → "movies" ✅
    - "book" → "books" ✅
    - "restaurant" → "restaurants" ✅
    - "grocery" → "groceries" ✅
    
    Args:
        category: The main category
        description: The expense description
    
    Returns:
        Valid subcategory name or "other"
    
    Examples:
        infer_subcategory_from_description("healthcare", "Doctor checkup")
        Returns: "doctor"
        
        infer_subcategory_from_description("food", "Bought groceries")
        Returns: "groceries"
        
        infer_subcategory_from_description("entertainment", "Movie ticket")
        Returns: "movies"
    """
    if not description:
        return "other"
    
    # Get valid subcategories for this category
    valid_subcats = get_subcategories_for_category(category)
    
    if not valid_subcats:
        return "other"
    
    desc_lower = description.lower()
    
    # STEP 1: Try exact match first (fastest)
    for subcat in valid_subcats:
        if subcat in desc_lower:
            logger.info(f"Exact match: '{subcat}' in '{description}'")
            return subcat
    
    # STEP 2: Try singular/plural variations
    for subcat in valid_subcats:
        # Handle: "movies" (plural) ↔ "movie" (singular)
        if subcat.endswith('s') and len(subcat) > 2:
            singular = subcat[:-1]  # "movies" → "movie"
            if singular in desc_lower:
                logger.info(f"Singular→Plural: '{singular}' → '{subcat}'")
                return subcat
        
        # Handle: "grocery" (singular) ↔ "groceries" (plural with ies)
        if subcat.endswith('ies') and len(subcat) > 4:
            singular_y = subcat[:-3] + 'y'  # "groceries" → "grocery"
            if singular_y in desc_lower:
                logger.info(f"Y-ending: '{singular_y}' → '{subcat}'")
                return subcat
        
        # Handle: "bus" (singular) ↔ "buses" (plural with es)
        if subcat.endswith('es') and len(subcat) > 3:
            singular_no_es = subcat[:-2]  # "buses" → "bus"
            if singular_no_es in desc_lower:
                logger.info(f"ES-ending: '{singular_no_es}' → '{subcat}'")
                return subcat
    
    # STEP 3: Special keyword variations for common cases
    
    # Food category special cases
    if category == "food":
        if any(word in desc_lower for word in ["restaurant", "lunch", "dinner", "ate", "dining", "dine"]):
            logger.info("Food keyword: restaurant-related → 'restaurants'")
            return "restaurants"
        if any(word in desc_lower for word in ["grocery", "groceries", "vegetable", "fruit", "supermarket", "veggies"]):
            logger.info("Food keyword: grocery-related → 'groceries'")
            return "groceries"
        if any(word in desc_lower for word in ["fast food", "fastfood", "burger", "pizza", "mcdonald", "kfc", "dominos"]):
            logger.info("Food keyword: fast food-related → 'fast_food'")
            return "fast_food"
        if any(word in desc_lower for word in ["coffee", "cafe", "starbucks", "ccd", "espresso", "latte"]):
            logger.info("Food keyword: coffee-related → 'coffee'")
            return "coffee"
        if any(word in desc_lower for word in ["snack", "chips", "biscuit", "cookie"]):
            logger.info("Food keyword: snack-related → 'snacks'")
            return "snacks"
    
    # Transport category special cases
    if category == "transport":
        if any(word in desc_lower for word in ["petrol", "diesel", "filled", "gas"]):
            logger.info("Transport keyword: fuel-related → 'fuel'")
            return "fuel"
        if any(word in desc_lower for word in ["uber", "ola", "cab", "taxi"]):
            logger.info("Transport keyword: taxi-related → 'taxi'")
            return "taxi"
        if any(word in desc_lower for word in ["metro", "subway"]):
            logger.info("Transport keyword: train-related → 'train'")
            return "train"
    
    # Healthcare category special cases
    if category == "healthcare":
        if any(word in desc_lower for word in ["dr", "dr.", "clinic", "checkup", "hospital", "physician"]):
            logger.info("Healthcare keyword: doctor-related → 'doctor'")
            return "doctor"
        if any(word in desc_lower for word in ["pharmacy", "drug", "tablet", "pill", "medication", "med"]):
            logger.info("Healthcare keyword: medicine-related → 'medicine'")
            return "medicine"
        if any(word in desc_lower for word in ["dentist", "dental", "teeth", "tooth"]):
            logger.info("Healthcare keyword: dental-related → 'dental'")
            return "dental"
        if any(word in desc_lower for word in ["eye", "glasses", "vision", "optical"]):
            logger.info("Healthcare keyword: vision-related → 'vision'")
            return "vision"
    
    # Utilities category special cases
    if category == "utilities":
        if any(word in desc_lower for word in ["electric", "power", "current"]):
            logger.info("Utilities keyword: electricity-related → 'electricity'")
            return "electricity"
        if any(word in desc_lower for word in ["wifi", "broadband", "internet"]):
            logger.info("Utilities keyword: internet-related → 'internet'")
            return "internet"
        if any(word in desc_lower for word in ["mobile", "cellular"]):
            logger.info("Utilities keyword: phone-related → 'phone'")
            return "phone"
    
    # Entertainment category special cases
    if category == "entertainment":
        if any(word in desc_lower for word in ["movie", "film", "cinema", "theatre", "theater"]):
            logger.info("Entertainment keyword: movie-related → 'movies'")
            return "movies"
        if any(word in desc_lower for word in ["game", "gaming", "videogame", "video game"]):
            logger.info("Entertainment keyword: game-related → 'games'")
            return "games"
        if any(word in desc_lower for word in ["netflix", "prime", "spotify", "subscription"]):
            logger.info("Entertainment keyword: subscription-related → 'subscriptions'")
            return "subscriptions"
        if any(word in desc_lower for word in ["concert", "show", "event", "festival"]):
            logger.info("Entertainment keyword: event-related → 'events'")
            return "events"
    
    # Education category special cases
    if category == "education":
        if any(word in desc_lower for word in ["book", "textbook", "novel"]):
            logger.info("Education keyword: book-related → 'books'")
            return "books"
        if any(word in desc_lower for word in ["course", "class", "training", "workshop"]):
            logger.info("Education keyword: course-related → 'courses'")
            return "courses"
        if any(word in desc_lower for word in ["tuition", "fee", "school"]):
            logger.info("Education keyword: tuition-related → 'tuition'")
            return "tuition"
    
    # Shopping category special cases
    if category == "shopping":
        if any(word in desc_lower for word in ["shirt", "pants", "dress", "clothes", "clothing", "jeans"]):
            logger.info("Shopping keyword: clothes-related → 'clothes'")
            return "clothes"
        if any(word in desc_lower for word in ["laptop", "computer", "phone", "electronics", "gadget"]):
            logger.info("Shopping keyword: electronics-related → 'electronics'")
            return "electronics"
        if any(word in desc_lower for word in ["gift", "present"]):
            logger.info("Shopping keyword: gift-related → 'gifts'")
            return "gifts"
    
    # Personal category special cases
    if category == "personal":
        if any(word in desc_lower for word in ["haircut", "barber", "salon", "hair"]):
            logger.info("Personal keyword: haircut-related → 'haircut'")
            return "haircut"
        if any(word in desc_lower for word in ["gym", "fitness", "workout"]):
            logger.info("Personal keyword: gym-related → 'gym'")
            return "gym"
        if any(word in desc_lower for word in ["spa", "massage"]):
            logger.info("Personal keyword: spa-related → 'spa'")
            return "spa"
    
    logger.info(f"No match for '{description}' in category '{category}', using 'other'")
    return "other"


# ============================================
# PAYMENT METHOD VALIDATION
# ============================================

def normalize_payment_method(payment_method: str) -> str:
    """
    Normalize payment method to standard format.
    
    Args:
        payment_method: Payment method from Claude
    
    Returns:
        Normalized payment method from VALID_PAYMENT_METHODS
    
    Examples:
        normalize_payment_method("google pay")
        Returns: "upi"
        
        normalize_payment_method("card")
        Returns: "credit_card"
    """
    if not payment_method:
        return "cash"
    
    pm_lower = payment_method.lower().strip().replace(" ", "_").replace("-", "_")
    
    # Direct mappings
    mappings = {
        "google_pay": "upi",
        "googlepay": "upi",
        "gpay": "upi",
        "g_pay": "upi",
        "phonepe": "upi",
        "phone_pe": "upi",
        "paytm": "upi",
        "bhim": "upi",
        "card": "credit_card",
        "credit": "credit_card",
        "debit": "debit_card",
        "online": "bank_transfer",
        "bank": "bank_transfer",
        "transfer": "bank_transfer",
        "neft": "bank_transfer",
        "rtgs": "bank_transfer",
        "imps": "bank_transfer",
    }
    
    if pm_lower in mappings:
        result = mappings[pm_lower]
        logger.info(f"Normalized payment method: '{payment_method}' → '{result}'")
        return result
    
    # Check if it's already valid
    if pm_lower in VALID_PAYMENT_METHODS:
        return pm_lower
    
    logger.warning(f"Unknown payment method '{payment_method}', defaulting to 'cash'")
    return "cash"


def infer_payment_subcategory(
    payment_method: str,
    original_payment: str,
    description: str
) -> Optional[str]:
    """
    Infer payment subcategory from payment method or description.
    
    Args:
        payment_method: Normalized payment method (e.g., "upi", "credit_card")
        original_payment: Original payment string from Claude (e.g., "google_pay")
        description: Expense description
    
    Returns:
        Payment subcategory or None
    
    Examples:
        infer_payment_subcategory("upi", "google_pay", "Bought groceries")
        Returns: "gpay"
        
        infer_payment_subcategory("credit_card", "visa card", "Movie ticket")
        Returns: "visa"
    """
    # Combine original payment and description for checking
    check_text = f"{original_payment} {description}".lower()
    
    # UPI subcategories
    if payment_method == "upi":
        if any(word in check_text for word in ["google pay", "googlepay", "gpay", "g pay", "g-pay"]):
            logger.info("Inferred payment subcategory: 'gpay'")
            return "gpay"
        elif any(word in check_text for word in ["phonepe", "phone pe", "phone-pe"]):
            logger.info("Inferred payment subcategory: 'phonepe'")
            return "phonepe"
        elif any(word in check_text for word in ["paytm"]):
            logger.info("Inferred payment subcategory: 'paytm'")
            return "paytm"
        elif any(word in check_text for word in ["bhim"]):
            logger.info("Inferred payment subcategory: 'bhim'")
            return "bhim"
    
    # Credit card subcategories
    elif payment_method == "credit_card":
        if any(word in check_text for word in ["visa"]):
            logger.info("Inferred payment subcategory: 'visa'")
            return "visa"
        elif any(word in check_text for word in ["mastercard", "master card", "master"]):
            logger.info("Inferred payment subcategory: 'mastercard'")
            return "mastercard"
        elif any(word in check_text for word in ["amex", "american express"]):
            logger.info("Inferred payment subcategory: 'amex'")
            return "amex"
        elif any(word in check_text for word in ["rupay"]):
            logger.info("Inferred payment subcategory: 'rupay'")
            return "rupay"
    
    # Debit card subcategories
    elif payment_method == "debit_card":
        if any(word in check_text for word in ["visa"]):
            logger.info("Inferred payment subcategory: 'visa'")
            return "visa"
        elif any(word in check_text for word in ["mastercard", "master card", "master"]):
            logger.info("Inferred payment subcategory: 'mastercard'")
            return "mastercard"
        elif any(word in check_text for word in ["rupay"]):
            logger.info("Inferred payment subcategory: 'rupay'")
            return "rupay"
    
    # Bank transfer subcategories
    elif payment_method == "bank_transfer":
        if any(word in check_text for word in ["neft"]):
            logger.info("Inferred payment subcategory: 'neft'")
            return "neft"
        elif any(word in check_text for word in ["rtgs"]):
            logger.info("Inferred payment subcategory: 'rtgs'")
            return "rtgs"
        elif any(word in check_text for word in ["imps"]):
            logger.info("Inferred payment subcategory: 'imps'")
            return "imps"
    
    return None