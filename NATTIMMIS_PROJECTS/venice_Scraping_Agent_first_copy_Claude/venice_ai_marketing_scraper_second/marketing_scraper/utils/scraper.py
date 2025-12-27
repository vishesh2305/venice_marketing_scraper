"""
Web Scraping Utilities
Async scraping with rate limiting and anti-detection
"""

import asyncio
import aiohttp
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import re
from bs4 import BeautifulSoup
import json


@dataclass
class ScrapeConfig:
    """Configuration for scraping"""
    delay_min: float = 1.0
    delay_max: float = 3.0
    max_concurrent: int = 5
    timeout: int = 30
    max_retries: int = 3
    respect_robots: bool = True


class UserAgentRotator:
    """Rotates user agents to avoid detection"""
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ]
    
    def __init__(self):
        self.index = 0
        
    def get(self) -> str:
        agent = self.USER_AGENTS[self.index % len(self.USER_AGENTS)]
        self.index += 1
        return agent


class AsyncWebScraper:
    """
    Async web scraper with rate limiting and anti-detection
    """
    
    def __init__(self, config: Optional[ScrapeConfig] = None):
        self.config = config or ScrapeConfig()
        self.ua_rotator = UserAgentRotator()
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore: Optional[asyncio.Semaphore] = None
        
    async def __aenter__(self):
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent)
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    def _get_headers(self) -> Dict[str, str]:
        """Generate random headers"""
        return {
            "User-Agent": self.ua_rotator.get(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }
        
    async def _random_delay(self):
        """Apply random delay between requests"""
        delay = random.uniform(self.config.delay_min, self.config.delay_max)
        await asyncio.sleep(delay)
        
    async def fetch(self, url: str, retries: int = 0) -> Dict[str, Any]:
        """
        Fetch a single URL with retry logic
        """
        async with self.semaphore:
            await self._random_delay()
            
            try:
                async with self.session.get(url, headers=self._get_headers()) as response:
                    if response.status == 200:
                        html = await response.text()
                        return {
                            "success": True,
                            "url": url,
                            "status": response.status,
                            "html": html,
                            "timestamp": datetime.now().isoformat()
                        }
                    elif response.status == 429:  # Rate limited
                        if retries < self.config.max_retries:
                            await asyncio.sleep(5 * (retries + 1))
                            return await self.fetch(url, retries + 1)
                    
                    return {
                        "success": False,
                        "url": url,
                        "status": response.status,
                        "error": f"HTTP {response.status}"
                    }
                    
            except asyncio.TimeoutError:
                return {"success": False, "url": url, "error": "Timeout"}
            except Exception as e:
                if retries < self.config.max_retries:
                    await asyncio.sleep(2)
                    return await self.fetch(url, retries + 1)
                return {"success": False, "url": url, "error": str(e)}
                
    async def fetch_many(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Fetch multiple URLs concurrently"""
        tasks = [self.fetch(url) for url in urls]
        return await asyncio.gather(*tasks)


class ProfileExtractor:
    """
    Extracts profile data from HTML using selectors
    """
    
    def __init__(self):
        self.email_pattern = re.compile(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        )
        self.phone_pattern = re.compile(
            r'[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}'
        )
        self.linkedin_pattern = re.compile(
            r'https?://(?:www\.)?linkedin\.com/in/[\w-]+'
        )
        
    def extract(self, html: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract profile data using CSS/XPath selectors
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        profile = {}
        
        for field, selector in selectors.items():
            if selector.startswith("css:"):
                css_sel = selector[4:]
                element = soup.select_one(css_sel)
                if element:
                    profile[field] = element.get_text(strip=True)
            elif selector.startswith("xpath:"):
                # BeautifulSoup doesn't support XPath natively
                # Would need lxml for xpath support
                profile[field] = None
            else:
                # Default: try as CSS selector
                element = soup.select_one(selector)
                if element:
                    profile[field] = element.get_text(strip=True)
                    
        # Auto-extract common patterns
        text = soup.get_text()
        
        if "email" not in profile or not profile.get("email"):
            emails = self.email_pattern.findall(text)
            if emails:
                profile["email"] = emails[0]
                
        if "phone" not in profile or not profile.get("phone"):
            phones = self.phone_pattern.findall(text)
            if phones:
                profile["phone"] = phones[0]
                
        if "linkedin" not in profile or not profile.get("linkedin"):
            linkedins = self.linkedin_pattern.findall(str(soup))
            if linkedins:
                profile["linkedin"] = linkedins[0]
                
        return profile
    
    def extract_many(self, results: List[Dict], selectors: Dict[str, str]) -> List[Dict]:
        """Extract profiles from multiple scraped pages"""
        profiles = []
        
        for result in results:
            if result.get("success") and result.get("html"):
                profile = self.extract(result["html"], selectors)
                profile["source_url"] = result["url"]
                profile["scraped_at"] = result.get("timestamp")
                profiles.append(profile)
                
        return profiles


class SearchQueryBuilder:
    """
    Builds optimized search queries for different platforms
    """
    
    PLATFORM_TEMPLATES = {
        "linkedin": {
            "profile": 'site:linkedin.com/in "{keyword}" "{title}"',
            "company": 'site:linkedin.com/company "{company}"',
            "people": 'site:linkedin.com/in "{keyword}" {location}'
        },
        "twitter": {
            "profile": 'site:twitter.com "{keyword}" "{title}"',
            "bio": 'site:twitter.com "{keyword}" bio'
        },
        "github": {
            "profile": 'site:github.com "{keyword}" "{skill}"',
            "repos": 'site:github.com "{keyword}" repositories'
        },
        "generic": {
            "profile": '"{keyword}" "{title}" email contact',
            "company": '"{company}" team about contact'
        }
    }
    
    def __init__(self):
        pass
        
    def build_queries(
        self,
        keywords: Dict[str, List[str]],
        platform: str = "generic",
        max_queries: int = 20
    ) -> List[str]:
        """
        Build search queries from keywords
        """
        templates = self.PLATFORM_TEMPLATES.get(platform, self.PLATFORM_TEMPLATES["generic"])
        queries = []
        
        primary = keywords.get("primary_keywords", [])
        titles = keywords.get("job_titles", [])
        companies = keywords.get("company_types", [])
        locations = keywords.get("geographic_hints", [])
        
        # Profile searches
        profile_template = templates.get("profile", '"{keyword}"')
        for kw in primary[:5]:
            for title in titles[:5]:
                query = profile_template.format(
                    keyword=kw,
                    title=title,
                    location=locations[0] if locations else ""
                )
                queries.append(query)
                if len(queries) >= max_queries:
                    return queries
                    
        # Company searches
        company_template = templates.get("company", '"{company}"')
        for company in companies[:5]:
            query = company_template.format(company=company)
            queries.append(query)
            if len(queries) >= max_queries:
                return queries
                
        return queries


def run_async_scrape(urls: List[str], config: Optional[ScrapeConfig] = None) -> List[Dict]:
    """
    Synchronous wrapper for async scraping
    """
    async def _scrape():
        async with AsyncWebScraper(config) as scraper:
            return await scraper.fetch_many(urls)
            
    return asyncio.run(_scrape())
