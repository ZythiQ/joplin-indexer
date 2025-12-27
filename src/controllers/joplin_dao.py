from models.joplin_data import JNote, JFolder, JTag
from controllers.joplin_client import JoplinClient

from typing import List, Optional, Dict, Set, Literal, Union, Callable, cast
from functools import wraps


class JoplinDAO:
    """
    Joplin data access object with lazy caching and minimal code footprint.
    """
    
    EntityType = Literal['note', 'folder', 'tag']

    @staticmethod
    def _ensure_loaded(entity_type: str):
        """
        Decorator to ensure entity type is loaded before accessing the cache.
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                load_method = f'_ensure_{entity_type}_loaded'
                if hasattr(self, load_method):
                    getattr(self, load_method)()
                return func(self, *args, **kwargs)
            return wrapper
        return decorator
    
    
    def __init__(self, token: str, base_url: Optional[str] = None):
        """
        Initialize the DAO.
        """
        self._api = JoplinClient(token, base_url)
        self._loaded: Set[str] = set()

        self._folders: Dict[str, JFolder] = {}
        self._notes: Dict[str, JNote] = {}
        self._tags: Dict[str, JTag] = {}
               
        self._config = {
            'note': (self._notes, JNote, 'notes', ['id', 'title', 'parent_id', 'updated_time', 'is_todo']),
            'folder': (self._folders, JFolder, 'folders', ['id', 'title', 'parent_id']),
            'tag': (self._tags, JTag, 'tags', ['id', 'title'])
        }


    def _get_config(self, entity_type: EntityType):
        """
        Get cache, class, endpoint, and fields for an entity type.
        """
        return self._config[entity_type]


    def _to_entity(self, entity_type: EntityType, data: Dict) -> Union[JNote, JFolder, JTag]:
        """
        Convert a dict to dataclass, filtering valid fields.
        """
        _, entity_class, _, _ = self._get_config(entity_type)
        return entity_class(**{k: v for k, v in data.items() if k in entity_class.__annotations__})


    def _cache_entity(self, entity_type: EntityType, data: Dict) -> Union[JNote, JFolder, JTag]:
        """
        Cache and return an entity.
        """
        entity = self._to_entity(entity_type, data)
        cache, _, _, _ = self._get_config(entity_type)
        cache[entity.id] = entity
        return entity


    def _bulk_fetch(self, entity_type: EntityType, endpoint: Optional[str] = None, fields: Optional[List[str]] = None):
        """
        Bulk fetch and cache entities.
        """
        _, _, default_endpoint, default_fields = self._get_config(entity_type)
        endpoint = endpoint or default_endpoint
        fields = fields or default_fields
        
        items = self._api.get_paginated(endpoint, fields=fields)

        for item in items:
            self._cache_entity(entity_type, item)

    
    def _ensure_folders_loaded(self):
        """
        Lazy-load all folders.
        """
        if 'folders' not in self._loaded:
            self._bulk_fetch('folder')
            self._loaded.add('folders')


    def _ensure_notes_loaded(self, folder_id: str):
        """
        Lazy-load all notes for a folder.
        """
        scope = f'folder:{folder_id}'
        if scope not in self._loaded:
            self._bulk_fetch('note', f'folders/{folder_id}/notes')
            self._loaded.add(scope)


    def _ensure_tags_loaded(self):
        """
        Lazy-load all tags.
        """
        if 'tags' not in self._loaded:
            self._bulk_fetch('tag')
            self._loaded.add('tags')


    def _get(self, entity_type: EntityType, entity_id: str, 
             fields: Optional[List[str]] = None) -> Union[JNote, JFolder, JTag]:
        """
        Generic get operation.
        """
        cache, _, endpoint, _ = self._get_config(entity_type)
        
        if not fields and entity_id in cache:
            return cache[entity_id]
        
        params = {'fields': ','.join(fields)} if fields else {}
        data = self._api.get(f'{endpoint}/{entity_id}', **params)
        return self._cache_entity(entity_type, data)


    def _create(self, entity_type: EntityType, data: Dict) -> Union[JNote, JFolder, JTag]:
        """
        Generic create operation.
        """
        _, _, endpoint, _ = self._get_config(entity_type)
        result = self._api.post(endpoint, data)
        return self._cache_entity(entity_type, result)


    def _update(self, entity_type: EntityType, entity_id: str, **fields) -> Union[JNote, JFolder, JTag]:
        """
        Generic update operation.
        """
        _, _, endpoint, _ = self._get_config(entity_type)
        result = self._api.put(f'{endpoint}/{entity_id}', fields)
        return self._cache_entity(entity_type, result)


    def _delete(self, entity_type: EntityType, entity_id: str):
        """
        Generic delete operation.
        """
        _, _, endpoint, _ = self._get_config(entity_type)
        self._api.delete(f'{endpoint}/{entity_id}')

        cache, _, _, _ = self._get_config(entity_type)
        cache.pop(entity_id, None)

        if entity_type == 'folder':
            removed_ids = [nid for nid, n in self._notes.items() if n.parent_id == entity_id]

            for nid in removed_ids:
                self._notes.pop(nid, None)

        elif entity_type == 'tag':
            for note in self._notes.values():
                note.tags = [t for t in note.tags if t.id != entity_id]


    def clear_cache(self):
        """
        Clear all caches.
        """
        self._notes.clear()
        self._folders.clear()
        self._tags.clear()
        self._loaded.clear()


    def get_folder(self, folder_id: str, fields: Optional[List[str]] = None) -> JFolder:
        """
        Get a folder with optional field selection.
        """
        return cast(JFolder, self._get('folder', folder_id, fields))


    @_ensure_loaded('folders')
    def list_folders(self, parent_id: Optional[str] = None, root_only: bool = False) -> List[JFolder]:
        """
        List folders with optional filtering by parent or root only.
        """
        folders = list(self._folders.values())
        
        if root_only:
            return [f for f in folders if not f.parent_id]
        
        if parent_id is not None:
            return [f for f in folders if f.parent_id == parent_id]
        
        return folders


    @_ensure_loaded('folders')
    def get_folder_path(self, folder_id: str) -> str:
        """
        Get full folder path by traversing tree structure.
        """
        path = []
        cid = folder_id
        
        while cid and cid in self._folders:
            path.insert(0, self._folders[cid].title)
            cid = self._folders[cid].parent_id

        return '/'.join(path)


    def create_folder(self, title: str, parent_id: str = '') -> JFolder:
        """
        Create a new folder.
        """
        return cast(JFolder, self._create('folder', {'title': title, 'parent_id': parent_id}))


    def update_folder(self, folder_id: str, **fields) -> JFolder:
        """
        Update folder fields.
        """
        return cast(JFolder, self._update('folder', folder_id, **fields))


    def delete_folder(self, folder_id: str):
        """
        Delete a folder and all its notes.
        """
        self._delete('folder', folder_id)


    def get_note(self, note_id: str, fields: Optional[List[str]] = None) -> JNote:
        """
        Get a note with optional field selection.
        """
        return cast(JNote, self._get('note', note_id, fields))


    def list_notes(self, folder_id: Optional[str] = None, tag_id: Optional[str] = None, todo_only: bool = False) -> List[JNote]:
        """
        List notes with optional filtering by folder, tag, or todo status.
        """
        if folder_id:
            self._ensure_notes_loaded(folder_id)
            notes = [n for n in self._notes.values() if n.parent_id == folder_id]

        elif tag_id:
            tag = cast(JTag, self._get('tag', tag_id))

            if (scope := f'tag:{tag_id}') not in self._loaded:
                for item in self._api.get_paginated(f'tags/{tag_id}/notes',
                    fields=['id', 'title', 'parent_id', 'updated_time', 'is_todo']
                ):
                    note = cast(JNote, self._cache_entity('note', item))
                    
                    if not any(t.id == tag_id for t in note.tags):
                        note.tags.append(tag)

                self._loaded.add(scope)

            notes = [n for n in self._notes.values() if any(t.id == tag_id for t in n.tags)]

        else:
            self._bulk_fetch('note')
            notes = list(self._notes.values())
        
        return [n for n in notes if n.is_todo] if todo_only else notes


    def search_notes(self, query: str) -> List[JNote]:
        """
        Search notes by title or body content.
        """
        result = self._api.get('search', query=query, type='note', fields='id,title,parent_id')
        return [cast(JNote, self._cache_entity('note', item)) for item in result.get('items', [])]


    def create_note(self, title: str, body: str = '', folder_id: str = '', **kwargs) -> JNote:
        """
        Create a new note.
        """
        data = {'title': title, 'body': body, 'parent_id': folder_id, **kwargs}
        return cast(JNote, self._create('note', data))


    def update_note(self, note_id: str, **fields) -> JNote:
        """
        Update note fields.
        """
        return cast(JNote, self._update('note', note_id, **fields))


    def delete_note(self, note_id: str):
        """
        Delete a note.
        """
        self._delete('note', note_id)


    def move_notes(self, note_ids: List[str], target_folder_id: str) -> int:
        """
        Move notes to a target folder and return the count of moved notes.
        """
        moved = 0
        for note_id in note_ids:
            try:
                self.update_note(note_id, parent_id=target_folder_id)
                moved += 1
            except Exception:
                continue
        return moved


    def get_tag(self, tag_id: str) -> JTag:
        """
        Get a tag by ID.
        """
        return cast(JTag, self._get('tag', tag_id))


    @_ensure_loaded('tags')
    def list_tags(self) -> List[JTag]:
        """
        List all tags.
        """
        return list(self._tags.values())


    def create_tag(self, title: str) -> JTag:
        """
        Create a new tag.
        """
        return cast(JTag, self._create('tag', {'title': title}))


    def update_tag(self, tag_id: str, **fields) -> JTag:
        """
        Update tag fields.
        """
        return cast(JTag, self._update('tag', tag_id, **fields))


    def delete_tag(self, tag_id: str):
        """
        Delete a tag.
        """
        self._delete('tag', tag_id)


    def get_note_tags(self, note_id: str) -> List[JTag]:
        """
        Get all tags associated with a note.
        """
        items = self._api.get_paginated(f'notes/{note_id}/tags', fields=['id', 'title'])
        tags = [cast(JTag, self._cache_entity('tag', item)) for item in items]

        if note_id in self._notes:
            self._notes[note_id].tags = tags

        return tags


    def tag_note(self, note_id: str, tag_id: str):
        """
        Add a tag to a note.
        """
        self._api.post(f'tags/{tag_id}/notes', {'id': note_id})
        
        if note_id in self._notes:
            note = self._notes[note_id]

            if not any(t.id == tag_id for t in note.tags):
                note.tags.append(cast(JTag, self._get('tag', tag_id)))



    def untag_note(self, note_id: str, tag_id: str):
        """
        Remove a tag from a note.
        """
        self._api.delete(f'tags/{tag_id}/notes/{note_id}')
        
        if note_id in self._notes:
            note = self._notes[note_id]
            note.tags = [t for t in note.tags if t.id != tag_id]
