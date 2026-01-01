from data import Synopsis

from typing import List, Dict, Optional, Union
from abc import ABC, abstractmethod
from pathlib import Path

import json


class Indexer(ABC):
    """
    Abstract base class for story indexers.
    """

    SETTINGS_FILE = ".indexer_settings.json"

    
    def __init__(self, settings_path: Optional[str] = None):
        """
        Initialize the indexer.
        """
        self.settings_path = settings_path or self.SETTINGS_FILE
        self._settings = self._load_settings()
    

    def _load_settings(self) -> Dict:
        """
        Load settings.
        """
        path = Path(self.settings_path)
        if path.exists():
            with open(path, 'r') as f:
                return json.load(f)
        return {}
    

    def _save_settings(self) -> None:
        """
        Save settings.
        """
        with open(self.settings_path, 'w') as f:
            json.dump(self._settings, f, indent=2)
    

    @abstractmethod
    def create_story(self, story: 'Synopsis', content: Union[str, List[str]]) -> 'Synopsis':
        """
        Create a new story with all parts.
        """
        pass
    

    @abstractmethod
    def read_story(self, title: str, author: str) -> 'Synopsis':
        """
        Retrieve a story by title and author.
        """
        pass
    

    @abstractmethod
    def update_story(self, title: str, author: str, **updates) -> 'Synopsis':
        """
        Update story metadata or content.
        """
        pass
    

    @abstractmethod
    def delete_story(self, title: str, author: str) -> None:
        """
        Delete a story and cleanup.
        """
        pass
    

    @abstractmethod
    def list_stories(self, author: Optional[str] = None, category: Optional[str] = None) -> List['Synopsis']:
        """
        List stories with optional filters.
        """
        pass
