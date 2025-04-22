import requests
from bs4 import BeautifulSoup
import json
import webbrowser
import re
from urllib.parse import quote_plus
import time
import traceback

def aliexpress_search(query):
    """
    Search AliExpress for products matching the query and return structured data
    """
    print(f"Searching AliExpress for: {query}")
    start_time = time.time()
    
    try:
        # Format query for URL
        formatted_query = quote_plus(query)
        
        # AliExpress search URL
        search_url = f"https://www.aliexpress.com/wholesale?SearchText={formatted_query}"
        
        # Set user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
        }
        
        # Open the search URL in browser first (this will happen regardless of other failures)
        webbrowser.open(search_url)
        print(f"Opening AliExpress search URL: {search_url}")
        
        # Create a default result in case all else fails
        default_result = basic_result(query, search_url)
        
        # Add a timeout to ensure the function doesn't hang indefinitely
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"Search request failed with status code: {response.status_code}")
            return default_result
        
        # Check if we got some content
        if len(response.text) < 1000:
            print("Response too small, possibly blocked. Using default result.")
            return default_result
            
        # Try to extract product data
        products_data = extract_products_from_html(response.text, query, search_url)
        
        # If we got products, return them
        if products_data and len(products_data.get('products', [])) > 0:
            print(f"Successfully extracted {len(products_data['products'])} products")
            elapsed = time.time() - start_time
            print(f"Search completed in {elapsed:.2f} seconds")
            return products_data
        
        # If no products, return basic info
        print("No products found, using default result")
        return default_result
            
    except requests.exceptions.Timeout:
        print("Request timed out")
        return basic_result(query, f"https://www.aliexpress.com/wholesale?SearchText={quote_plus(query)}")
        
    except Exception as e:
        print(f"AliExpress search error: {e}")
        print(traceback.format_exc())  # Print full traceback for debugging
        return basic_result(query, f"https://www.aliexpress.com/wholesale?SearchText={quote_plus(query)}")
    finally:
        elapsed = time.time() - start_time
        print(f"Total search time: {elapsed:.2f} seconds")

def extract_products_from_html(html_content, query, search_url):
    """Extract product information from HTML content"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check for captcha or anti-bot measures
        if "verify" in html_content.lower() or "captcha" in html_content.lower():
            print("Detected verification page. Using default result.")
            return basic_result(query, search_url)
        
        # Try to find product data in JSON format
        json_data = extract_json_data(soup)
        if json_data:
            return json_data
            
        # If no JSON data, try direct HTML parsing
        html_data = extract_html_data(soup, query, search_url)
        if html_data:
            return html_data
            
        return basic_result(query, search_url)
        
    except Exception as e:
        print(f"Error extracting product data: {e}")
        print(traceback.format_exc())
        return basic_result(query, search_url)

def extract_json_data(soup):
    """Try to extract product data from embedded JSON"""
    try:
        script_tags = soup.find_all('script')
        
        for script in script_tags:
            if not script.string:
                continue
                
            # Look for different JSON data patterns
            patterns = [
                r'window\.runParams\s*=\s*({.*?});',
                r'data\s*=\s*({.*?});',
                r'window\.__AER_DATA__\s*=\s*({.*?});',
                r'window\.__INIT_DATA__\s*=\s*({.*?});'
            ]
            
            for pattern in patterns:
                try:
                    json_match = re.search(pattern, script.string, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                        data = json.loads(json_str)
                        
                        # Check different possible paths to product data
                        if 'items' in data:
                            return process_json_items(data['items'])
                        elif 'data' in data and 'items' in data['data']:
                            return process_json_items(data['data']['items'])
                        elif 'mods' in data and 'itemList' in data['mods']:
                            return process_json_items(data['mods']['itemList']['content'])
                except Exception as e:
                    print(f"Error parsing specific JSON pattern: {e}")
                    continue
        
        return None
        
    except Exception as e:
        print(f"JSON extraction error: {e}")
        return None

def process_json_items(items):
    """Process JSON items into a consistent format"""
    if not items or not isinstance(items, list):
        return None
        
    products_info = []
    for item in items[:5]:  # Limit to 5 products
        try:
            # Handle different JSON structures
            title = item.get('title', item.get('name', item.get('productTitle', 'Unknown Product')))
            price = item.get('price', item.get('formatedPrice', item.get('minPrice', 'Price not available')))
            
            img_url = ''
            for img_key in ['imageUrl', 'image', 'imgUrl', 'imageUrl', 'mainImageUrl']:
                if img_key in item and item[img_key]:
                    img_url = item[img_key]
                    break
            
            product_url = ''
            for url_key in ['productDetailUrl', 'productUrl', 'detailUrl', 'itemDetailUrl']:
                if url_key in item and item[url_key]:
                    product_url = item[url_key]
                    break
            
            if product_url and not product_url.startswith('http'):
                if product_url.startswith('//'):
                    product_url = f"https:{product_url}"
                elif product_url.startswith('/'):
                    product_url = f"https://www.aliexpress.com{product_url}"
            
            products_info.append({
                'title': str(title),
                'price': str(price),
                'image': str(img_url),
                'url': str(product_url)
            })
        except Exception as e:
            print(f"Error processing JSON item: {e}")
            continue
    
    if products_info:
        return {
            'query': str(items[0].get('query', 'Unknown query')),
            'url_content': str(items[0].get('searchUrl', 'https://www.aliexpress.com')),
            'products': products_info
        }
    return None

def extract_html_data(soup, query, search_url):
    """Extract product information from HTML if JSON extraction fails"""
    try:
        # Try various selectors to find product cards
        selectors = [
            '.list--gallery--34TropR', 
            '.product-card', 
            '.product', 
            '.list-item', 
            '[data-product-id]',
            '.JIIxO',  # Modern AliExpress card class
            '.cards--gallery--2o6yJVt'  # Another card container class
        ]
        
        product_cards = []
        for selector in selectors:
            cards = soup.select(selector)
            if cards and len(cards) > 0:
                product_cards = cards
                print(f"Found {len(cards)} product cards with selector '{selector}'")
                break
        
        # If no main containers found, try to find individual items
        if not product_cards:
            print("No product cards found with main selectors, trying fallback selectors")
            # Try to find any elements with product info
            all_links = soup.find_all('a', href=True)
            product_links = [link for link in all_links if 'item/' in link.get('href', '')]
            
            if product_links:
                print(f"Found {len(product_links)} product links as fallback")
                # Use these links to build basic product data
                products_info = []
                for i, link in enumerate(product_links[:5]):
                    if i >= 5:
                        break
                    
                    title = link.text.strip() if link.text and len(link.text.strip()) > 0 else "Product " + str(i+1)
                    href = link.get('href')
                    
                    # Ensure we have full URLs
                    if href.startswith('//'):
                        product_url = f"https:{href}"
                    elif href.startswith('/'):
                        product_url = f"https://www.aliexpress.com{href}"
                    else:
                        product_url = href
                    
                    # Try to find an image near the link
                    img = link.find('img') or link.find_parent().find('img')
                    img_url = img.get('src', '') if img else ''
                    
                    products_info.append({
                        'title': title[:100],
                        'price': "Check website",
                        'image': img_url,
                        'url': product_url
                    })
                
                return {
                    'query': query,
                    'url_content': search_url,
                    'products': products_info
                }
            
            # If still nothing found, return basic result
            print("No product links found either, returning basic result")
            return basic_result(query, search_url)
                
        # Extract basic information from the found product cards
        products_info = []
        for i, card in enumerate(product_cards[:5]):
            if i >= 5:
                break
                
            try:
                # Handle different possible structures
                title_elem = None
                for title_selector in ['h1', 'h2', 'h3', '.product-title', '.title', '[data-title]', '.awV9E']:
                    title_elem = card.select_one(title_selector)
                    if title_elem and title_elem.text.strip():
                        break
                
                price_elem = None
                for price_selector in ['.product-price', '.price', '[data-price]', '.mGXnE', '.pxGQs']:
                    price_elem = card.select_one(price_selector)
                    if price_elem and price_elem.text.strip():
                        break
                
                img_elem = card.select_one('img')
                link_elem = card.select_one('a[href]')
                
                title = title_elem.text.strip() if title_elem else "Product " + str(i+1)
                price = price_elem.text.strip() if price_elem else "Price not available"
                
                img_url = ''
                if img_elem:
                    for attr in ['src', 'data-src', 'data-lazy-src']:
                        if img_elem.get(attr):
                            img_url = img_elem.get(attr)
                            break
                
                product_url = ""
                if link_elem and link_elem.get('href'):
                    href = link_elem.get('href')
                    if href.startswith('//'):
                        product_url = f"https:{href}"
                    elif href.startswith('/'):
                        product_url = f"https://www.aliexpress.com{href}"
                    else:
                        product_url = href
                
                products_info.append({
                    'title': title[:100],  # Limit title length
                    'price': price,
                    'image': img_url,
                    'url': product_url
                })
            except Exception as e:
                print(f"Error processing card {i}: {e}")
                continue
        
        if products_info:
            return {
                'query': query,
                'url_content': search_url,
                'products': products_info
            }
        else:
            return basic_result(query, search_url)
            
    except Exception as e:
        print(f"HTML extraction error: {e}")
        print(traceback.format_exc())
        return basic_result(query, search_url)

def basic_result(query, url):
    """Create a basic result when detailed extraction fails"""
    return {
        'query': str(query),
        'url_content': str(url),
        'products': [
            {
                'title': f"Search results for {query}",
                'price': "See website for prices",
                'image': "",
                # 'open_url': url,
                'url': url
            }
        ]
    }

