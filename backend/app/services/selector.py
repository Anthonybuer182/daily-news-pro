import re
from typing import List, Optional
from bs4 import BeautifulSoup
from lxml import etree


class SelectorParser:
    """CSS/XPath/Regex selector parser"""

    @staticmethod
    def parse_css(html: str, selector: str) -> List[str]:
        """Parse using CSS selector (via BeautifulSoup)"""
        soup = BeautifulSoup(html, 'lxml')
        elements = soup.select(selector)
        return [str(el) for el in elements]

    @staticmethod
    def extract_links_css(html: str, selector: str, base_url: str = "") -> List[str]:
        """Extract links using CSS selector"""
        soup = BeautifulSoup(html, 'lxml')
        elements = soup.select(selector)
        links = []
        for el in elements:
            href = el.get('href')
            if href:
                links.append(SelectorParser.normalize_url(href, base_url))
        return links

    @staticmethod
    def extract_links_xpath(html: str, selector: str, base_url: str = "") -> List[str]:
        """Extract links using XPath"""
        try:
            parser = etree.HTMLParser()
            tree = etree.fromstring(html, parser)
            elements = tree.xpath(selector)
            links = []
            for el in elements:
                href = el.get('href') if hasattr(el, 'get') else str(el)
                if href:
                    links.append(SelectorParser.normalize_url(href, base_url))
            return links
        except Exception as e:
            print(f"XPath error: {e}")
            return []

    @staticmethod
    def extract_text_css(html: str, selector: str) -> Optional[str]:
        """Extract text using CSS selector"""
        soup = BeautifulSoup(html, 'lxml')
        el = soup.select_one(selector)
        return el.get_text(strip=True) if el else None

    @staticmethod
    def extract_html_css(html: str, selector: str) -> Optional[str]:
        """Extract HTML using CSS selector"""
        soup = BeautifulSoup(html, 'lxml')
        el = soup.select_one(selector)
        return str(el) if el else None

    @staticmethod
    def extract_text_xpath(html: str, selector: str) -> Optional[str]:
        """Extract text using XPath"""
        try:
            parser = etree.HTMLParser()
            tree = etree.fromstring(html, parser)
            elements = tree.xpath(selector)
            if elements:
                el = elements[0]
                return el.text.strip() if el.text else str(el)
            return None
        except Exception as e:
            print(f"XPath error: {e}")
            return None

    @staticmethod
    def extract_attribute_css(html: str, selector: str, attr: str) -> Optional[str]:
        """Extract attribute using CSS selector"""
        soup = BeautifulSoup(html, 'lxml')
        el = soup.select_one(selector)
        return el.get(attr) if el else None

    @staticmethod
    def extract_by_regex(text: str, pattern: str) -> List[str]:
        """Extract using regex"""
        try:
            return re.findall(pattern, text)
        except Exception as e:
            print(f"Regex error: {e}")
            return []

    @staticmethod
    def normalize_url(url: str, base_url: str = "") -> str:
        """Normalize URL"""
        from urllib.parse import urljoin, urlparse
        if not url:
            return ""
        # Remove fragment
        url = url.split('#')[0]
        # Handle relative URLs
        if base_url and not url.startswith(('http://', 'https://')):
            return urljoin(base_url, url)
        return url
