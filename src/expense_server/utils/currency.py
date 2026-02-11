"""
Currency conversion utilities
Uses ExchangeRate-API for real-time rates with caching
"""

import requests
from typing import Tuple, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Cache exchange rates to reduce API calls
# Key: "FROM_TO" (e.g., "INR_USD")
# Value: {"rate": float, "timestamp": datetime}
_rate_cache = {}

# Cache expiry: 24 hours
CACHE_DURATION_HOURS = 24

# Base currency (everything converted to this)
BASE_CURRENCY = "USD"


def get_exchange_rate(from_currency: str, to_currency: str = "USD") -> float:
    """
    Get exchange rate from one currency to another.
    Uses ExchangeRate-API with 24-hour caching.
    
    Free tier: 1,500 requests/month
    With caching: Supports many users without hitting limit
    
    Args:
        from_currency: Source currency code (e.g., "INR")
        to_currency: Target currency code (default: "USD")
    
    Returns:
        Exchange rate (e.g., 1 INR = 0.012 USD returns 0.012)
    
    Example:
        >>> get_exchange_rate("INR", "USD")
        0.012
        # Means: 1 INR = 0.012 USD
    """
    # If same currency, no conversion needed
    if from_currency == to_currency:
        return 1.0
    
    # Check cache first
    cache_key = f"{from_currency}_{to_currency}"
    now = datetime.now()
    
    if cache_key in _rate_cache:
        cached_data = _rate_cache[cache_key]
        cache_age = now - cached_data["timestamp"]
        
        # If cache is still valid (less than 24 hours old)
        if cache_age < timedelta(hours=CACHE_DURATION_HOURS):
            logger.info(f"Using cached rate for {from_currency} to {to_currency}: {cached_data['rate']}")
            return cached_data["rate"]
        else:
            logger.info(f"Cache expired for {cache_key}, fetching new rate")
    
    # Fetch from API
    try:
        # ExchangeRate-API (Free tier: 1,500 requests/month)
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        
        logger.info(f"Fetching exchange rate from API: {from_currency} to {to_currency}")
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Get rate for target currency
        if to_currency not in data["rates"]:
            raise ValueError(f"Currency {to_currency} not found in API response")
        
        rate = data["rates"][to_currency]
        
        # Cache the rate
        _rate_cache[cache_key] = {
            "rate": rate,
            "timestamp": now
        }
        
        logger.info(f"✅ Fetched exchange rate: 1 {from_currency} = {rate} {to_currency}")
        
        return rate
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ API request failed: {e}")
        return _get_fallback_rate(from_currency, to_currency)
    
    except (KeyError, ValueError) as e:
        logger.error(f"❌ Failed to parse API response: {e}")
        return _get_fallback_rate(from_currency, to_currency)
    
    except Exception as e:
        logger.error(f"❌ Unexpected error getting exchange rate: {e}")
        return _get_fallback_rate(from_currency, to_currency)


def _get_fallback_rate(from_currency: str, to_currency: str) -> float:
    """
    Get fallback/approximate exchange rate when API fails.
    
    These are approximate rates updated manually.
    Should be updated monthly for accuracy.
    
    Returns:
        Approximate exchange rate
    """
    # Approximate rates (as of February 2025)
    # Update these monthly for better accuracy
    fallback_rates_to_usd = {
        "INR": 0.012,   # 1 INR ≈ 0.012 USD (₹83.33 = $1)
        "GBP": 1.27,    # 1 GBP ≈ 1.27 USD
        "EUR": 1.09,    # 1 EUR ≈ 1.09 USD
        "AUD": 0.65,    # 1 AUD ≈ 0.65 USD
        "CAD": 0.74,    # 1 CAD ≈ 0.74 USD
        "JPY": 0.0067,  # 1 JPY ≈ 0.0067 USD
        "CNY": 0.14,    # 1 CNY ≈ 0.14 USD
        "SGD": 0.74,    # 1 SGD ≈ 0.74 USD
        "AED": 0.27,    # 1 AED ≈ 0.27 USD
        "USD": 1.0,     # 1 USD = 1 USD
    }
    
    if to_currency == "USD":
        rate = fallback_rates_to_usd.get(from_currency, 1.0)
        logger.warning(f"⚠️ Using fallback rate: 1 {from_currency} = {rate} USD")
        return rate
    
    elif from_currency == "USD":
        # Convert from USD to target
        usd_rate = fallback_rates_to_usd.get(to_currency, 1.0)
        rate = 1.0 / usd_rate if usd_rate != 0 else 1.0
        logger.warning(f"⚠️ Using fallback rate: 1 USD = {rate} {to_currency}")
        return rate
    
    else:
        # Convert from_currency → USD → to_currency
        from_to_usd = fallback_rates_to_usd.get(from_currency, 1.0)
        usd_to_target = 1.0 / fallback_rates_to_usd.get(to_currency, 1.0)
        rate = from_to_usd * usd_to_target
        logger.warning(f"⚠️ Using fallback rate: 1 {from_currency} = {rate} {to_currency}")
        return rate


def convert_to_usd(amount: float, from_currency: str) -> Tuple[float, float]:
    """
    Convert amount from any currency to USD (base currency).
    
    Args:
        amount: Amount in original currency
        from_currency: Currency code (e.g., "INR", "GBP")
    
    Returns:
        Tuple of (amount_in_usd, exchange_rate_used)
    
    Example:
        >>> convert_to_usd(150, "INR")
        (1.80, 0.012)
        # 150 INR = 1.80 USD at rate 0.012
    """
    if from_currency == "USD":
        return (amount, 1.0)
    
    # Get current exchange rate
    rate = get_exchange_rate(from_currency, "USD")
    
    # Convert
    amount_usd = amount * rate
    
    # Round to 2 decimal places (cents)
    amount_usd = round(amount_usd, 2)
    
    logger.info(f"💱 Converted {amount} {from_currency} → ${amount_usd} USD (rate: {rate})")
    
    return (amount_usd, rate)


def convert_from_usd(amount_usd: float, to_currency: str) -> float:
    """
    Convert amount from USD to another currency (for display).
    
    Args:
        amount_usd: Amount in USD
        to_currency: Target currency code
    
    Returns:
        Amount in target currency
    
    Example:
        >>> convert_from_usd(1.80, "INR")
        150.0
        # $1.80 USD = 150 INR
    """
    if to_currency == "USD":
        return amount_usd
    
    # Get rate from USD to target currency
    rate = get_exchange_rate("USD", to_currency)
    
    # Convert
    amount_target = amount_usd * rate
    
    # Round to 2 decimal places
    amount_target = round(amount_target, 2)
    
    logger.info(f"💱 Converted ${amount_usd} USD → {amount_target} {to_currency} (rate: {rate})")
    
    return amount_target


def get_all_rates_for_currency(base_currency: str) -> dict:
    """
    Get exchange rates from base currency to all other currencies.
    Useful for displaying converted amounts in multiple currencies.
    
    Args:
        base_currency: Base currency code
    
    Returns:
        Dictionary of {currency_code: rate}
    
    Example:
        >>> get_all_rates_for_currency("USD")
        {"INR": 83.33, "GBP": 0.79, "EUR": 0.92, ...}
    """
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return data["rates"]
        
    except Exception as e:
        logger.error(f"Failed to get all rates: {e}")
        return {}


def format_amount_with_symbol(amount: float, currency_code: str) -> str:
    """
    Format amount with currency symbol.
    
    Args:
        amount: Amount to format
        currency_code: Currency code
    
    Returns:
        Formatted string with symbol
    
    Example:
        >>> format_amount_with_symbol(150, "INR")
        "₹150.00"
        >>> format_amount_with_symbol(20, "USD")
        "$20.00"
    """
    from src.expense_server.database.models import CURRENCY_SYMBOLS
    
    symbol = CURRENCY_SYMBOLS.get(currency_code.upper(), currency_code)
    return f"{symbol}{amount:.2f}"


def clear_cache():
    """
    Clear the exchange rate cache.
    Useful for testing or manual refresh.
    """
    global _rate_cache
    _rate_cache = {}
    logger.info("🗑️ Exchange rate cache cleared")


def get_cache_info() -> dict:
    """
    Get information about cached exchange rates.
    Useful for debugging and monitoring.
    
    Returns:
        Dictionary with cache statistics
    """
    now = datetime.now()
    cache_info = {
        "total_cached": len(_rate_cache),
        "rates": {}
    }
    
    for key, data in _rate_cache.items():
        age = now - data["timestamp"]
        cache_info["rates"][key] = {
            "rate": data["rate"],
            "age_hours": age.total_seconds() / 3600,
            "expires_in_hours": CACHE_DURATION_HOURS - (age.total_seconds() / 3600)
        }
    
    return cache_info