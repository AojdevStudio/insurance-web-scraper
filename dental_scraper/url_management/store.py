"""Storage and management system for URLs."""

import json
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import logging
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

@dataclass
class URLEntry:
    """Represents a stored URL with metadata."""
    url: str
    carrier: str
    category: str
    added_at: datetime = field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0
    tags: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'url': self.url,
            'carrier': self.carrier,
            'category': self.category,
            'added_at': self.added_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'tags': list(self.tags)
        }
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'URLEntry':
        """Create from dictionary."""
        return cls(
            url=data['url'],
            carrier=data['carrier'],
            category=data['category'],
            added_at=datetime.fromisoformat(data['added_at']),
            last_accessed=datetime.fromisoformat(data['last_accessed']) if data['last_accessed'] else None,
            success_count=data['success_count'],
            failure_count=data['failure_count'],
            tags=set(data['tags'])
        )

class URLStore:
    """Manages storage and retrieval of URLs."""
    
    def __init__(self, storage_file: Optional[str] = None):
        """Initialize the URL store.
        
        Args:
            storage_file: Path to JSON file for persistent storage
        """
        self.storage_file = storage_file
        self.urls: Dict[str, URLEntry] = {}
        self.carrier_index: Dict[str, Set[str]] = {}  # carrier -> set of URLs
        self.category_index: Dict[str, Set[str]] = {}  # category -> set of URLs
        self.tag_index: Dict[str, Set[str]] = {}  # tag -> set of URLs
        
        if storage_file:
            self.load()
            
    def add_url(
        self,
        url: str,
        carrier: str,
        category: str,
        tags: Optional[Set[str]] = None
    ) -> URLEntry:
        """Add a URL to the store.
        
        Args:
            url: The URL to add
            carrier: Associated carrier
            category: URL category (e.g., 'provider-portal', 'documentation')
            tags: Optional set of tags
            
        Returns:
            The created URLEntry
        """
        entry = URLEntry(
            url=url,
            carrier=carrier.lower(),
            category=category.lower(),
            tags=tags or set()
        )
        
        # Add to main storage
        self.urls[url] = entry
        
        # Update indices
        self._add_to_index(self.carrier_index, carrier.lower(), url)
        self._add_to_index(self.category_index, category.lower(), url)
        for tag in entry.tags:
            self._add_to_index(self.tag_index, tag.lower(), url)
            
        self.save()
        return entry
        
    def remove_url(self, url: str) -> bool:
        """Remove a URL from the store.
        
        Args:
            url: URL to remove
            
        Returns:
            True if URL was removed, False if not found
        """
        if url not in self.urls:
            return False
            
        entry = self.urls[url]
        
        # Remove from indices
        self._remove_from_index(self.carrier_index, entry.carrier, url)
        self._remove_from_index(self.category_index, entry.category, url)
        for tag in entry.tags:
            self._remove_from_index(self.tag_index, tag, url)
            
        # Remove from main storage
        del self.urls[url]
        
        self.save()
        return True
        
    def get_url(self, url: str) -> Optional[URLEntry]:
        """Get a URL entry.
        
        Args:
            url: URL to retrieve
            
        Returns:
            URLEntry if found, None otherwise
        """
        return self.urls.get(url)
        
    def get_urls_by_carrier(self, carrier: str) -> List[URLEntry]:
        """Get all URLs for a carrier.
        
        Args:
            carrier: Carrier name
            
        Returns:
            List of URLEntry objects
        """
        urls = self.carrier_index.get(carrier.lower(), set())
        return [self.urls[url] for url in urls]
        
    def get_urls_by_category(self, category: str) -> List[URLEntry]:
        """Get all URLs in a category.
        
        Args:
            category: Category name
            
        Returns:
            List of URLEntry objects
        """
        urls = self.category_index.get(category.lower(), set())
        return [self.urls[url] for url in urls]
        
    def get_urls_by_tag(self, tag: str) -> List[URLEntry]:
        """Get all URLs with a specific tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of URLEntry objects
        """
        urls = self.tag_index.get(tag.lower(), set())
        return [self.urls[url] for url in urls]
        
    def update_stats(self, url: str, success: bool) -> None:
        """Update success/failure statistics for a URL.
        
        Args:
            url: URL to update
            success: Whether the request was successful
        """
        if url in self.urls:
            entry = self.urls[url]
            entry.last_accessed = datetime.now()
            if success:
                entry.success_count += 1
            else:
                entry.failure_count += 1
            self.save()
            
    def add_tags(self, url: str, tags: Set[str]) -> bool:
        """Add tags to a URL.
        
        Args:
            url: URL to tag
            tags: Tags to add
            
        Returns:
            True if successful, False if URL not found
        """
        if url not in self.urls:
            return False
            
        entry = self.urls[url]
        new_tags = {tag.lower() for tag in tags}
        
        # Add new tags to indices
        for tag in new_tags - entry.tags:
            self._add_to_index(self.tag_index, tag, url)
            
        entry.tags.update(new_tags)
        self.save()
        return True
        
    def remove_tags(self, url: str, tags: Set[str]) -> bool:
        """Remove tags from a URL.
        
        Args:
            url: URL to update
            tags: Tags to remove
            
        Returns:
            True if successful, False if URL not found
        """
        if url not in self.urls:
            return False
            
        entry = self.urls[url]
        tags_to_remove = {tag.lower() for tag in tags}
        
        # Remove tags from indices
        for tag in tags_to_remove & entry.tags:
            self._remove_from_index(self.tag_index, tag, url)
            
        entry.tags -= tags_to_remove
        self.save()
        return True
        
    def save(self) -> None:
        """Save the URL store to disk if storage_file is configured."""
        if not self.storage_file:
            return
            
        data = {
            'urls': {url: entry.to_dict() for url, entry in self.urls.items()}
        }
        
        with open(self.storage_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    def load(self) -> None:
        """Load the URL store from disk if storage_file exists."""
        if not self.storage_file or not Path(self.storage_file).exists():
            return
            
        try:
            with open(self.storage_file, 'r') as f:
                content = f.read().strip()
                if not content:  # Handle empty file
                    return
                data = json.loads(content)
                
            # Clear current data
            self.urls.clear()
            self.carrier_index.clear()
            self.category_index.clear()
            self.tag_index.clear()
            
            # Load URLs and rebuild indices
            for url, entry_data in data.get('urls', {}).items():
                entry = URLEntry.from_dict(entry_data)
                self.urls[url] = entry
                
                # Rebuild indices
                self._add_to_index(self.carrier_index, entry.carrier, url)
                self._add_to_index(self.category_index, entry.category, url)
                for tag in entry.tags:
                    self._add_to_index(self.tag_index, tag, url)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON from {self.storage_file}, starting with empty store")
        except Exception as e:
            logger.error(f"Error loading URL store from {self.storage_file}: {str(e)}")
            raise
        
    @staticmethod
    def _add_to_index(index: Dict[str, Set[str]], key: str, value: str) -> None:
        """Add a value to an index."""
        if key not in index:
            index[key] = set()
        index[key].add(value)
        
    @staticmethod
    def _remove_from_index(index: Dict[str, Set[str]], key: str, value: str) -> None:
        """Remove a value from an index."""
        if key in index:
            index[key].discard(value)
            if not index[key]:
                del index[key] 