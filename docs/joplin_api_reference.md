# Joplin API Reference

**The Joplin integration provides two layers:**

- **JoplinClient**: Low-level REST API client
- **JoplinDAO**: High-level data access layer with caching and query operations

**Generally you should use the JoplinDAO**, which internally uses JoplinClient and provides usability improvements.

---

## JoplinDAO

#### `JoplinDAO(token: str, base_url: Optional[str] = None)`

Initialize the DAO with Joplin API credentials.

**Parameters:**

- `token` (str): Joplin API token (from Web Clipper settings)
- `base_url` (str, optional): Joplin API base URL

**Example:**

```python
dao = JoplinDAO(token="your_token_here")
```

**Notes:**

- Automatically discovers Joplin port (41184-41194) if `base_url` is omitted
- Creates internal caches that are lazily populated on access
- Uses singleton pattern for the underlying `JoplinClient`

---

### Folder Operations

#### `list_folders(parent_id: Optional[str] = None, root_only: bool = False) -> List[JFolder]`

List folders with optional filtering.

**Parameters:**

- `parent_id` (str, optional): Filter to children of this folder
- `root_only` (bool, optional): Filter to root-level folders only

**Returns:**

- `List[JFolder]`: List of folder objects

**Example:**

```python
# Get all folders
all_folders = dao.list_folders()

# Get root folders only
roots = dao.list_folders(root_only=True)

# Get children of specific folder
children = dao.list_folders(parent_id="folder123")
```

---

#### `get_folder(folder_id: str, fields: Optional[List[str]] = None) -> JFolder`

Get a single folder by ID.

**Parameters:**

- `folder_id` (str): Folder ID
- `fields` (List[str], optional): Specific fields to fetch (fetches all if omitted)

**Returns:**

- `JFolder`: Folder object

**Example:**

```python
folder = dao.get_folder("folder123")
print(folder.title)

# Fetch specific fields only
folder = dao.get_folder("folder123", fields=["id", "title"])
```

**Raises:**

- `JoplinNotFoundError`: If folder doesn't exist

---

#### `get_folder_path(folder_id: str) -> str`

Get the full hierarchical path to a folder. This traverses parent relationships to build path

**Parameters:**

- `folder_id` (str): Folder ID

**Returns:**

- `str`: Path string (e.g., "Library/Melville/Moby Dick")

**Example:**

```python
path = dao.get_folder_path("folder123")
# "Library/Authors/Melville"
```

---

#### `create_folder(title: str, parent_id: str = '') -> JFolder`

Create a new folder.

**Parameters:**

- `title` (str): Folder title
- `parent_id` (str, optional): Parent folder ID (empty string for root)

**Returns:**

- `JFolder`: Created folder object

**Example:**

```python
# Create root folder
library = dao.create_folder("Library")

# Create subfolder
authors = dao.create_folder("Authors", parent_id=library.id)
```

---

#### `update_folder(folder_id: str, **fields) -> JFolder`

Update folder fields.

**Parameters:**

- `folder_id` (str): Folder ID
- `**fields`: Key-value pairs to update

**Returns:**

- `JFolder`: Updated folder object

**Example:**

```python
folder = dao.update_folder("folder123", title="New Title")
```

---

#### `delete_folder(folder_id: str) -> None`

Delete a folder and all its notes.

**Parameters:**

- `folder_id` (str): Folder ID

**Example:**

```python
dao.delete_folder("folder123")
```

---

### Note Operations

#### `list_notes(folder_id: Optional[str] = None, tag_id: Optional[str] = None, todo_only: bool = False) -> List[JNote]`

List notes with flexible filtering.

**Parameters:**

- `folder_id` (str, optional): Filter to notes in this folder
- `tag_id` (str, optional): Filter to notes with this tag
- `todo_only` (bool, optional): Filter to todo notes only

**Returns:**

- `List[JNote]`: List of note objects

**Example:**

```python
# Get all notes in a folder
notes = dao.list_notes(folder_id="folder123")

# Get notes with specific tag
tagged = dao.list_notes(tag_id="tag456")

# Get all todos
todos = dao.list_notes(todo_only=True)

# Get all notes (expensive, lazy loads everything)
all_notes = dao.list_notes()
```

**Notes:**

- Different scopes cache independently (per-folder, per-tag, global)

---

#### `get_note(note_id: str, fields: Optional[List[str]] = None) -> JNote`

Get a single note by ID.

**Parameters:**

- `note_id` (str): Note ID
- `fields` (List[str], optional): Specific fields to fetch

**Returns:**

- `JNote`: Note object

**Example:**

```python
note = dao.get_note("note123")
print(note.title, note.body)

# Fetch with specific fields
note = dao.get_note("note123", fields=["id", "title", "body"])
```

**Raises:**

- `JoplinNotFoundError`: If note doesn't exist

---

#### `search_notes(query: str) -> List[JNote]`

Search notes by title or body content.

**Parameters:**

- `query` (str): Search query

**Returns:**

- `List[JNote]`: Matching notes

**Example:**

```python
results = dao.search_notes("moby dick")
for note in results:
    print(note.title)
```

**Notes:**

- Uses Joplin's built-in search functionality

---

#### `create_note(title: str, body: str = '', folder_id: str = '', **kwargs) -> JNote`

Create a new note.

**Parameters:**

- `title` (str): Note title
- `body` (str, optional): Note markdown content
- `folder_id` (str, optional): Parent folder ID
- `**kwargs`: Additional note fields (e.g., `is_todo`, `author`)

**Returns:**

- `JNote`: Created note object

**Example:**

```python
# Simple note
note = dao.create_note("My Note", body="Content here")

# Note in specific folder
note = dao.create_note("Story", body="Once upon a time...", folder_id="folder123")

# Todo note with metadata
todo = dao.create_note("Task", is_todo=1, author="John")
```

---

#### `update_note(note_id: str, **fields) -> JNote`

Update note fields.

**Parameters:**

- `note_id` (str): Note ID
- `**fields`: Key-value pairs to update

**Returns:**

- `JNote`: Updated note object

**Example:**

```python
# Update body
note = dao.update_note("note123", body="New content")

# Update multiple fields
note = dao.update_note("note123", 
    title="Updated Title",
    body="Updated body",
    is_todo=1
)
```

---

#### `delete_note(note_id: str) -> None`

Delete a note.

**Parameters:**

- `note_id` (str): Note ID

**Example:**

```python
dao.delete_note("note123")
```

---

#### `move_notes(note_ids: List[str], target_folder_id: str) -> int`

Move multiple notes to a target folder.

**Parameters:**

- `note_ids` (List[str]): List of note IDs to move
- `target_folder_id` (str): Destination folder ID

**Returns:**

- `int`: Number of notes successfully moved

**Example:**

```python
moved = dao.move_notes(
    ["note1", "note2", "note3"],
    target_folder_id="folder456"
)
print(f"Moved {moved} notes")
```

**Notes:**

- Continues on errors.

---

### Tag Operations

#### `list_tags() -> List[JTag]`

List all tags.

**Returns:**

- `List[JTag]`: List of tag objects

**Example:**

```python
tags = dao.list_tags()
for tag in tags:
    print(tag.title)
```

---

#### `get_tag(tag_id: str) -> JTag`

Get a single tag by ID.

**Parameters:**

- `tag_id` (str): Tag ID

**Returns:**

- `JTag`: Tag object

**Example:**

```python
tag = dao.get_tag("tag123")
```

**Raises:**

- `JoplinNotFoundError`: If tag doesn't exist

---

#### `create_tag(title: str) -> JTag`

Create a new tag.

**Parameters:**

- `title` (str): Tag title

**Returns:**

- `JTag`: Created tag object

**Example:**

```python
tag = dao.create_tag("fantasy")
```

---

#### `update_tag(tag_id: str, **fields) -> JTag`

Update tag fields.

**Parameters:**

- `tag_id` (str): Tag ID
- `**fields`: Fields to update

**Returns:**

- `JTag`: Updated tag object

**Example:**

```python
tag = dao.update_tag("tag123", title="new-name")
```

---

#### `delete_tag(tag_id: str) -> None`

Delete a tag.

**Parameters:**

- `tag_id` (str): Tag ID

**Example:**

```python
dao.delete_tag("tag123")
```

---

#### `get_note_tags(note_id: str) -> List[JTag]`

Get all tags associated with a note.

**Parameters:**

- `note_id` (str): Note ID

**Returns:**

- `List[JTag]`: List of tag objects

**Example:**

```python
tags = dao.get_note_tags("note123")
for tag in tags:
    print(tag.title)
```

---

#### `tag_note(note_id: str, tag_id: str) -> None`

Add a tag to a note.

**Parameters:**

- `note_id` (str): Note ID
- `tag_id` (str): Tag ID

**Example:**

```python
dao.tag_note("note123", "tag456")
```

**Notes:**

- Idempotent (safe to call multiple times with the same tag)

---

#### `untag_note(note_id: str, tag_id: str) -> None`

Remove a tag from a note.

**Parameters:**

- `note_id` (str): Note ID
- `tag_id` (str): Tag ID

**Example:**

```python
dao.untag_note("note123", "tag456")
```

---

### Cache Management

#### `clear_cache() -> None`

Clear all cached data.

**Example:**

```python
dao.clear_cache()
```

**Notes:**

- Forces fresh fetch on next access
- Useful after external modifications to Joplin data

---

### Data Models

#### JNote

```python
@dataclass
class JNote:
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
    tags: List[JTag] = field(default_factory=list)
```

---

#### JFolder

```python
@dataclass
class JFolder:
    id: str = ''
    title: str = ''
    parent_id: str = ''
    created_time: int = 0
    updated_time: int = 0
    icon: str = ''
```

---

#### JTag

```python
@dataclass
class JTag:
    id: str = ''
    title: str = ''
    created_time: int = 0
    updated_time: int = 0
```

---

## JoplinClient

#### `JoplinClient(token: str, base_url: Optional[str] = None)`

Initialize the API client.

**Parameters:**

- `token` (str): Joplin API token
- `base_url` (str, optional): API base URL

**Example:**

```python
client = JoplinClient(token="your_token")
```

**Notes:**

- Auto-discovers port by testing 41184-41194
- Discovery happens once and is cached

---

### Port Discovery

#### `reset_discovery() -> None` (class method)

Reset port discovery state to force re-discovery.

**Example:**

```python
JoplinClient.reset_discovery()
client = JoplinClient(token="your_token")  # Will discover port again
```

**Notes:**

- Static method, call on class not instance
- Useful if Joplin restarts on a different port

---

### HTTP Methods

#### `get(endpoint: str, **params) -> Any`

Make a GET request.

**Parameters:**

- `endpoint` (str): API endpoint (e.g., "notes/note123")
- `**params`: Query parameters

**Returns:**

- `Any`: JSON response

**Example:**

```python
note = client.get("notes/note123")
notes = client.get("notes", limit=10, page=1)
```

---

#### `post(endpoint: str, data: Dict) -> Any`

Make a POST request.

**Parameters:**

- `endpoint` (str): API endpoint
- `data` (Dict): Request body

**Returns:**

- `Any`: JSON response

**Example:**

```python
note = client.post("notes", {"title": "New Note", "body": "Content"})
```

---

#### `put(endpoint: str, data: Dict) -> Any`

Make a PUT request.

**Parameters:**

- `endpoint` (str): API endpoint
- `data` (Dict): Request body

**Returns:**

- `Any`: JSON response

**Example:**

```python
updated = client.put("notes/note123", {"body": "Updated content"})
```

---

#### `delete(endpoint: str) -> Any`

Make a DELETE request.

**Parameters:**

- `endpoint` (str): API endpoint

**Returns:**

- `Any`: JSON response (typically empty)

**Example:**

```python
client.delete("notes/note123")
```

---

### Pagination

#### `get_paginated(endpoint: str, fields: Optional[List[str]] = None, **params) -> List[Dict]`

Fetch all items with automatic pagination.

**Parameters:**

- `endpoint` (str): API endpoint
- `fields` (List[str], optional): Fields to include
- `**params`: Additional query parameters

**Returns:**

- `List[Dict]`: All items from all pages

**Example:**

```python
# Get all notes
all_notes = client.get_paginated("notes", fields=["id", "title"])

# Get all tags
all_tags = client.get_paginated("tags")
```

---

## Common Patterns

### Basic Workflow

```python
# Initialize
dao = JoplinDAO(token="your_token")

# Create structure
library = dao.create_folder("Library")
authors = dao.create_folder("Authors", parent_id=library.id)

# Create content
note = dao.create_note(
    "Moby Dick Summary",
    body="A tale of obsession...",
    folder_id=authors.id
)

# Add tags
tag = dao.create_tag("classic")
dao.tag_note(note.id, tag.id)
```

---

### Working with Hierarchies

```python
# Get root folders
roots = dao.list_folders(root_only=True)

for root in roots:
    print(f"Root: {root.title}")
  
    # Get children
    children = dao.list_folders(parent_id=root.id)
    for child in children:
        path = dao.get_folder_path(child.id)
        print(f"  Path: {path}")
  
        # Get notes in folder
        notes = dao.list_notes(folder_id=child.id)
        print(f"    Notes: {len(notes)}")
```

---

### Bulk Operations

```python
# Find all notes with a tag
notes = dao.list_notes(tag_id="tag123")

# Move them all
moved = dao.move_notes(
    [n.id for n in notes],
    target_folder_id="archive_folder"
)

# Update multiple notes
for note in notes:
    dao.update_note(note.id, author="Updated")
```

---

### Search and Filter

```python
# Search for notes
results = dao.search_notes("moby dick")

# Filter by tag
for note in results:
    tags = dao.get_note_tags(note.id)
    if any(t.title == "classic" for t in tags):
        print(f"Classic: {note.title}")
```

---

### Integration with MML

JoplinDAO is designed to work with MML documents:

```python
from controllers.joplin_dao import JoplinDAO
from controllers.joplin_dom import MMLDOM

# Get note with MML content
dao = JoplinDAO(token="your_token")
note = dao.get_note("note123", fields=["id", "title", "body"])

# Parse as MML document
dom = MMLDOM().set_document(note.body)

# Manipulate
dom.where(type="summary").bulk_set_attributes(status="published")

# Save back
updated_body = dom.get_document()
dao.update_note(note.id, body=updated_body)
```

---

## Error Handling

### JoplinAPIError

General API error (network issues, invalid responses, etc.)

```python
from models.errors import JoplinAPIError

try:
    note = dao.get_note("invalid_id")
except JoplinAPIError as e:
    print(f"API error: {e}")
```

---

### JoplinNotFoundError

Specific 404 error when resource doesn't exist.

```python
from models.errors import JoplinNotFoundError

try:
    note = dao.get_note("nonexistent_id")
except JoplinNotFoundError as e:
    print(f"Not found: {e}")
```

---

## Debugging

### Viewing Cache State

The DAO `__repr__` method provides a visual tree of all folders, notes, and tags:

```python
dao = JoplinDAO(token="your_token")
print(repr(dao))
```

This outputs a colored tree structure showing the complete hierarchy.

**Note**: This method is slow (2+ seconds on first load) as it pulls everything and renders a complete tree.

---

### Testing Connection

```python
try:
    dao = JoplinDAO(token="your_token")
    folders = dao.list_folders(root_only=True)
    print(f"Connected! Found {len(folders)} root folders")
except JoplinAPIError as e:
    print(f"Connection failed: {e}")
```

---

### Manual Cache Control

```python
# Force refresh everything
dao.clear_cache()

# Access will now fetch fresh from API
folders = dao.list_folders()
```

---
