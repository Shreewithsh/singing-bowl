"""
Singing Bowl Export Desk
Web Scraper Service - Extracts business contact info from websites
"""
import logging
import random
import re
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from services.utils import (
    validate_email, clean_text, extract_emails_from_text,
    extract_phones_from_text, calculate_score, get_country_from_text,
    country_from_tld
)

logger = logging.getLogger(__name__)

HEADERS_POOL = [
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    },
    {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.5',
    },
    {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.3',
    }
]


def scrape_website(url: str, source_url: str = '', hint_countries: list = None) -> Optional[Dict]:
    """
    Scrape a website for business contact information.
    Returns a dict with extracted data or None if failed.
    """
    try:
        headers = random.choice(HEADERS_POOL)
        session = requests.Session()
        session.headers.update(headers)

        # Try main page first
        response = session.get(url, timeout=10, allow_redirects=True)
        if response.status_code != 200:
            logger.warning(f"HTTP {response.status_code} for {url}")
            return None

        soup = BeautifulSoup(response.content, 'lxml')
        text_content = soup.get_text(separator=' ', strip=True)

        # Extract basic info from main page
        data = _extract_from_page(soup, text_content, url, source_url, hint_countries)

        # If no email found, try contact page
        if not data.get('email'):
            contact_url = _find_contact_page(soup, url)
            if contact_url:
                try:
                    contact_resp = session.get(contact_url, timeout=8)
                    if contact_resp.status_code == 200:
                        contact_soup = BeautifulSoup(contact_resp.content, 'lxml')
                        contact_text = contact_soup.get_text(separator=' ', strip=True)
                        contact_data = _extract_from_page(contact_soup, contact_text, url, source_url, hint_countries)
                        if contact_data.get('email'):
                            data['email'] = contact_data['email']
                        if not data.get('phone') and contact_data.get('phone'):
                            data['phone'] = contact_data['phone']
                        if not data.get('owner_name') and contact_data.get('owner_name'):
                            data['owner_name'] = contact_data['owner_name']
                except Exception as e:
                    logger.debug(f"Contact page error for {url}: {e}")

        if not data.get('email'):
            return None

        # Calculate score
        data['score'] = calculate_score(data)
        return data

    except requests.exceptions.Timeout:
        logger.warning(f"Timeout scraping {url}")
        return None
    except requests.exceptions.ConnectionError:
        logger.warning(f"Connection error scraping {url}")
        return None
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return None


def _extract_from_page(soup: BeautifulSoup, text: str, url: str, source_url: str, hint_countries: list) -> Dict:
    """Extract structured data from a parsed page."""
    data = {
        'business_name': '',
        'owner_name': '',
        'email': '',
        'phone': '',
        'country': '',
        'website': url,
        'source_url': source_url
    }

    # Extract business name
    data['business_name'] = _extract_business_name(soup)

    # Extract owner name
    data['owner_name'] = _extract_owner_name(soup, text)

    # Extract emails
    emails = extract_emails_from_text(text)
    # Also check mailto links
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('mailto:'):
            email = href[7:].split('?')[0].strip()
            if validate_email(email):
                emails.insert(0, email)

    if emails:
        # Prefer business email (non-free providers for first)
        free_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com']
        business_emails = [e for e in emails if not any(d in e.lower() for d in free_domains)]
        data['email'] = business_emails[0] if business_emails else emails[0]

    # Extract phones
    phones = extract_phones_from_text(text)
    if phones:
        data['phone'] = phones[0]

    # Extract country
    country = country_from_tld(url)
    if not country:
        country = get_country_from_text(text, hint_countries)
    data['country'] = country

    # Look for structured data (Schema.org)
    _enhance_from_schema(soup, data)

    # Clean all text fields
    for key in ['business_name', 'owner_name', 'phone', 'country']:
        data[key] = clean_text(data[key])

    return data


def _extract_business_name(soup: BeautifulSoup) -> str:
    """Extract business name from page."""
    # Try og:site_name
    og = soup.find('meta', property='og:site_name')
    if og and og.get('content'):
        return og['content'].strip()[:255]

    # Try title tag
    title = soup.find('title')
    if title and title.text:
        name = title.text.strip().split('|')[0].split('-')[0].strip()
        if name and len(name) < 100:
            return name

    # Try h1
    h1 = soup.find('h1')
    if h1 and h1.text.strip():
        return h1.text.strip()[:255]

    return ''


def _extract_owner_name(soup: BeautifulSoup, text: str) -> str:
    """Try to extract owner/contact person name."""
    # Look for "About" section patterns
    about_patterns = [
        r'(?:My name is|I am|I\'m|Founded by|Owner:|CEO:|Director:|Contact:|From|Hi,? I\'m)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})',
        r'(?:About|Team|Our Story)[^.]*?([A-Z][a-z]+\s+[A-Z][a-z]+)',
    ]
    for pattern in about_patterns:
        match = re.search(pattern, text)
        if match:
            name = match.group(1).strip()
            if 3 < len(name) < 60:
                return name

    # Check meta author
    author = soup.find('meta', {'name': 'author'})
    if author and author.get('content'):
        content = author['content'].strip()
        if content and len(content) < 60 and not any(
            w in content.lower() for w in ['wordpress', 'drupal', 'joomla', 'wix', 'squarespace']
        ):
            return content

    return ''


def _find_contact_page(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    """Find the contact page URL."""
    contact_keywords = ['contact', 'contact-us', 'about', 'get-in-touch', 'reach-us', 'kontakt']
    for a in soup.find_all('a', href=True):
        href = a['href'].lower()
        text = a.get_text().lower().strip()
        if any(k in href or k in text for k in contact_keywords):
            full_url = urljoin(base_url, a['href'])
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                return full_url
    return None


def _enhance_from_schema(soup: BeautifulSoup, data: Dict):
    """Enhance data from Schema.org JSON-LD."""
    import json
    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        try:
            schema = json.loads(script.string or '{}')
            if isinstance(schema, list):
                schema = schema[0] if schema else {}

            if not data['business_name'] and schema.get('name'):
                data['business_name'] = str(schema['name'])[:255]

            if not data['email']:
                email = schema.get('email', '')
                if email and validate_email(email):
                    data['email'] = email

            if not data['phone']:
                phone = schema.get('telephone', '')
                if phone:
                    data['phone'] = str(phone)[:100]

            if not data['country']:
                address = schema.get('address', {})
                if isinstance(address, dict):
                    country = address.get('addressCountry', '') or address.get('addressRegion', '')
                    if country:
                        data['country'] = str(country)[:100]
        except Exception:
            continue


def scrape_from_search_results(search_results: List[Dict], hint_countries: list = None,
                                 progress_callback=None) -> List[Dict]:
    """
    Scrape all websites from search results.
    Calls progress_callback(current, total, message) if provided.
    """
    extracted_leads = []
    total = len(search_results)

    for i, result in enumerate(search_results):
        url = result.get('url', '')
        metadata = result.get('metadata', {})

        if progress_callback:
            progress_callback(i + 1, total, f"Scraping {url[:50]}...")

        # If we have pre-loaded metadata (simulated), use it directly
        if metadata and metadata.get('email'):
            lead = {
                'business_name': metadata.get('business_name', ''),
                'owner_name': metadata.get('owner_name', ''),
                'email': metadata.get('email', ''),
                'phone': metadata.get('phone', ''),
                'country': metadata.get('country', ''),
                'website': metadata.get('website', url),
                'source_url': metadata.get('source_url', url),
                'score': 0
            }
            lead['score'] = calculate_score(lead)
            extracted_leads.append(lead)
        else:
            # Try real scraping for seed URLs
            if url:
                scraped = scrape_website(url, source_url=url, hint_countries=hint_countries)
                if scraped:
                    extracted_leads.append(scraped)
                time.sleep(random.uniform(0.5, 1.5))  # Polite delay

        # Small delay between results
        time.sleep(0.1)

    logger.info(f"Extracted {len(extracted_leads)} leads from {total} websites")
    return extracted_leads
