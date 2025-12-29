# MML API Reference

**MML (Markdown Markup Language)** embeds structured metadata within markdown using HTML comments:

- **Containers**: `<!-- @c id="..." --> ... <!-- /@c -->`
- **Nodes**: `<!-- @n id="..." --> ... <!-- /@n -->`
- **Fragments**: `<!-- %identifier --> ... <!-- /%identifier -->`

**MMLDoc** parses and manages the document tree, while **MMLDOM** provides SQL-like query operations for filtering and bulk manipulation.

---

## MMLDoc

#### `MMLDoc(markdown: str)`

Initialize and parse a MML-tagged markdown document.

**Parameters:**

- `markdown` (str): MML-tagged markdown text to parse

**Example:**

```python
doc = MMLDoc("")
```

**Notes:**

- Automatically fixes malformed MML during deserialization
- Creates implicit root container if not present
- Removes empty nodes and wraps loose content
- Parses fragments into child nodes

---

### Document Serialization

#### `serialize() -> str`

Serialize the document tree back to MML-tagged markdown.

**Returns:**

- `str`: Complete markdown with MML tags

**Example:**

```python
markdown = doc.serialize()
```

---

### Node Creation

#### `create_container(parent_id: str, **attributes) -> str`

Create a new container node.

**Parameters:**

- `parent_id` (str): ID of parent container
- `**attributes`: Key-value pairs for node attributes

**Returns:**

- `str`: Generated container ID (format: `c_XXXXXXXX`)

**Example:**

```python
cid = doc.create_container("root", type="series", author="John")
```

**Raises:**

- `MMLNodeNotFoundError`: If parent doesn't exist

---

#### `create_node(content: str, parent_id: str, **attributes) -> str`

Create a new node with content.

**Parameters:**

- `content` (str): Markdown content for the node
- `parent_id` (str): ID of parent container
- `**attributes`: Key-value pairs for node attributes

**Returns:**

- `str`: Generated node ID (format: `n_XXXXXXXX`)

**Example:**

```python
nid = doc.create_node("# Title\n\nContent", "c_abc123", type="summary")
```

**Raises:**

- `MMLNodeNotFoundError`: If parent doesn't exist

---

### Reading Operations

#### `read_content(node_id: str) -> str`

Read the content of a node.

**Parameters:**

- `node_id` (str): Node ID

**Returns:**

- `str`: Node content (markdown text)

**Example:**

```python
content = doc.read_content("n_abc123")
```

**Raises:**

- `MMLNodeNotFoundError`: If node doesn't exist
- `InvalidOperationError`: If called on a container

---

#### `read_attribute(node_id: str, key: str, default=None) -> Any`

Read a single attribute value.

**Parameters:**

- `node_id` (str): Node ID
- `key` (str): Attribute key
- `default` (Any, optional): Default value if key doesn't exist

**Returns:**

- `Any`: Attribute value or default

**Example:**

```python
author = doc.read_attribute("n_abc123", "author", "Unknown")
```

**Raises:**

- `MMLNodeNotFoundError`: If node doesn't exist

---

#### `read_attributes(node_id: str) -> Dict[str, Any]`

Read all attributes from a node.

**Parameters:**

- `node_id` (str): Node ID

**Returns:**

- `Dict[str, Any]`: Copy of all attributes

**Example:**

```python
attrs = doc.read_attributes("n_abc123")
```

**Raises:**

- `MMLNodeNotFoundError`: If node doesn't exist

---

#### `read_children(container_id: str) -> List[str]`

Get list of child node IDs.

**Parameters:**

- `container_id` (str): Container ID

**Returns:**

- `List[str]`: List of child node IDs

**Example:**

```python
children = doc.read_children("c_abc123")
```

**Raises:**

- `MMLNodeNotFoundError`: If container doesn't exist

---

#### `read_parent(node_id: str) -> Optional[str]`

Get the parent node ID.

**Parameters:**

- `node_id` (str): Node ID

**Returns:**

- `Optional[str]`: Parent ID or `None` if root

**Example:**

```python
parent = doc.read_parent("n_abc123")
```

**Raises:**

- `MMLNodeNotFoundError`: If node doesn't exist

---

#### `read_type(node_id: str) -> str`

Get the node type as a string.

**Parameters:**

- `node_id` (str): Node ID

**Returns:**

- `str`: One of `"node"`, `"container"`, or `"fragment"`

**Example:**

```python
node_type = doc.read_type("n_abc123")
```

**Raises:**

- `MMLNodeNotFoundError`: If node doesn't exist

---

### Update Operations

#### `update_content(node_id: str, content: str) -> None`

Update node content.

**Parameters:**

- `node_id` (str): Node ID
- `content` (str): New markdown content

**Example:**

```python
doc.update_content("n_abc123", "Updated content")
```

**Raises:**

- `MMLNodeNotFoundError`: If node doesn't exist
- `InvalidOperationError`: If called on a container

---

#### `update_attribute(node_id: str, key: str, value: Any) -> None`

Update a single attribute.

**Parameters:**

- `node_id` (str): Node ID
- `key` (str): Attribute key
- `value` (Any): New value

**Example:**

```python
doc.update_attribute("n_abc123", "status", "published")
```

**Raises:**

- `MMLNodeNotFoundError`: If node doesn't exist

---

#### `update_attributes(node_id: str, **attributes) -> None`

Update multiple attributes at once.

**Parameters:**

- `node_id` (str): Node ID
- `**attributes`: Key-value pairs to update

**Example:**

```python
doc.update_attributes("n_abc123", author="Jane", status="draft")
```

**Raises:**

- `MMLNodeNotFoundError`: If node doesn't exist

---

### Fragment Operations

Fragments are aggregating snippets embedded within node content. They're parsed as child nodes of type `FRAGMENT` and can be updated independently via a shared id and the index.

#### `get_fragments(parent_id: str, identifier: Optional[str] = None) -> Dict[str, List[str]]`

Get all fragments from a node, optionally filtered by identifier.

**Parameters:**

- `parent_id` (str): Node ID containing fragments
- `identifier` (str, optional): Specific fragment identifier to retrieve

**Returns:**

- `Dict[str, List[str]]`: Dictionary mapping identifiers to lists of content strings

**Example:**

```python
# Get all fragments
all_frags = doc.get_fragments("n_abc123")
# {'genre': ['Sci-Fi', 'Mystery'], 'author': ['John']}

# Get specific fragment
genres = doc.get_fragments("n_abc123", "genre")
# {'genre': ['Sci-Fi', 'Mystery']}
```

**Raises:**

- `MMLNodeNotFoundError`: If parent doesn't exist

---

#### `update_fragment(parent_id: str, identifier: str, index: int, content: str) -> None`

Update a specific fragment occurrence.

**Parameters:**

- `parent_id` (str): Node ID containing the fragment
- `identifier` (str): Fragment identifier
- `index` (int): Zero-based index of the occurrence
- `content` (str): New content for this occurrence

**Example:**

```python
# Update the second occurrence of 'genre' fragment: Mystery -> Horror
doc.update_fragment("n_abc123", "genre", 1, "Horror")
```

**Raises:**

- `MMLNodeNotFoundError`: If parent or fragment doesn't exist
- `InvalidOperationError`: If index is out of bounds

**Notes:**

- Automatically updates the node content to reflect changes
- Index is zero-based (0 = first occurrence, 1 = second, etc.)

---

#### `generate_fragment_md(identifier: str, content: str) -> str`

Generate fragment markdown for manual insertion.

**Parameters:**

- `identifier` (str): Fragment identifier
- `content` (str): Fragment content

**Returns:**

- `str`: Formatted fragment markdown

**Example:**

```python
frag = doc.generate_fragment_md("author", "John Doe")
doc.update_content("n_abc123", f"Written by {frag}")
# Results in: "Written by <!-- %author -->John Doe<!-- /%author -->"
```

---

### Deletion Operations

#### `delete_node(node_id: str) -> None`

Delete a node and all its descendants.

**Parameters:**

- `node_id` (str): Node ID to delete

**Example:**

```python
doc.delete_node("n_abc123")
```

**Raises:**

- `MMLNodeNotFoundError`: If node doesn't exist

**Notes:**

- Recursively deletes all children
- Removes from parent's children list
- Removes from internal index

---

#### `delete_attribute(node_id: str, key: str) -> None`

Remove an attribute from a node.

**Parameters:**

- `node_id` (str): Node ID
- `key` (str): Attribute key to remove

**Example:**

```python
doc.delete_attribute("n_abc123", "draft")
```

**Raises:**

- `MMLNodeNotFoundError`: If node doesn't exist

**Notes:**

- Silent operation if key doesn't exist

---

### Tree Operations

#### `move_node(node_id: str, new_parent_id: str, position: int = -1) -> None`

Move a node to a different parent.

**Parameters:**

- `node_id` (str): Node to move
- `new_parent_id` (str): Target parent container
- `position` (int, optional): Index position in new parent's children (-1 = append)

**Example:**

```python
# Append to end
doc.move_node("n_abc123", "c_xyz789")

# Insert at specific position
doc.move_node("n_abc123", "c_xyz789", 0)
```

**Raises:**

- `MMLNodeNotFoundError`: If node or parent doesn't exist
- `InvalidOperationError`: If new parent is not a container

---

#### `sort_children(parent_id: str, key_func: Callable) -> None`

Sort a container's children using a key function.

**Parameters:**

- `parent_id` (str): Container ID
- `key_func` (Callable): Function taking `MMLNode` returning sort key

**Example:**

```python
# Sort by title attribute
doc.sort_children("c_abc123", lambda n: n.attributes.get('title', ''))
```

**Raises:**

- `MMLNodeNotFoundError`: If parent doesn't exist

---

### Utility Operations

#### `exists(node_id: str) -> bool`

Check if a node exists in the document.

**Parameters:**

- `node_id` (str): Node ID to check

**Returns:**

- `bool`: `True` if exists, `False` otherwise

**Example:**

```python
if doc.exists("n_abc123"):
    content = doc.read_content("n_abc123")
```

---

#### `get_node_ids() -> List[str]`

Get all node IDs in the document.

**Returns:**

- `List[str]`: All node IDs including root

**Example:**

```python
all_ids = doc.get_node_ids()
```

---

#### `get_all_descendants(container_id: str) -> List[str]`

Get all descendant node IDs recursively.

**Parameters:**

- `container_id` (str): Container ID

**Returns:**

- `List[str]`: List of all descendant IDs

**Example:**

```python
descendants = doc.get_all_descendants("c_abc123")
```

**Notes:**

- Returns empty list if container doesn't exist
- Includes all nested descendants, not just direct children

---

## MMLDOM

#### `MMLDOM()`

Initialize an empty query builder.

**Example:**

```python
dom = MMLDOM()
```

---

### Document Management

#### `set_document(markdown: str) -> MMLDOM`

Load and parse a markdown document for querying.

**Parameters:**

- `markdown` (str): MML-tagged markdown text

**Returns:**

- `MMLDOM`: Self for chaining

**Example:**

```python
dom = MMLDOM().set_document(markdown_text)
```

**Notes:**

- Creates a new `MMLDoc` instance internally

---

#### `get_document() -> str`

Serialize the current document back to markdown.

**Returns:**

- `str`: MML-tagged markdown

**Example:**

```python
updated_markdown = dom.get_document()
```

**Raises:**

- `InvalidOperationError`: If no document is loaded

---

### Query Filters

All `where*` methods return a new `MMLDOM` instance with filtered results, enabling method chaining.

#### `where(**attributes) -> MMLDOM`

Filter nodes by exact attribute matches.

**Parameters:**

- `**attributes`: Key-value pairs to match

**Returns:**

- `MMLDOM`: New instance with filtered results

**Example:**

```python
# Find all nodes with type="summary" and author="John"
results = dom.where(type="summary", author="John")
```

---

#### `where_in(key: str, values: list) -> MMLDOM`

Filter nodes where attribute is in a list of values.

**Parameters:**

- `key` (str): Attribute key
- `values` (list): List of acceptable values

**Returns:**

- `MMLDOM`: New instance with filtered results

**Example:**

```python
# Find nodes with category in ['short', 'series']
results = dom.where_in("category", ["short", "series"])
```

---

#### `where_contains(key: str, substring: str) -> MMLDOM`

Filter nodes where attribute contains a substring.

**Parameters:**

- `key` (str): Attribute key
- `substring` (str): Substring to search for

**Returns:**

- `MMLDOM`: New instance with filtered results

**Example:**

```python
# Find nodes where title contains "Fire"
results = dom.where_contains("title", "Fire")
```

---

#### `where_container(container_id: str, recursive: bool = True) -> MMLDOM`

Filter to descendants of a specific container.

**Parameters:**

- `container_id` (str): Container ID
- `recursive` (bool, optional): Include nested descendants (default: `True`)

**Returns:**

- `MMLDOM`: New instance with filtered results

**Example:**

```python
# Get all descendants
results = dom.where_container("c_abc123")

# Get only direct children
results = dom.where_container("c_abc123", recursive=False)
```

---

#### `where_type(node_type: str) -> MMLDOM`

Filter nodes by type.

**Parameters:**

- `node_type` (str): Either `"node"` or `"container"`

**Returns:**

- `MMLDOM`: New instance with filtered results

**Example:**

```python
# Get only content nodes
nodes = dom.where_type("node")

# Get only containers
containers = dom.where_type("container")
```

**Notes:**

- Fragments cannot be queried directly as they don't have a globally unique id; use `where_has_fragment()` instead

---

#### `where_has_fragment(identifier: str) -> MMLDOM`

Filter to nodes containing fragments with a specific identifier.

**Parameters:**

- `identifier` (str): Fragment identifier to search for

**Returns:**

- `MMLDOM`: New instance with filtered results

**Example:**

```python
# Find nodes with 'genre' fragments
results = dom.where_has_fragment("genre")
```

---

#### `where_lambda(func: Callable[[str, Dict[str, Any]], bool]) -> MMLDOM`

Filter using a custom function.

**Parameters:**

- `func` (Callable): Function taking `(node_id, attributes)` returning bool

**Returns:**

- `MMLDOM`: New instance with filtered results

**Example:**

```python
# Find nodes with title starting with 'The'
results = dom.where_lambda(
    lambda id, attrs: attrs.get('title', '').startswith('The')
)
```

---

#### `where_not(*node_ids: str) -> MMLDOM`

Exclude specific nodes from results.

**Parameters:**

- `*node_ids` (str): Node IDs to exclude

**Returns:**

- `MMLDOM`: New instance with filtered results

**Example:**

```python
# Exclude specific nodes
results = dom.where(type="summary").where_not("n_abc123", "n_xyz789")
```

---

### Chaining Example

```python
# Complex query with multiple filters
results = (
    dom.where(type="summary")
       .where_in("category", ["short", "series"])
       .where_container("c_author_john")
       .where_has_fragment("sequel")
       .where_not("n_draft_123")
)
```

---

### Bulk Operations

#### `bulk_set_attributes(**attributes) -> MMLDOM`

Set attributes on all matched nodes.

**Parameters:**

- `**attributes`: Key-value pairs to set

**Returns:**

- `MMLDOM`: Self for chaining

**Example:**

```python
dom.where(type="draft").bulk_set_attributes(status="published", published_date="2025-01-01")
```

---

#### `bulk_set_content(transformer: Callable[[str, Dict[str, Any]], str]) -> MMLDOM`

Transform content of all matched nodes.

**Parameters:**

- `transformer` (Callable): Function taking `(content, attributes)` returning new content

**Returns:**

- `MMLDOM`: Self for chaining

**Example:**

```python
# Prepend a header to all summaries
dom.where(type="summary").bulk_set_content(
    lambda content, attrs: f"# {attrs.get('title', 'Untitled')}\n\n{content}"
)
```

**Notes:**

- Only operates on nodes of type `"node"`, skips containers which cannot hold content

---

#### `bulk_delete() -> int`

Delete all matched nodes.

**Returns:**

- `int`: Number of nodes deleted

**Example:**

```python
deleted = dom.where(status="archived").bulk_delete()
print(f"Deleted {deleted} nodes")
```

---

#### `bulk_move(container_id: str) -> MMLDOM`

Move all matched nodes to a container.

**Parameters:**

- `container_id` (str): Target container ID

**Returns:**

- `MMLDOM`: Self for chaining

**Example:**

```python
dom.where(status="approved").bulk_move("c_published")
```

---

#### `sort_parents_children(key: str, reverse: bool = False) -> MMLDOM`

Sort matched nodes within their parent containers by attribute.

**Parameters:**

- `key` (str): Attribute key to sort by
- `reverse` (bool, optional): Sort descending (default: `False`)

**Returns:**

- `MMLDOM`: Self for chaining

**Example:**

```python
# Sort all summaries by title within their parent containers
dom.where(type="summary").sort_parents_children("title")

# Sort descending
dom.where(type="summary").sort_parents_children("date", reverse=True)
```

---

### Direct Node Operations

These methods operate on individual nodes through the DOM interface.

#### `create_container(parent_id: str, **attributes) -> str`

Create a container in the loaded document.

**Parameters:**

- `parent_id` (str): Parent container ID
- `**attributes`: Node attributes

**Returns:**

- `str`: Generated container ID

**Example:**

```python
cid = dom.create_container("root", type="series", author="John")
```

---

#### `create_node(content: str, parent_id: str, **attributes) -> str`

Create a node in the loaded document.

**Parameters:**

- `content` (str): Node content
- `parent_id` (str): Parent container ID
- `**attributes`: Node attributes

**Returns:**

- `str`: Generated node ID

**Example:**

```python
nid = dom.create_node("Content", "c_abc123", type="summary")
```

---

#### `get_content(node_id: str) -> str`

Read node content.

**Parameters:**

- `node_id` (str): Node ID

**Returns:**

- `str`: Node content

---

#### `read_attributes(node_id: str) -> Dict[str, Any]`

Read all node attributes.

**Parameters:**

- `node_id` (str): Node ID

**Returns:**

- `Dict[str, Any]`: Node attributes

---

#### `read_attribute(node_id: str, key: str, default=None) -> Any`

Read single attribute.

**Parameters:**

- `node_id` (str): Node ID
- `key` (str): Attribute key
- `default` (Any, optional): Default if not found

**Returns:**

- `Any`: Attribute value

---

#### `read_children(node_id: str) -> List[str]`

Read child IDs.

**Parameters:**

- `node_id` (str): Node ID

**Returns:**

- `List[str]`: Child node IDs

---

#### `set_content(node_id: str, content: str) -> None`

Update node content.

**Parameters:**

- `node_id` (str): Node ID
- `content` (str): New content

---

#### `set_attributes(node_id: str, **attributes) -> None`

Update node attributes.

**Parameters:**

- `node_id` (str): Node ID
- `**attributes`: Attributes to update

---

#### `set_attribute(node_id: str, key: str, value: Any) -> None`

Update single attribute.

**Parameters:**

- `node_id` (str): Node ID
- `key` (str): Attribute key
- `value` (Any): New value

---

#### `get_fragments(parent_id: str, identifier: Optional[str] = None) -> Dict[str, List[str]]`

Get fragments from a node.

**Parameters:**

- `parent_id` (str): Node ID
- `identifier` (str, optional): Specific fragment ID

**Returns:**

- `Dict[str, List[str]]`: Fragment data

---

#### `update_fragment(parent_id: str, identifier: str, index: int, content: str) -> None`

Update fragment content.

**Parameters:**

- `parent_id` (str): Node ID
- `identifier` (str): Fragment ID
- `index` (int): Occurrence index
- `content` (str): New content

---

#### `delete_attribute(node_id: str, key: str) -> None`

Remove attribute from node.

**Parameters:**

- `node_id` (str): Node ID
- `key` (str): Attribute key

---

#### `move(node_id: str, new_parent_id: str, position: int = -1) -> None`

Move node to different parent.

**Parameters:**

- `node_id` (str): Node to move
- `new_parent_id` (str): Target parent
- `position` (int, optional): Position in children

---

#### `delete(node_id: str) -> None`

Delete a node and descendants.

**Parameters:**

- `node_id` (str): Node to delete

---

#### `generate_fragment(identifier: str, content: str) -> str`

Generate fragment markdown.

**Parameters:**

- `identifier` (str): Fragment ID
- `content` (str): Fragment content

**Returns:**

- `str`: Fragment markdown

---

### Result Retrieval

#### `get_ids() -> List[str]`

Get list of matched node IDs.

**Returns:**

- `List[str]`: Node IDs

**Example:**

```python
ids = dom.where(type="summary").get_ids()
```

---

#### `get_count() -> int`

Count matched nodes.

**Returns:**

- `int`: Number of matches

**Example:**

```python
count = dom.where(status="draft").get_count()
```

---

#### `get_first() -> Optional[str]`

Get first matched node ID.

**Returns:**

- `Optional[str]`: First node ID or `None`

**Example:**

```python
first = dom.where(type="toc").get_first()
```

---

#### `get_at(index: int) -> Optional[str]`

Get node ID at specific index.

**Parameters:**

- `index` (int): Zero-based index

**Returns:**

- `Optional[str]`: Node ID or `None`

**Example:**

```python
second = dom.where(type="summary").get_at(1)
```

---

#### `has_results() -> bool`

Check if any matches exist.

**Returns:**

- `bool`: True if results exist

**Example:**

```python
if dom.where(status="draft").has_results():
    print("Drafts found")
```

---

#### `each(func: Callable[[str], None]) -> MMLDOM`

Execute function for each matched node.

**Parameters:**

- `func` (Callable): Function taking node ID

**Returns:**

- `MMLDOM`: Self for chaining

**Example:**

```python
dom.where(type="summary").each(lambda id: print(f"Found: {id}"))
```

---

## Common Patterns

### Loading and Querying

```python
# Load document and query
dom = MMLDOM().set_document(markdown_text)
summaries = dom.where(type="summary").get_ids()

# Process results
for node_id in summaries:
    title = dom.read_attribute(node_id, "title")
    content = dom.get_content(node_id)
    print(f"{title}: {content[:50]}")
```

---

### Complex Filtering

```python
# Chain multiple filters
results = (
    dom.where(type="summary")
       .where_container("c_author_john")
       .where_in("category", ["short", "series"])
       .where_has_fragment("sequel")
)
```

---

### Bulk Updates

```python
# Update multiple nodes at once
dom.where(status="draft").bulk_set_attributes(
    status="published",
    published_date="2025-01-01"
)

# Transform content
dom.where(type="summary").bulk_set_content(
    lambda content, attrs: content.upper()
)

# Save changes
updated = dom.get_document()
```

---

### Working with Fragments

```python
# Add fragment to node
frag = dom.generate_fragment("genre", "Sci-Fi")
dom.set_content("n_abc123", f"A {frag} story")

# Update specific occurrence
dom.update_fragment("n_abc123", "genre", 0, "Horror")

# Read all fragments
fragments = dom.get_fragments("n_abc123")
# {'genre': ['Horror']}
```

---

### Reorganizing Structure

```python
# Move nodes to new container
approved = dom.where(status="approved").get_ids()
dom.bulk_move("c_published")

# Sort children
dom.where_container("c_authors").sort_parents_children("title")

# Delete old drafts
deleted = dom.where(status="archived").bulk_delete()
```

---

## Error Handling

### MMLNodeNotFoundError

Raised when attempting to access a node that doesn't exist.

```python
try:
    content = doc.read_content("n_invalid")
except MMLNodeNotFoundError as e:
    print(f"Node not found: {e}")
```

---

### InvalidOperationError

Raised when attempting an invalid operation (e.g., reading content from a container).

```python
try:
    content = doc.read_content("c_container123")
except InvalidOperationError as e:
    print(f"Invalid operation: {e}")
```
