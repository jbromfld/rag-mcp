"""Simple document scraper and processor."""

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime
from fnmatch import fnmatch
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup


@dataclass
class ScrapedDocument:
    """Scraped document with metadata."""

    url: str
    title: str
    content: str
    metadata: Dict
    scraped_at: datetime


class DocumentScraper:
    """Simple document scraper for web pages with recursive crawling."""

    def __init__(self, timeout: int = 10, user_agent: str = "RAG-Testing-Bot/1.0"):
        """Initialize scraper.

        Args:
            timeout: Request timeout in seconds
            user_agent: User agent string
        """
        self.timeout = timeout
        self.user_agent = user_agent
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": self.user_agent},
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            )
        return self.session

    async def scrape_url(self, url: str) -> ScrapedDocument:
        """Scrape content from URL.

        Args:
            url: URL to scrape

        Returns:
            ScrapedDocument with content and metadata

        Raises:
            RuntimeError: If scraping fails
        """
        session = await self._get_session()

        try:
            async with session.get(url) as response:
                if response.status != 200:
                    raise RuntimeError(
                        f"Failed to fetch {url}: HTTP {response.status}"
                    )

                html = await response.text()
                content_type = response.headers.get("Content-Type", "")

        except Exception as e:
            raise RuntimeError(f"Failed to scrape {url}: {str(e)}")

        # Parse HTML
        soup = BeautifulSoup(html, "lxml")

        # Extract title
        title = self._extract_title(soup, url)

        # Extract main content
        content = self._extract_content(soup)

        # Extract metadata
        metadata = {
            "source_url": url,
            "source_type": "documentation",  # Default type
            "source_domain": urlparse(url).netloc,
            "title": title,
            "content_type": content_type,
            "scraped_at": datetime.utcnow().isoformat(),
        }

        # Try to extract last modified date from headers or meta tags
        last_modified = self._extract_last_modified(soup, response)
        if last_modified:
            metadata["last_modified"] = last_modified

        return ScrapedDocument(
            url=url,
            title=title,
            content=content,
            metadata=metadata,
            scraped_at=datetime.utcnow(),
        )

    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        """Extract page title.

        Args:
            soup: BeautifulSoup object
            url: Page URL (fallback)

        Returns:
            Page title
        """
        # Try <title> tag
        if soup.title and soup.title.string:
            return soup.title.string.strip()

        # Try <h1> tag
        h1 = soup.find("h1")
        if h1:
            return h1.get_text().strip()

        # Try og:title meta tag
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()

        # Fallback to URL
        return url

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from page.

        Args:
            soup: BeautifulSoup object

        Returns:
            Extracted text content
        """
        # Remove script and style elements
        for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
            element.decompose()

        # Try to find main content area
        main = soup.find("main") or soup.find("article") or soup.find("div", class_=re.compile(r"content|main|body"))

        if main:
            text = main.get_text(separator="\n", strip=True)
        else:
            # Fall back to body
            text = soup.get_text(separator="\n", strip=True)

        # Clean up text
        text = self._clean_text(text)

        return text

    def _extract_last_modified(
        self, soup: BeautifulSoup, response: aiohttp.ClientResponse
    ) -> Optional[str]:
        """Extract last modified date.

        Args:
            soup: BeautifulSoup object
            response: HTTP response

        Returns:
            ISO format date string or None
        """
        # Try Last-Modified header
        last_modified = response.headers.get("Last-Modified")
        if last_modified:
            try:
                from email.utils import parsedate_to_datetime

                dt = parsedate_to_datetime(last_modified)
                return dt.isoformat()
            except:
                pass

        # Try meta tags
        meta = soup.find("meta", attrs={"name": "last-modified"}) or soup.find(
            "meta", property="article:modified_time"
        )
        if meta and meta.get("content"):
            return meta["content"]

        return None

    def _clean_text(self, text: str) -> str:
        """Clean extracted text.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)

        # Remove lines that are too short (likely navigation/junk)
        lines = text.split("\n")
        lines = [line.strip() for line in lines if len(line.strip()) > 3]

        text = "\n".join(lines)
        return text.strip()

    async def scrape_recursive(
        self,
        start_url: str,
        max_depth: int = 2,
        max_pages: int = 50,
        url_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> List[ScrapedDocument]:
        """Recursively scrape URLs starting from a given URL.

        Args:
            start_url: Starting URL to crawl from
            max_depth: Maximum crawl depth (1 = only start_url)
            max_pages: Maximum number of pages to scrape
            url_patterns: URL patterns to include (glob syntax, e.g., "*/docs/*")
            exclude_patterns: URL patterns to exclude (glob syntax)

        Returns:
            List of ScrapedDocument objects

        Raises:
            RuntimeError: If scraping fails
        """
        # Initialize tracking sets
        visited: Set[str] = set()
        to_visit: List[tuple[str, int, bool]] = [(start_url, 0, True)]  # (url, depth, is_start)
        scraped_docs: List[ScrapedDocument] = []

        # Get base domain for same-domain filtering
        base_domain = urlparse(start_url).netloc

        while to_visit and len(scraped_docs) < max_pages:
            url, depth, is_start = to_visit.pop(0)

            # Skip if already visited
            if url in visited:
                continue

            # Mark as visited
            visited.add(url)

            # Check URL patterns (but always allow the starting URL)
            if not is_start and not self._should_scrape_url(url, url_patterns, exclude_patterns):
                # Still extract links from this page to find matching pages
                if depth < max_depth:
                    try:
                        links = await self._extract_links(url, base_domain)
                        for link in links:
                            if link not in visited:
                                to_visit.append((link, depth + 1, False))
                    except Exception as e:
                        print(f"Warning: Failed to extract links from {url}: {e}")
                continue

            # Scrape the page
            try:
                doc = await self.scrape_url(url)
                scraped_docs.append(doc)

                # If we haven't reached max depth, extract links to crawl
                if depth < max_depth:
                    links = await self._extract_links(url, base_domain)
                    for link in links:
                        if link not in visited:
                            to_visit.append((link, depth + 1, False))

            except Exception as e:
                # Log error but continue crawling
                print(f"Warning: Failed to scrape {url}: {e}")
                continue

        return scraped_docs

    def _should_scrape_url(
        self,
        url: str,
        url_patterns: Optional[List[str]],
        exclude_patterns: Optional[List[str]],
    ) -> bool:
        """Check if URL should be scraped based on patterns.

        Args:
            url: URL to check
            url_patterns: Include patterns (if None, include all)
            exclude_patterns: Exclude patterns

        Returns:
            True if URL should be scraped
        """
        # Check exclude patterns first
        if exclude_patterns:
            for pattern in exclude_patterns:
                if fnmatch(url, pattern):
                    return False

        # Check include patterns
        if url_patterns:
            for pattern in url_patterns:
                if fnmatch(url, pattern):
                    return True
            return False  # No pattern matched

        return True  # No patterns means include all

    async def _extract_links(self, url: str, base_domain: str) -> List[str]:
        """Extract links from a page.

        Args:
            url: Current page URL
            base_domain: Base domain to restrict links to

        Returns:
            List of absolute URLs from the same domain
        """
        session = await self._get_session()

        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return []

                html = await response.text()

        except Exception:
            return []

        # Parse HTML
        soup = BeautifulSoup(html, "lxml")

        # Extract all links
        links = []
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]

            # Convert relative URLs to absolute
            absolute_url = urljoin(url, href)

            # Parse URL
            parsed = urlparse(absolute_url)

            # Skip non-HTTP(S) links
            if parsed.scheme not in ("http", "https"):
                continue

            # Skip if different domain
            if parsed.netloc != base_domain:
                continue

            # Remove fragment
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                clean_url += f"?{parsed.query}"

            links.append(clean_url)

        return list(set(links))  # Deduplicate

    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
