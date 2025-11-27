"""Simple document scraper and processor."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional
from urllib.parse import urlparse

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
    """Simple document scraper for web pages."""

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
