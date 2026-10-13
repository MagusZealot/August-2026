#!/usr/bin/env python3
"""
Currency Converter Module - Standardizes all amounts to PHP (Philippine Peso)
using historical exchange rates relative to transaction dates.

Data period: August - October 2026
"""

from datetime import datetime
from pathlib import Path
import json
import requests
import time
from functools import lru_cache

CACHE_FILE = Path(__file__).parent / "currency_cache.json"
CACHE_TTL_DAYS = 30

# Base fallback rates (used when API unavailable or for currencies not supported)
BASE_RATES = {
    'CNY': 7.85,      # Chinese Yuan
    'IDR': 0.0033,    # Indonesian Rupiah
    'VND': 0.0021,    # Vietnamese Dong
    'KRW': 0.042,     # South Korean Won
    'JPY': 0.37,      # Japanese Yen
    'THB': 1.65,      # Thai Baht
    'USD': 56.5,      # US Dollar
    'SGD': 42.8,      # Singapore Dollar
    'HKD': 7.25,      # Hong Kong Dollar
    'TWD': 1.78,      # Taiwan Dollar
    'MYR': 12.8,      # Malaysian Ringgit
    'INR': 0.68,      # Indian Rupee
    'MMK': 0.027,     # Myanmar Kyat
    'NPR': 0.43,      # Nepalese Rupee
    'BDT': 0.48,      # Bangladeshi Taka
    'TRY': 1.65,      # Turkish Lira
    'USDT': 56.5,     # Tether (pegged to USD)
    'IDRK': 0.0033,   # Indonesian Rupiah (variant)
    'VNDK': 0.0021,   # Vietnamese Dong (variant)
    'PHP': 1.0,       # Philippine Peso (base)
}

# Currency to Country mapping (consistent with existing code)
CURRENCY_COUNTRY = {
    'CNY': 'China', 'IDR': 'Indonesia', 'VND': 'Vietnam', 'KRW': 'South Korea',
    'JPY': 'Japan', 'THB': 'Thailand', 'USD': 'USA', 'SGD': 'Singapore',
    'HKD': 'Hong Kong', 'TWD': 'Taiwan', 'MYR': 'Malaysia', 'INR': 'India',
    'MMK': 'Myanmar', 'NPR': 'Nepal', 'BDT': 'Bangladesh', 'TRY': 'Turkey',
    'USDT': 'Crypto', 'IDRK': 'Indonesia', 'VNDK': 'Vietnam', 'PHP': 'Philippines'
}

# In-memory cache
_rate_cache = {}
_cache_loaded = False


def _load_cache():
    """Load cached rates from disk."""
    global _rate_cache, _cache_loaded
    if _cache_loaded:
        return
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r') as f:
                data = json.load(f)
                _rate_cache = data.get('rates', {})
        except (json.JSONDecodeError, OSError):
            _rate_cache = {}
    _cache_loaded = True


def _save_cache():
    """Save cached rates to disk."""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump({'rates': _rate_cache, 'updated': time.time()}, f)
    except OSError:
        pass


def _is_cache_valid(timestamp: float) -> bool:
    """Check if cached rate is still valid."""
    return (time.time() - timestamp) < (CACHE_TTL_DAYS * 86400)


def _fetch_rate_from_api(currency: str, date_str: str) -> float | None:
    """
    Fetch historical exchange rate from frankfurter.app API (no API key required).
    Returns rate (1 currency = X PHP) or None if failed.
    """
    try:
        # Extract date portion
        date_part = date_str[:10]  # 'YYYY-MM-DD'
        url = f"https://api.frankfurter.app/{date_part}"
        params = {'from': currency.upper(), 'to': 'PHP'}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if 'rates' in data and 'PHP' in data['rates']:
            return float(data['rates']['PHP'])
    except (requests.RequestException, ValueError, KeyError):
        pass
    return None


@lru_cache(maxsize=10_000)
def _get_rate_final(currency: str, date_part: str = "") -> float:
    """Compute final rate with full caching. date_part should be YYYY-MM-DD."""
    currency = (currency or '').strip().upper()
    if currency == 'PHP':
        return 1.0
    if currency not in BASE_RATES and currency != 'PHP':
        # still allow lookup; fall back later
        pass
    if not date_part:
        return BASE_RATES.get(currency, 1.0)
    cache_key = f"{currency}_{date_part}"
    if cache_key in _rate_cache:
        cached_rate, timestamp = _rate_cache[cache_key]
        if _is_cache_valid(timestamp):
            return cached_rate
    _load_cache()
    if cache_key in _rate_cache:
        cached_rate, timestamp = _rate_cache[cache_key]
        if _is_cache_valid(timestamp):
            return cached_rate
    rate = _fetch_rate_from_api(currency, date_part)
    if rate is not None:
        _rate_cache[cache_key] = (rate, time.time())
        _save_cache()
        return rate
    return BASE_RATES.get(currency, 1.0)


def get_rate(currency: str, date_str: str = None) -> float:
    """
    Get PHP exchange rate for a currency on a specific date.
    """
    currency = (currency or '').strip().upper()
    if currency == 'PHP':
        return 1.0
    if currency not in BASE_RATES:
        # try to get anyway
        pass
    if not date_str:
        return BASE_RATES.get(currency, 1.0)
    try:
        date_part = date_str[:10]
    except Exception:
        return BASE_RATES.get(currency, 1.0)
    return _get_rate_final(currency, date_part)


def convert_to_php(amount: float, currency: str, date_str: str = None) -> float:
    """
    Convert an amount from its currency to PHP.
    
    Args:
        amount: Amount in original currency
        currency: Currency code
        date_str: Transaction date for date-specific rate
    
    Returns:
        Amount in PHP
    """
    if amount == 0:
        return 0.0
    rate = get_rate(currency, date_str)
    return round(amount * rate, 2)


def convert_row_to_php(row: dict, debit_col: str = 'debit_amount', 
                        credit_col: str = 'credit_amount',
                        winlose_col: str = 'winlose_amount',
                        balance_col: str = 'balance',
                        currency_col: str = 'currency',
                        date_col: str = 'formatted_debit_at') -> dict:
    """
    Convert all monetary columns in a CSV row to PHP.
    
    Args:
        row: Dictionary row from CSV DictReader
        debit_col: Column name for debit amount
        credit_col: Column name for credit amount
        winlose_col: Column name for win/lose amount
        balance_col: Column name for balance
        currency_col: Column name for currency
        date_col: Column name for date (used for historical rate)
    
    Returns:
        Modified row with PHP-converted values (original values preserved with _orig suffix)
    """
    currency = row.get(currency_col, '').strip()
    date_str = row.get(date_col, '').strip()
    
    for col in [debit_col, credit_col, winlose_col, balance_col]:
        if col in row and row[col]:
            try:
                orig_val = float(row[col])
                row[f'{col}_php'] = convert_to_php(orig_val, currency, date_str)
                row[f'{col}_orig'] = orig_val
            except (ValueError, TypeError):
                row[f'{col}_php'] = 0.0
                row[f'{col}_orig'] = 0.0
    
    row['currency_php'] = 'PHP'
    return row


def get_country(currency: str) -> str:
    """Get country name from currency code."""
    return CURRENCY_COUNTRY.get(currency.strip().upper(), 'Unknown')


if __name__ == "__main__":
    # Quick test
    print("Currency Converter Test")
    print(f"100 USD on 2026-08-15 = {convert_to_php(100, 'USD', '2026-08-15')} PHP")
    print(f"1000 CNY on 2026-09-01 = {convert_to_php(1000, 'CNY', '2026-09-01')} PHP")
    print(f"1000000 IDR on 2026-10-01 = {convert_to_php(1000000, 'IDR', '2026-10-01')} PHP")
    print(f"50000 VND on 2026-08-20 = {convert_to_php(50000, 'VND', '2026-08-20')} PHP")