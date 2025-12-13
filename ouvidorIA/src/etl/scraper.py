import requests
import logging
import copy
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from src.etl.exceptions import DocumentProcessingError

@dataclass
class WikiSource:
    name: str
    url: str

logger = logging.getLogger(__name__)

class Scraper:
    """
    Web scraper that extracts content from wikis and organizes it into a recursive
    JSON tree structure based on HTML headings (H1-H6).
    """

    # Default terms to ignore (ignores the topic AND its children)
    DEFAULT_BLACKLIST = [
        "Ouvidoria",
        "Configurações (Gestor/Cadastrador/Administrador)",
        "Integração Fala.BR e outros sistemas",
        "Dúvidas, Suporte Técnico do Sistema e Sugestões",
        "Atualizações do sistema"
    ]

    # HTML tags to extract
    INTEREST_TAGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'pre', 'table', 'div', 'dl', 'dt', 'dd', 'a']
    
    # Header hierarchy mapping
    HEADER_LEVELS = {'h1': 1, 'h2': 2, 'h3': 3, 'h4': 4, 'h5': 5, 'h6': 6}

    def __init__(
        self,
        blacklist: Optional[List[str]] = None,
        timeout: int = 30,
        headers: Optional[Dict[str, str]] = None
    ):
        self.blacklist = blacklist or self.DEFAULT_BLACKLIST.copy()
        self.timeout = timeout
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def _extract_text(self, element) -> str:
        """
        Extract text from element
        - converts <a> tags for Markdown format [Text](Link)
        """
        element_copy = copy.copy(element)
        
        for link in element_copy.find_all('a', href=True):
            text = link.get_text(strip=True)
            href = link['href']
            
            if not text or href.startswith('#') or 'javascript:' in href:
                continue
            
            markdown_link = f" [{text}]({href}) "
            link.replace_with(markdown_link)

        raw_text = element_copy.get_text(separator=' ', strip=True)
        clean_text = re.sub(r'\s+', ' ', raw_text).strip()
        return clean_text

    def extract(self, wiki: WikiSource) -> Dict[str, Any]:
        """
        Extracts content from a single URL into a recursive tree structure.
        Returns a Dict with specific formatting required for the JSON output.
        """
        try:
            logger.info(f"Starting extraction from: {wiki.url}")
            response = requests.get(wiki.url, timeout=self.timeout, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            logger.error(f"Error extracting {wiki.url}: {e}")
            raise DocumentProcessingError(f"Failed to fetch {wiki.url}: {e}") from e
        
        content_div = soup.find('div', id="mw-content-text")
        
        if not content_div:
            error_msg = f"Conteúdo principal não encontrado para: {wiki.name}"
            raise DocumentProcessingError(error_msg)

        # The stack holds dictionaries: {'level': int, 'data': dict}
        # The 'root' is a dummy container to hold top-level H1/H2s
        root = {'sections': []} 
        stack = [{'level': 0, 'data': root}]

        # State for blocking blacklisted sections
        block_level = None 

        for element in content_div.find_all(self.INTEREST_TAGS):
            
            # --- Handling Headers (Structure) ---
            if element.name in self.HEADER_LEVELS:
                level = self.HEADER_LEVELS[element.name]
                headline_span = element.find('span', class_='mw-headline')
                title_text = headline_span.get_text(strip=True)

                if not title_text:
                    continue

                # Check Blocking (Blacklist)
                if block_level is not None:
                    if level <= block_level:
                        block_level = None # Unblock if we hit a higher or equal header
                    else:
                        continue # Skip this header and its children

                is_blacklisted = any(b.lower() in title_text.lower() for b in self.blacklist)
                if is_blacklisted:
                    block_level = level
                    continue

                # Create new section/topic node
                new_node = {
                    'title': title_text,
                    'content': "", 
                    'topics': [] # Children go here
                }

                # Pop stack until we find the parent (strictly lower level number)
                while stack[-1]['level'] >= level:
                    stack.pop()
                
                # Add new node to the parent found at top of stack
                parent_node = stack[-1]['data']
                
                # If parent is root, we add to 'sections', otherwise to 'topics'
                if stack[-1]['level'] == 0:
                    parent_node['sections'].append(new_node)
                else:
                    if 'topics' not in parent_node:
                        parent_node['topics'] = []
                    parent_node['topics'].append(new_node)

                # Push new node to stack so it can receive children/content
                stack.append({'level': level, 'data': new_node})

            # --- Handling Content (Text) ---
            else:
                # Only add content if not blocked and strictly inside a section (stack > 0)
                if block_level is None and len(stack) > 1:

                    if element.name in ['p', 'li']:
                        text = self._extract_text(element)
                        if text:
                            current_node = stack[-1]['data']
                            # Append to existing content or start new
                            current_node['content'] = (current_node.get('content', '') + "\n" + text).strip()

        return {
            "wiki_name": wiki.name,
            "wiki_url": wiki.url,
            "sections": root['sections']
        }

    def extract_multiple_wikis(self, wikis: List[WikiSource]) -> List[Dict[str, Any]]:
        """
        Orchestrates extraction for multiple Wikis.
        Returns a LIST of wiki objects (dictionaries), one for each URL.
        """
        results = []
        for wiki in wikis:
            data = self.extract(wiki)
            results.append(data)

        return results