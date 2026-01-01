from typing import Dict, List, Literal, Union, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


@dataclass
class Synopsis:
    """
    Story synopsis.
    """
    title: str
    author: str
    author_url: str = "#"

    description: Union[str, List[str]] = ""
    genres: List[str] = field(default_factory=list)
    category: Literal['short', 'series', 'anthology'] = 'short'

    parts: List[str] = field(default_factory=list)
    relations: Optional[Dict[str, str]] = None


@dataclass
class MMLNode:
    """
    Markdown Markup Language Node.
    """
    class Type(Enum):
        NODE = 'node'
        CONTAINER = 'container'
        FRAGMENT = 'fragment'
    
    id: str
    content: str
    type: 'MMLNode.Type'

    attributes: Dict[str, Any] = field(default_factory=dict)
    children: List['MMLNode'] = field(default_factory=list)
    parent: Optional['MMLNode'] = None


@dataclass
class JNote:
    """
    Joplin Note entity.
    """
    id: str = ''
    body: str = ''
    title: str = ''
    parent_id: str = ''

    is_todo: int = 0
    todo_completed: int = 0

    created_time: int = 0
    updated_time: int = 0

    author: str = ''
    source_url: str = ''
    markup_language: int = 1

    tags: List['JTag'] = field(default_factory=list)


@dataclass
class JFolder:
    """
    Joplin Folder entity.
    """
    id: str = ''
    title: str = ''
    parent_id: str = ''

    created_time: int = 0
    updated_time: int = 0

    icon: str = ''


@dataclass
class JTag:
    """
    Joplin Tag entity.
    """
    id: str = ''
    title: str = ''

    created_time: int = 0
    updated_time: int = 0
