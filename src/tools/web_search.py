import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import serpapi
from loguru import logger
from urllib.parse import urlparse
from trafilatura.settings import use_config
from trafilatura import extract, fetch_url

load_dotenv()

class WebSearchError(Exception):
    """Exception for web search errors."""
    pass

def url_is_accepted(
    url: str, 
    accepted_list: Optional[List[str]] = None, 
    rejected_list: Optional[List[str]] = None
) -> bool:
    """Check if the URL is accepted."""
    domain = urlparse(url).netloc
    
    if accepted_list:
        return domain in accepted_list
        
    if rejected_list and domain in rejected_list:
        return False
        
    return True

def content_is_relevant(content: str = "") -> bool:
    """Check if the content is relevant."""
    return not (content is None or len(str(content)) < 100 or len(content.split()) < 10)

def get_urls_from_google_search(
    query: str,
    num: int = 10,
    tbs: str = "qdr:m",  # Past month for current trends
    accepted_urls: Optional[List[str]] = None,
    rejected_urls: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Perform Google search using SerpApi."""
    
    logger.info(f"Searching Google for: {query}")
    
    try:
        search_params = {
            "q": query,
            "num": num,
            "tbs": tbs,
            "safe": "off",
            "api_key": os.getenv("SERP_API_KEY")
        }
        
        search = serpapi.search(search_params)
        results = search.as_dict()
        
        search_status = results.get("search_metadata", {}).get("status", "Error")
        
        articles = []
        if results.get("organic_results"):
            for result in results["organic_results"]:
                url = result.get("link")
                if url and url_is_accepted(url, accepted_urls, rejected_urls):
                    articles.append({
                        "title": result.get("title", "No Title"),
                        "url": url,
                        "date": result.get("date", "No Date"),
                        "snippet": result.get("snippet", "No Snippet"),
                        "source": result.get("source", "Unknown Source"),
                    })
        
        logger.info(f"Found {len(articles)} relevant articles")
        return {
            "status": search_status,
            "articles": articles
        }
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise WebSearchError(f"Google search failed: {str(e)}")

def extract_content_from_url(url: str) -> Optional[str]:
    """Extract content from URL using Trafilatura."""
    
    try:
        # Configure Trafilatura
        config = use_config()
        config.set("DEFAULT", "user-agent", 
                  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36")
        
        # Fetch URL
        downloaded = fetch_url(url, config=config, no_ssl=True)
        if not downloaded:
            logger.warning(f"Could not download: {url}")
            return None
            
        # Extract content
        content = extract(downloaded, favor_precision=True)
        
        if content and content_is_relevant(content):
            logger.info(f"Extracted content from: {url}")
            return content
        else:
            logger.warning(f"Irrelevant content from: {url}")
            return None
            
    except Exception as e:
        logger.error(f"Content extraction failed for {url}: {str(e)}")
        return None

def web_search_tool(query: str, num_results: int = 3) -> List[Dict[str, Any]]:
    """
    Main web search function for agent use.
    
    Args:
        query: Search query string
        num_results: Number of results to return
        
    Returns:
        List of result objects with all metadata and content
    """
    
    try:
        search_results = get_urls_from_google_search(query, num=num_results)
        
        if search_results["status"] != "Success":
            return []
            
        if not search_results["articles"]:
            return []
        
        processed_results = []
        
        for article in search_results["articles"]:
            content = extract_content_from_url(article["url"])
            
            # Create result object with full metadata
            result = {
                "title": article['title'],
                "url": article['url'],
                "source": article['source'],
                "date": article['date'],
                "content": content or article['snippet'],
                "is_snippet": content is None
            }
            processed_results.append(result)
        
        return processed_results
        
    except WebSearchError as e:
        logger.error(f"Web search error: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in web_search_tool: {str(e)}")
        return []