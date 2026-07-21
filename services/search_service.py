"""
Singing Bowl Export Desk
Search Service - Simulates SerpApi search and collects seed URLs
"""
import logging
import random
import time
from typing import List, Dict

logger = logging.getLogger(__name__)

# Simulated business data pool for demonstration
SIMULATED_BUSINESSES = [
    {
        'business_name': 'Harmony Wellness Store',
        'owner_name': 'Sarah Mitchell',
        'email': 'sarah@harmonywellness.com',
        'phone': '+1-555-234-5678',
        'country': 'United States',
        'website': 'https://harmonywellness.com',
        'source_url': 'https://www.google.com/search?q=singing+bowls+wholesale+usa'
    },
    {
        'business_name': 'Zen Garden Imports',
        'owner_name': 'James Thornton',
        'email': 'james@zengardenimports.co.uk',
        'phone': '+44-7700-900123',
        'country': 'United Kingdom',
        'website': 'https://zengardenimports.co.uk',
        'source_url': 'https://www.google.com/search?q=singing+bowls+wholesale+uk'
    },
    {
        'business_name': 'Pacific Wellness Hub',
        'owner_name': 'Emma Wilson',
        'email': 'emma@pacificwellness.com.au',
        'phone': '+61-2-9876-5432',
        'country': 'Australia',
        'website': 'https://pacificwellness.com.au',
        'source_url': 'https://www.google.com/search?q=singing+bowls+wholesale+australia'
    },
    {
        'business_name': 'Nordic Sound Healing',
        'owner_name': 'Lars Eriksson',
        'email': 'lars@nordicsoundhealing.se',
        'phone': '+46-70-123-4567',
        'country': 'Sweden',
        'website': 'https://nordicsoundhealing.se',
        'source_url': 'https://www.google.com/search?q=tibetan+bowls+wholesale+europe'
    },
    {
        'business_name': 'Mindful Imports Canada',
        'owner_name': 'Sophie Tremblay',
        'email': 'sophie@mindfulimports.ca',
        'phone': '+1-514-555-0199',
        'country': 'Canada',
        'website': 'https://mindfulimports.ca',
        'source_url': 'https://www.google.com/search?q=singing+bowls+canada+wholesale'
    },
    {
        'business_name': 'Himalayan Sounds GmbH',
        'owner_name': 'Klaus Weber',
        'email': 'info@himalayan-sounds.de',
        'phone': '+49-30-12345678',
        'country': 'Germany',
        'website': 'https://himalayan-sounds.de',
        'source_url': 'https://www.google.com/search?q=klangschalen+wholesale+germany'
    },
    {
        'business_name': 'Spiritual Arts Gallery',
        'owner_name': 'Maria Santos',
        'email': 'maria@spiritualartsgallery.com',
        'phone': '+1-305-555-7890',
        'country': 'United States',
        'website': 'https://spiritualartsgallery.com',
        'source_url': 'https://www.google.com/search?q=spiritual+wellness+products+wholesale'
    },
    {
        'business_name': 'Lotus Wellness Boutique',
        'owner_name': 'Aroha Williams',
        'email': 'aroha@lotuswellness.co.nz',
        'phone': '+64-9-876-5432',
        'country': 'New Zealand',
        'website': 'https://lotuswellness.co.nz',
        'source_url': 'https://www.google.com/search?q=singing+bowl+new+zealand+supplier'
    },
    {
        'business_name': 'Tranquil Mind Yoga Studio',
        'owner_name': 'Rachel Green',
        'email': 'rachel@tranquilmindyoga.com',
        'phone': '+1-212-555-0147',
        'country': 'United States',
        'website': 'https://tranquilmindyoga.com',
        'source_url': 'https://www.google.com/search?q=yoga+accessories+wholesale+usa'
    },
    {
        'business_name': 'Crystals and Sound Therapy',
        'owner_name': 'David Chen',
        'email': 'david@crystalsound.com',
        'phone': '+1-415-555-3210',
        'country': 'United States',
        'website': 'https://crystalsound.com',
        'source_url': 'https://www.google.com/search?q=sound+therapy+products+wholesale'
    },
    {
        'business_name': 'Amsterdam Wellness Shop',
        'owner_name': 'Jan van der Berg',
        'email': 'jan@amsterdamwellness.nl',
        'phone': '+31-20-123-4567',
        'country': 'Netherlands',
        'website': 'https://amsterdamwellness.nl',
        'source_url': 'https://www.google.com/search?q=singing+bowls+netherlands+wholesale'
    },
    {
        'business_name': 'French Holistic Center',
        'owner_name': 'Isabelle Dupont',
        'email': 'isabelle@holisticfrance.fr',
        'phone': '+33-1-23-45-67-89',
        'country': 'France',
        'website': 'https://holisticfrance.fr',
        'source_url': 'https://www.google.com/search?q=bols+tibetains+grossiste+france'
    },
    {
        'business_name': 'Bodhi Tree Imports',
        'owner_name': 'Michael Anderson',
        'email': 'michael@bodhitreeimports.com',
        'phone': '+1-888-555-0133',
        'country': 'United States',
        'website': 'https://bodhitreeimports.com',
        'source_url': 'https://www.google.com/search?q=buddhist+imports+wholesale+usa'
    },
    {
        'business_name': 'Singapore Wellness Hub',
        'owner_name': 'Mei Lin Tan',
        'email': 'meilin@sgwellnesshub.com.sg',
        'phone': '+65-6234-5678',
        'country': 'Singapore',
        'website': 'https://sgwellnesshub.com.sg',
        'source_url': 'https://www.google.com/search?q=singing+bowls+singapore+supplier'
    },
    {
        'business_name': 'Norwegian Sound Bath',
        'owner_name': 'Ingrid Larsen',
        'email': 'ingrid@soundbath.no',
        'phone': '+47-22-12-34-56',
        'country': 'Norway',
        'website': 'https://soundbath.no',
        'source_url': 'https://www.google.com/search?q=lydbolle+grossist+norge'
    },
    {
        'business_name': 'Celtic Holistic Emporium',
        'owner_name': 'Fiona MacDonald',
        'email': 'fiona@celticholistic.co.uk',
        'phone': '+44-131-555-0178',
        'country': 'United Kingdom',
        'website': 'https://celticholistic.co.uk',
        'source_url': 'https://www.google.com/search?q=tibetan+bowls+scotland+wholesale'
    },
    {
        'business_name': 'Desert Bloom Wellness',
        'owner_name': 'Fatima Al-Hassan',
        'email': 'fatima@desertbloomwellness.ae',
        'phone': '+971-4-555-0192',
        'country': 'UAE',
        'website': 'https://desertbloomwellness.ae',
        'source_url': 'https://www.google.com/search?q=wellness+products+wholesale+dubai'
    },
    {
        'business_name': 'Italian Healing Arts',
        'owner_name': 'Marco Rossi',
        'email': 'marco@italianhealing.it',
        'phone': '+39-02-1234567',
        'country': 'Italy',
        'website': 'https://italianhealing.it',
        'source_url': 'https://www.google.com/search?q=campane+tibetane+ingrosso+italia'
    },
    {
        'business_name': 'Finnish Forest Healing',
        'owner_name': 'Aino Mäkinen',
        'email': 'aino@foresthealing.fi',
        'phone': '+358-9-1234567',
        'country': 'Finland',
        'website': 'https://foresthealing.fi',
        'source_url': 'https://www.google.com/search?q=tiibetilainen+kulho+tukkumyynti'
    },
    {
        'business_name': 'Spanish Yoga & Meditation',
        'owner_name': 'Carmen Rodriguez',
        'email': 'carmen@yogaespana.es',
        'phone': '+34-91-555-0156',
        'country': 'Spain',
        'website': 'https://yogaespana.es',
        'source_url': 'https://www.google.com/search?q=cuencos+tibetanos+distribuidor+espana'
    },
    {
        'business_name': 'The Healing Sound Co.',
        'owner_name': 'Jennifer Adams',
        'email': 'jennifer@healingsoundco.com',
        'phone': '+1-720-555-0143',
        'country': 'United States',
        'website': 'https://healingsoundco.com',
        'source_url': 'https://www.google.com/search?q=sound+healing+business+wholesale'
    },
    {
        'business_name': 'Pure Vibrations Import',
        'owner_name': 'Thomas Brown',
        'email': 'thomas@purevibrationsimport.com',
        'phone': '+1-617-555-0167',
        'country': 'United States',
        'website': 'https://purevibrationsimport.com',
        'source_url': 'https://www.google.com/search?q=vibration+healing+products+wholesale'
    },
    {
        'business_name': 'Kiwi Wellness Imports',
        'owner_name': 'Hemi Walker',
        'email': 'hemi@kiwiwellness.co.nz',
        'phone': '+64-3-555-0188',
        'country': 'New Zealand',
        'website': 'https://kiwiwellness.co.nz',
        'source_url': 'https://www.google.com/search?q=wellness+imports+nz+wholesale'
    },
    {
        'business_name': 'Copenhagen Mindfulness',
        'owner_name': 'Anders Nielsen',
        'email': 'anders@copenhagenmindfull.dk',
        'phone': '+45-33-12-34-56',
        'country': 'Denmark',
        'website': 'https://copenhagenmindfull.dk',
        'source_url': 'https://www.google.com/search?q=tibetanske+klokker+grossist+denmark'
    },
    {
        'business_name': 'Alpine Sound Therapy',
        'owner_name': 'Hans Mueller',
        'email': 'hans@alpinesound.ch',
        'phone': '+41-44-123-4567',
        'country': 'Switzerland',
        'website': 'https://alpinesound.ch',
        'source_url': 'https://www.google.com/search?q=klangschalen+grosshandel+schweiz'
    }
]


def simulate_serpapi_search(keywords: str, countries: list, limit: int, serpapi_key: str = None) -> List[Dict]:
    """
    Simulate SerpApi search results.
    If a real SerpApi key is provided and available, it will attempt real searches.
    Otherwise, returns simulated results with optional filtering.
    """
    results = []
    logger.info(f"Searching for: '{keywords}' in countries: {countries}, limit: {limit}")

    # Filter simulated data based on countries if specified
    pool = SIMULATED_BUSINESSES.copy()

    if countries and countries[0].strip():
        country_list = [c.strip().lower() for c in countries]
        filtered = [b for b in pool if any(
            c in b['country'].lower() for c in country_list
        )]
        if filtered:
            pool = filtered

    # Try real SerpApi if key is provided
    if serpapi_key and serpapi_key.strip() and serpapi_key != 'your-serpapi-key-here':
        try:
            real_results = _real_serpapi_search(keywords, countries, limit, serpapi_key)
            if real_results:
                return real_results[:limit]
        except Exception as e:
            logger.warning(f"Real SerpApi search failed, using simulated: {e}")

    # Return simulated results
    random.shuffle(pool)
    selected = pool[:min(limit, len(pool))]

    # Add some variance to make it feel more like real search results
    for item in selected:
        item = item.copy()
        results.append({
            'url': item['website'],
            'title': item['business_name'],
            'snippet': f"Quality wellness and spiritual products from {item['business_name']}. Wholesale available.",
            'metadata': item
        })

    logger.info(f"Found {len(results)} websites from search simulation")
    return results


def _real_serpapi_search(keywords: str, countries: list, limit: int, api_key: str) -> List[Dict]:
    """Attempt real SerpApi search."""
    import requests
    results = []
    
    for country in countries[:2]:  # Limit to first 2 countries for API calls
        try:
            params = {
                'q': f'{keywords} {country} wholesale supplier contact email',
                'api_key': api_key,
                'num': min(limit, 10),
                'engine': 'google'
            }
            response = requests.get('https://serpapi.com/search', params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                organic = data.get('organic_results', [])
                for r in organic:
                    results.append({
                        'url': r.get('link', ''),
                        'title': r.get('title', ''),
                        'snippet': r.get('snippet', ''),
                        'metadata': {}
                    })
        except Exception as e:
            logger.error(f"SerpApi request error: {e}")

    return results


def get_seed_urls_from_text(seed_urls_text: str) -> List[str]:
    """Parse comma-separated seed URLs."""
    if not seed_urls_text or not seed_urls_text.strip():
        return []
    urls = [url.strip() for url in seed_urls_text.split(',') if url.strip()]
    valid_urls = []
    for url in urls:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        valid_urls.append(url)
    return valid_urls
