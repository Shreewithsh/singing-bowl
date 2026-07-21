"""
Singing Bowl Export Desk
Utility Functions
"""
import re
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def validate_email(email: str) -> bool:
    """Validate email address format."""
    if not email or not isinstance(email, str):
        return False
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email.strip()):
        return False
    # Filter out obvious non-real emails
    skip_domains = [
        'example.com', 'test.com', 'placeholder.com', 'domain.com',
        'email.com', 'yoursite.com', 'sentry.io', 'wixpress.com',
        'wordpress.com', 'squarespace.com'
    ]
    domain = email.split('@')[-1].lower()
    if domain in skip_domains:
        return False
    skip_prefixes = ['noreply', 'no-reply', 'donotreply', 'mailer-daemon', 'postmaster', 'webmaster', 'hostmaster']
    prefix = email.split('@')[0].lower()
    if any(prefix.startswith(p) for p in skip_prefixes):
        return False
    return True


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    if not text:
        return ''
    text = re.sub(r'\s+', ' ', str(text)).strip()
    return text[:500]  # Limit length


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        return domain.lower()
    except Exception:
        return url


def normalize_url(url: str) -> str:
    """Normalize URL for deduplication."""
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        parsed = urlparse(url)
        scheme = parsed.scheme
        netloc = parsed.netloc.lower().replace('www.', '')
        return f"{scheme}://{netloc}"
    except Exception:
        return url


def calculate_score(lead_data: dict) -> int:
    """Calculate a relevance score for a lead."""
    score = 0
    if lead_data.get('email') and validate_email(lead_data['email']):
        score += 30
    if lead_data.get('owner_name') and len(lead_data['owner_name']) > 2:
        score += 20
    if lead_data.get('business_name') and len(lead_data['business_name']) > 2:
        score += 15
    if lead_data.get('phone'):
        score += 15
    if lead_data.get('website'):
        score += 10
    if lead_data.get('country'):
        score += 10
    return min(score, 100)


def extract_emails_from_text(text: str) -> list:
    """Extract all valid email addresses from text."""
    pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, text)
    return [e for e in emails if validate_email(e)]


def extract_phones_from_text(text: str) -> list:
    """Extract phone numbers from text."""
    patterns = [
        r'\+?[\d\s\-\(\)]{10,20}',
        r'(?:tel|phone|ph|mobile|mob)[\s:\-]*[\+\d\s\-\(\)]{8,20}'
    ]
    phones = []
    for pattern in patterns:
        found = re.findall(pattern, text, re.IGNORECASE)
        for p in found:
            clean = re.sub(r'[^\d\+\-\s\(\)]', '', p).strip()
            if len(re.sub(r'\D', '', clean)) >= 7:
                phones.append(clean)
    return list(set(phones))[:1]  # Return at most 1 phone


def country_from_tld(url: str) -> str:
    """Guess country from URL TLD."""
    tld_map = {
        '.uk': 'United Kingdom',
        '.co.uk': 'United Kingdom',
        '.us': 'United States',
        '.au': 'Australia',
        '.ca': 'Canada',
        '.de': 'Germany',
        '.fr': 'France',
        '.nl': 'Netherlands',
        '.se': 'Sweden',
        '.no': 'Norway',
        '.dk': 'Denmark',
        '.fi': 'Finland',
        '.it': 'Italy',
        '.es': 'Spain',
        '.jp': 'Japan',
        '.cn': 'China',
        '.in': 'India',
        '.np': 'Nepal',
        '.nz': 'New Zealand',
        '.sg': 'Singapore',
        '.ae': 'UAE',
    }
    url_lower = url.lower()
    for tld, country in tld_map.items():
        if url_lower.endswith(tld) or f'{tld}/' in url_lower:
            return country
    return ''


def get_country_from_text(text: str, hint_countries: list = None) -> str:
    """Try to detect country mentioned in text."""
    country_keywords = {
        'usa': 'United States', 'united states': 'United States', 'u.s.a': 'United States',
        'uk': 'United Kingdom', 'united kingdom': 'United Kingdom', 'england': 'United Kingdom',
        'australia': 'Australia', 'canada': 'Canada', 'germany': 'Germany',
        'france': 'France', 'netherlands': 'Netherlands', 'sweden': 'Sweden',
        'norway': 'Norway', 'denmark': 'Denmark', 'finland': 'Finland',
        'italy': 'Italy', 'spain': 'Spain', 'japan': 'Japan',
        'new zealand': 'New Zealand', 'singapore': 'Singapore'
    }
    text_lower = text.lower()
    for keyword, country in country_keywords.items():
        if keyword in text_lower:
            return country
    if hint_countries:
        return hint_countries[0] if hint_countries else ''
    return ''


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename."""
    return re.sub(r'[^\w\-_\. ]', '_', filename)
