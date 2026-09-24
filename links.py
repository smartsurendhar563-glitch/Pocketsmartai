from urllib.parse import quote_plus

PLATFORMS = {
    'home': ['amazon','flipkart','meesho','google'],
    'party': ['amazon','swiggy','zomato','bookmyshow','google','booking'],
    'jewelry': ['amazon','flipkart','tanishq','bluestone','caratlane','meesho','google']
}

def shopping_links(search_terms: str, kind: str):
    q = quote_plus(search_terms)
    links = {}
    for p in PLATFORMS.get(kind, ['google']):
        if p == 'amazon': links[p] = f'https://www.amazon.in/s?k={q}'
        elif p == 'flipkart': links[p] = f'https://www.flipkart.com/search?q={q}'
        elif p == 'meesho': links[p] = f'https://www.meesho.com/search?q={q}'
        elif p == 'google': links[p] = f'https://www.google.com/search?q={q}'
        elif p == 'swiggy': links[p] = f'https://www.swiggy.com/search?query={q}'
        elif p == 'zomato': links[p] = f'https://www.zomato.com/search?q={q}'
        elif p == 'bookmyshow': links[p] = f'https://in.bookmyshow.com/explore/home/chennai'
        elif p == 'booking': links[p] = f'https://www.booking.com/search.html?ss={q}'
        elif p == 'tanishq': links[p] = f'https://www.tanishq.co.in/search?q={q}'
        elif p == 'bluestone': links[p] = f'https://www.bluestone.com/search.html?query={q}'
        elif p == 'caratlane': links[p] = f'https://www.caratlane.com/search?q={q}'
    return links
