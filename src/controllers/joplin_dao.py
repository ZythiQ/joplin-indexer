from models.joplin_data import JNote, JFolder, JTag
from controllers.joplin_client import JoplinClient

from typing import List, Optional, Dict, Set, Literal
from datetime import datetime, timedelta


class JoplinDAO:
    """
    Joplin data access object.
    """
    
    EntityType = Literal['note', 'folder', 'tag']
    
    def __init__(self, token: str, base_url: Optional[str] = None):
        """
        Initialize the DAO.
        """
        self._api = JoplinClient(token, base_url)

        self._notes_by_folder: Dict[str, Set[str]] = {}
        self._notes_by_tag: Dict[str, Set[str]] = {}
        
        self._folder_cache: Dict[str, Dict] = {}
        self._note_cache: Dict[str, Dict] = {}
        self._tag_cache: Dict[str, Dict] = {}
        
        self._cache_ttl = timedelta(minutes=5)
        self._cache_timestamp = None

        self._cache_config = {
            'note': {
                'cache': self._note_cache,
                'fields': ['id', 'title', 'parent_id', 'updated_time', 'is_todo']
            },
            'folder': {
                'cache': self._folder_cache,
                'fields': ['id', 'title', 'parent_id']
            },
            'tag': {
                'cache': self._tag_cache,
                'fields': ['id', 'title']
            }
        }


    def _dict_to_note(self, data: Dict) -> JNote:
        return JNote(**{k: v for k, v in data.items()
                        if k in JNote.__annotations__})
    

    def _dict_to_folder(self, data: Dict) -> JFolder:
        return JFolder(**{k: v for k, v in data.items()
                          if k in JFolder.__annotations__})
    

    def _dict_to_tag(self, data: Dict) -> JTag:
        return JTag(**{k: v for k, v in data.items()
                       if k in JTag.__annotations__})
    

    def _rebuild_cache(self):
        """
        Rebuild lightweight cache from API.
        """
        notes = self._api.get_paginated('notes', fields=self._cache_config['note']['fields'])
        self._note_cache.clear()

        self._note_cache.update({n['id']: n for n in notes})
        self._notes_by_folder.clear()

        for note in notes:
            parent = note.get('parent_id', '')

            if parent: 
                self._notes_by_folder.setdefault(parent, set()).add(note['id'])
        
        # Folders:
        folders = self._api.get_paginated('folders', fields=self._cache_config['folder']['fields'])
        self._folder_cache.clear()

        self._folder_cache.update({f['id']: f for f in folders})
        
        # Tags:
        tags = self._api.get_paginated('tags', fields=self._cache_config['tag']['fields'])
        self._tag_cache.clear()

        self._tag_cache.update({t['id']: t for t in tags})
        self._notes_by_tag.clear()

        for tag_id in self._tag_cache:
            note_items = self._api.get_paginated(f'tags/{tag_id}/notes', fields=['id'])
            self._notes_by_tag[tag_id] = {n['id'] for n in note_items}
        
        self._cache_timestamp = datetime.now()


    def _freshen_cache(self):
        """
        Lazy-load cache only when needed with TTL.
        """
        now = datetime.now()
        
        if (self._cache_timestamp is None or 
            now - self._cache_timestamp > self._cache_ttl):
            self._rebuild_cache()


    def _invalidate_cache(self):
        """
        Force cache refresh on next access.
        """
        self._cache_timestamp = None


    def _update_cache(self, entity_type: 'JoplinDAO.EntityType', entity_id: str, data: Optional[Dict] = None):
        """
        Generic method to add/update/remove an entity in cache.
        If data is None, removes the entity. Otherwise, adds/updates it.
        """
        if self._cache_timestamp is None:
            return
        
        config = self._cache_config[entity_type]

        if data is None:
            entity = config['cache'].pop(entity_id, None)

            if entity_type == 'note' and entity:
                pid = entity.get('parent_id', '')

                if pid and pid in self._notes_by_folder:
                    self._notes_by_folder[pid].discard(entity_id)

                for tag_notes in self._notes_by_tag.values():
                    tag_notes.discard(entity_id)

            elif entity_type == 'tag':
                self._notes_by_tag.pop(entity_id, None)
        
        else:
            cached_data = {k: data.get(k, '') for k in config['fields']}
            config['cache'][entity_id] = cached_data
            
            if entity_type == 'note':
                pid = data.get('parent_id', '')
                
                if pid:
                    self._notes_by_folder.setdefault(pid, set()).add(entity_id)


    def refresh_cache(self):
        """
        Manually refresh cache.
        """
        self._rebuild_cache()

    
    def get_folder(self, folder_id: str, fields: List[str] | None = None) -> JFolder:
        """
        Get a folder with optional field selection.
        """
        params = {'fields': ','.join(fields)} if fields else {}
        data = self._api.get(f'folders/{folder_id}', **params)
        return self._dict_to_folder(data)
    

    def list_folders(self, parent_id: Optional[str] = None, root_only: bool = False) -> List[Dict]:
        """
        List folders (id, title, parent_id).
        """
        self._freshen_cache()
        folders = list(self._folder_cache.values())
        
        if root_only:
            folders = [f for f in folders if not f['parent_id']]

        elif parent_id is not None:
            folders = [f for f in folders if f['parent_id'] == parent_id]

        return folders
    

    def get_folder_path(self, folder_id: str) -> str:
        """
        Get full folder path ('Work/Projects/Client A').
        """
        self._freshen_cache()
        
        path_parts = []
        cid = folder_id
        
        while cid:
            folder = self._folder_cache.get(cid)
            if not folder: break

            path_parts.insert(0, folder['title'])
            cid = folder['parent_id']

        return '/'.join(path_parts)
    

    def create_folder(self, title: str, parent_id: str = '') -> JFolder:
        """
        Create a new folder.
        """
        data = self._api.post('folders', {'title': title, 'parent_id': parent_id})
        folder = self._dict_to_folder(data)
        self._update_cache('folder', data['id'], data)
        return folder
    

    def update_folder(self, folder_id: str, **fields) -> JFolder:
        """
        Update folder fields.
        """
        result = self._api.put(f'folders/{folder_id}', fields)
        folder = self._dict_to_folder(result)
        self._update_cache('folder', result['id'], result)
        return folder


    def delete_folder(self, folder_id: str) -> None:
        """
        Delete a folder.
        """
        self._api.delete(f'folders/{folder_id}')
        self._update_cache('folder', folder_id)

    
    def get_note(self, note_id: str, fields: List[str] | None = None) -> JNote:
        """
        Get a note with optional field selection.
        """
        params = {'fields': ','.join(fields)} if fields else {}
        data = self._api.get(f'notes/{note_id}', **params)
        return self._dict_to_note(data)
    

    def list_notes(self, folder_id: Optional[str] = None, tag_id: Optional[str] = None, todo_only: bool = False) -> List[Dict]:
        """
        List notes (id, title, parent_id, timestamps).
        """
        self._freshen_cache()
        
        if folder_id:
            note_ids = self._notes_by_folder.get(folder_id, set())
            notes = [self._note_cache[nid] for nid in note_ids]
        elif tag_id:
            note_ids = self._notes_by_tag.get(tag_id, set())
            notes = [self._note_cache[nid] for nid in note_ids]
        else:
            notes = list(self._note_cache.values())
        
        if todo_only:
            notes = [n for n in notes if n.get('is_todo')]
        
        return notes
    

    def search_notes(self, query: str, use_cache: bool = True) -> List[Dict]:
        """
        Search notes by title/body.
        """
        params = {'query': query, 'type': 'note', 'fields': 'id,title,parent_id'}
        result = self._api.get('search', **params)
        api_results = result.get('items', [])
        cache_results = []
        
        if not use_cache:
            return api_results
        
        self._freshen_cache()

        for note_dict in self._note_cache.values():
            title = note_dict.get('title', '').lower()

            if query.lower() in title:
                if not any(r['id'] == note_dict['id'] for r in api_results):
                    cache_results.append({
                        'id': note_dict['id'],
                        'title': note_dict.get('title', ''),
                        'parent_id': note_dict.get('parent_id', '')
                    })
        
        return api_results + cache_results
    

    def create_note(self, title: str, body: str = '', folder_id: str = '', **kwargs) -> JNote:
        """
        Create a new note.
        """
        data = {'title': title, 'body': body, 'parent_id': folder_id, **kwargs}
        result = self._api.post('notes', data)
        note = self._dict_to_note(result)

        self._update_cache('note', result['id'], result)
        return note
    

    def update_note(self, note_id: str, **fields) -> JNote:
        """
        Update note fields.
        """
        result = self._api.put(f'notes/{note_id}', fields)
        note = self._dict_to_note(result)

        self._update_cache('note', result['id'], result)
        return note
    
    
    def move_notes(self, note_ids: List[str], target_folder_id: str) -> int:
        """
        Bulk move notes to folder and return the count.
        """
        moved_count = 0
        
        for note_id in note_ids:
            try:
                result = self._api.put(f'notes/{note_id}', {'parent_id': target_folder_id})
                self._update_cache('note', result['id'], result)
                moved_count += 1

            except Exception:
                continue
        
        return moved_count
    

    def delete_note(self, note_id: str) -> None:
        """
        Delete a note.
        """
        self._api.delete(f'notes/{note_id}')
        self._update_cache('note', note_id)

    
    def get_tag(self, tag_id: str) -> JTag:
        """
        Get a tag.
        """
        data = self._api.get(f'tags/{tag_id}')
        return self._dict_to_tag(data)
    

    def list_tags(self) -> List[Dict]:
        """
        List all tags.
        """
        self._freshen_cache()
        return list(self._tag_cache.values())
    

    def create_tag(self, title: str) -> JTag:
        """
        Create a new tag.
        """
        data = self._api.post('tags', {'title': title})
        tag = self._dict_to_tag(data)

        self._update_cache('tag', data['id'], data)
        return tag
    

    def update_tag(self, tag_id: str, **fields) -> JTag:
        """
        Update tag fields.
        """
        result = self._api.put(f'tags/{tag_id}', fields)
        tag = self._dict_to_tag(result)

        self._update_cache('tag', result['id'], result)
        return tag


    def delete_tag(self, tag_id: str) -> None:
        """
        Delete a tag.
        """
        self._api.delete(f'tags/{tag_id}')
        self._update_cache('tag', tag_id)

    
    def get_note_tags(self, note_id: str) -> List[Dict]:
        """
        Get tags for a note.
        """
        items = self._api.get_paginated(f'notes/{note_id}/tags', fields=['id', 'title'])
        return items
    

    def get_notes_with_tag(self, tag_id: str) -> List[Dict]:
        """
        Get notes with a tag.
        """
        self._freshen_cache()
        note_ids = self._notes_by_tag.get(tag_id, set())
        return [self._note_cache[nid] for nid in note_ids]
    

    def tag_note(self, note_id: str, tag_id: str) -> None:
        """
        Add a tag to a note.
        """
        self._api.post(f'tags/{tag_id}/notes', {'id': note_id})
        
        if self._cache_timestamp:
            if tag_id not in self._notes_by_tag:
                self._notes_by_tag[tag_id] = set()
                
            self._notes_by_tag[tag_id].add(note_id)

    
    def untag_note(self, note_id: str, tag_id: str) -> None:
        """
        Remove a tag from a note.
        """
        self._api.delete(f'tags/{tag_id}/notes/{note_id}')
        
        if self._cache_timestamp and tag_id in self._notes_by_tag:
            self._notes_by_tag[tag_id].discard(note_id)
