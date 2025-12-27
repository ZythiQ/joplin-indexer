from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class JMLNode:
    """
    Joplin Markup Language Node.
    """
    id: str
    type: str
    content: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    children: List['JMLNode'] = field(default_factory=list)
    parent: Optional['JMLNode'] = None


@dataclass
class JNote:
    """
    Joplin Note entity.
    """
    id: str = ''
    title: str = ''
    body: str = ''
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
