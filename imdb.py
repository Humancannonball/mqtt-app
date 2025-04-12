from selenium import webdriver
import os
import time
import json
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import requests
from bs4 import BeautifulSoup
import re
import webbrowser

# Setup Chrome WebDriver with modern approach
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36')
chrome_options.add_argument('--window-size=1920,1080')  # Larger window to avoid click interception
chrome_options.add_argument('--disable-popup-blocking')
chrome_options.add_argument('--disable-notifications')

# Initialize the driver
try:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
except Exception as e:
    print(f"Failed to initialize Chrome driver: {e}")
    # Fallback to direct path if available
    try:
        chromedriver = "./chromedriver"
        os.environ["webdriver.chrome.driver"] = chromedriver
        driver = webdriver.Chrome(service=Service(chromedriver), options=chrome_options)
    except Exception as e2:
        print(f"Fallback also failed: {e2}")
        raise

def join_content(jc):
    if isinstance(jc, list):
        return ','.join(jc)
    return str(jc)

def iterate_actors(iter_actors):
    if not isinstance(iter_actors, list):
        return str(iter_actors)
    m = []
    for item in iter_actors:
        if isinstance(item, dict) and 'name' in item:
            m.append(item['name'])
    return ','.join(m)

def prepare_content(json_content, url_content=""):
    """Prepare movie data for response"""
    d = {}
    d['image'] = json_content.get('image', '')
    d['name'] = json_content.get('name', '')
    d['url_content'] = url_content or json_content.get('url', '')
    d['genre'] = join_content(json_content.get('genre', []))
    d['actors'] = iterate_actors(json_content.get('actor', []))
    d['description'] = json_content.get('description', '')
    
    # Handle trailer data
    if 'trailer' in json_content and isinstance(json_content['trailer'], dict) and 'embedUrl' in json_content['trailer']:
        d['trailer'] = json_content['trailer']['embedUrl']
    else:
        d['trailer'] = ''
        
    return d

def fallback_search_with_requests(query):
    """
    Fallback method using requests and BeautifulSoup
    This is now the primary method since it's more reliable
    """
    print("Using requests-based search method")
    
    # Format query for URL
    formatted_query = query.replace(' ', '+')
    
    # Try direct search on IMDB
    search_url = f"https://www.imdb.com/find/?q={formatted_query}&s=tt"
    
    try:
        # Set a user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://www.imdb.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        # Get search results page
        response = requests.get(search_url, headers=headers)
        
        if response.status_code != 200:
            print(f"Search request failed with status code: {response.status_code}")
            return basic_result(query, search_url)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try different result selectors to handle IMDB's layout changes
        selectors = [
            '.findResult .result_text a',                      # Classic layout
            '.ipc-metadata-list-summary-item__t',              # New layout
            'a[href^="/title/"]',                             # Generic title links
            'a.ipc-metadata-list-summary-item__t',            # Another variant
            'li.ipc-metadata-list-summary-item a'             # List items with links
        ]
        
        result_link = None
        for selector in selectors:
            links = soup.select(selector)
            if links:
                # Find a movie/TV show link
                for link in links:
                    href = link.get('href', '')
                    if '/title/' in href:
                        result_link = link
                        break
                if result_link:
                    break
        
        if result_link:
            # Get the movie path
            movie_path = result_link.get('href', '')
            movie_title = result_link.text.strip()
            
            # Ensure path starts with /title/
            if '/title/' in movie_path:
                # Make sure we have a full URL
                movie_url = f"https://www.imdb.com{movie_path}" if movie_path.startswith('/') else movie_path
                
                # Open in browser
                webbrowser.open(movie_url)
                print(f"Opening movie URL: {movie_url}")
                
                # Get the movie page
                movie_response = requests.get(movie_url, headers=headers)
                
                if movie_response.status_code != 200:
                    print(f"Movie page request failed with status code: {movie_response.status_code}")
                    return basic_result(movie_title, movie_url)
                
                movie_soup = BeautifulSoup(movie_response.text, 'html.parser')
                
                # Extract structured data if available
                try:
                    json_ld = None
                    script_tags = movie_soup.find_all('script', {'type': 'application/ld+json'})
                    
                    for script in script_tags:
                        try:
                            data = json.loads(script.string)
                            if '@type' in data and data['@type'] in ['Movie', 'TVSeries', 'TVMovie']:
                                json_ld = data
                                break
                        except:
                            continue
                    
                    if json_ld:
                        # Create result from structured data
                        result = {
                            'name': json_ld.get('name', movie_title),
                            'description': json_ld.get('description', ''),
                            'url_content': movie_url,
                            'image': json_ld.get('image', ''),
                            'genre': ','.join(json_ld.get('genre', [])),
                            'actors': ','.join([actor.get('name', '') for actor in json_ld.get('actor', [])[:5]]),
                            'trailer': json_ld.get('trailer', {}).get('embedUrl', f"{movie_url}/videogallery/")
                        }
                        
                        print(f"Successfully extracted structured data for: {result['name']}")
                        return result
                except Exception as e:
                    print(f"Error extracting structured data: {e}")
                
                # If structured data extraction failed, scrape the page
                try:
                    # Try to get title
                    title = movie_title
                    title_elem = movie_soup.select_one('h1')
                    if title_elem:
                        title = title_elem.text.strip()
                    
                    # Try to get description
                    description = ""
                    desc_selectors = [
                        'span[data-testid="plot-xl"]',
                        '.GenresAndPlot__TextContainerBreakpointXS',
                        '[data-testid="plot"]',
                        '.summary_text'
                    ]
                    
                    for selector in desc_selectors:
                        desc_elem = movie_soup.select_one(selector)
                        if desc_elem:
                            description = desc_elem.text.strip()
                            break
                    
                    # Try to find poster image
                    image_url = ""
                    img_selectors = [
                        'img.ipc-image',
                        '.poster img',
                        '[data-testid="hero-media__poster"] img',
                        '.poster a img'
                    ]
                    
                    for selector in img_selectors:
                        img_elem = movie_soup.select_one(selector)
                        if img_elem and 'src' in img_elem.attrs:
                            image_url = img_elem['src']
                            break
                    
                    # Extract genre
                    genres = []
                    genre_selectors = [
                        'a.GenresAndPlot__GenreChip',
                        'a.ipc-chip--on-baseAlt',
                        'a[href*="/genres/"]'
                    ]
                    
                    for selector in genre_selectors:
                        genre_elems = movie_soup.select(selector)
                        if genre_elems:
                            for genre in genre_elems:
                                if 'genres' in genre.get('href', ''):
                                    genres.append(genre.text.strip())
                            break
                    
                    # Try to find actors
                    actors = []
                    actor_selectors = [
                        'a.sc-bfec09a1-1',
                        'a[data-testid="title-cast-item__actor"]',
                        '.credit_summary_item a[href*="/name/"]'
                    ]
                    
                    for selector in actor_selectors:
                        actor_elems = movie_soup.select(selector)
                        if actor_elems:
                            for actor in actor_elems:
                                if '/name/' in actor.get('href', ''):
                                    actors.append(actor.text.strip())
                            break
                    
                    result = {
                        'name': title,
                        'description': description,
                        'url_content': movie_url,
                        'image': image_url,
                        'genre': ','.join(genres),
                        'actors': ','.join(actors[:5]),  # Limit to first 5 actors
                        'trailer': f"{movie_url}/videogallery/"
                    }
                    
                    print(f"Successfully extracted page data for: {title}")
                    return result
                    
                except Exception as e:
                    print(f"Error extracting page data: {e}")
                    
                # If all extraction fails, return basic info
                return basic_result(movie_title, movie_url)
        
        # If no specific result found, handle general search page
        print("No specific movie result found in search")
        
        # Try to extract any movie title from search results as a last resort
        try:
            titles = soup.select('a[href*="/title/"]')
            if titles:
                for title in titles:
                    href = title.get('href', '')
                    if '/title/' in href and not '/title/tt' in href:
                        continue  # Skip category links
                    
                    movie_url = f"https://www.imdb.com{href}" if href.startswith('/') else href
                    webbrowser.open(movie_url)
                    
                    return basic_result(title.text.strip(), movie_url)
        except Exception as e:
            print(f"Error extracting any movie from search: {e}")
        
        # If all else fails, just open the search page
        webbrowser.open(search_url)
        return basic_result(query, search_url)
        
    except Exception as e:
        print(f"Fallback search error: {e}")
        search_url = f"https://www.imdb.com/find/?q={formatted_query}"
        webbrowser.open(search_url)
        return basic_result(query, search_url)

def basic_result(title, url):
    """Create a basic result when detailed extraction fails"""
    return {
        'name': title,
        'description': f"Search results for {title}",
        'url_content': url,
        'image': '',
        'genre': '',
        'actors': '',
        'trailer': ''
    }

def imdb_search(query):
    """Main function to search IMDB for movie information"""
    print(f"Searching IMDB for: {query}")
    
    # Since the fallback method is more reliable, use it directly
    result = fallback_search_with_requests(query)
    
    print(f"Search complete. Found: {result.get('name', 'No results')}")
    return result




