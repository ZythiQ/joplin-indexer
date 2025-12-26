# Joplin Indexing Tools

This project uses a Joplin workspace as a small database. Minimally represented `notes` / `folders` / `tags` are controlled via a DAO and API client pair and their markdown contents are structured and navigatable using JML, a comment-based markup language, which can be safely queried with a DOM.

## Requirements

* Joplin Desktop with the Web Clipper service enabled (REST API).
* Python dependencies: `requests` (used by the API client).

## Modules

* **JoplinClient** : REST client + port discovery + pagination.
* **JoplinDAO** : Cached database-like operations over `notes` / `folders` / `tags`.
* **JMLTree** : Parses and edits JML-tagged markdown into a `node` / `container` tree.
* **JMLDOM** : Query builder over a JMLTree (SQL-styled ops).
* **Data models** : `JNote`, `JFolder`, `JTag`, `JMLNode`.

---

# Usage Guide

## 1) API Client (JoplinClient)

### Create a client

* If the `base_url` is omitted, it discovers the local Joplin port by probing `41184–41194` via `/ping`.
* Discovery happens once per process unless you reset it.

```python
from controllers.joplin_client import JoplinClient

client = JoplinClient(token="YOUR_JOPLIN_TOKEN")  # auto-discovers base_url
# or:
client = JoplinClient(token="YOUR_JOPLIN_TOKEN", base_url="http://localhost:41184")
```

### Reset port discovery

```python
JoplinClient.reset_discovery()
```

### Basic requests

```python
note = client.get("notes/NOTE_ID")			# GET
created = client.post("notes", {"title": "X"})		# POST
updated = client.put("notes/NOTE_ID", {"title": "Y"})	# PUT
client.delete("notes/NOTE_ID")				# DELETE
```

---

## 2) DAO (JoplinDAO)

`JoplinDAO` builds and refreshes a lightweight cache (`notes` / `folders` / `tags` + indexes) with a TTL (default 5 minutes).

### Create DAO

```python
from controllers.joplin_dao import JoplinDAO

dao = JoplinDAO(token="YOUR_JOPLIN_TOKEN")
```

### Folders

```python
root_folders = dao.list_folders(root_only=True)
folder = dao.create_folder("Stories")
path = dao.get_folder_path(folder.id)
```

### Notes

```python
note = dao.create_note("Fire and Ice", body="...", folder_id=folder.id)
note = dao.update_note(note.id, body="updated")

notes_in_folder = dao.list_notes(folder_id=folder.id)
hits = dao.search_notes("Fire and Ice")

moved = dao.move_notes([note.id], target_folder_id="TARGET_FOLDER")
```

### Tags

```python
tag = dao.create_tag("fantasy")
dao.tag_note(note.id, tag.id)

notes_with_tag = dao.get_notes_with_tag(tag.id)
dao.untag_note(note.id, tag.id)
```

### Cache control

```python
dao.refresh_cache()  # force rebuild now
```

---

## 3) JML Document (JMLTree)

Joplin Markup Language is embedded in markdown using HTML-style comments with two constructs:

* containers: `<!-- container id="..." ... --> ... <!-- /container -->`
* nodes: `<!-- node id="..." ... --> ... <!-- /node -->`

Attributes are parsed from `key="value"` pairs.

### Example JML document

```md
<!-- container id="root" type="toc" -->
<!-- container id="c_abc12345" name="stuff" -->
<!-- node id="n_def67890" type="something" tag="it" -->
Some content...
<!-- /node -->
<!-- /container -->
<!-- /container -->
```

### Parse / edit / serialize

```python
from controllers.joplin_dom import JMLTree

tree = JMLTree(markdown_text)

cid = tree.create_container("root", name="stuff")
nid = tree.create_node("# Part 1", cid, type="something", tag="it")

tree.update_content(nid, "Updated content...")
new_markdown_text = tree.serialize()
```

(If you try to read / write content on a container, it raises an  `InvalidOperationError`.)

---

## 4) JML Document Object Manager (JMLDOM)

`JMLDOM` is a query-builder wrapper around a JML document: call `set_document()`, filter with `where*()`, then bulk edit / delete / move, and finally `get_document()` to serialize.

### Load and query

```python
from controllers.joplin_dom import JMLDOM

dom = JMLDOM().set_document(markdown)

parts = (
  dom.where(type="something")
     .where_in("tag", ["it", "bit", "git"])
     .get_ids()
)
```

### Bulk operations

```python
dom.set_document(markdown_text)

dom.where(type="something").bulk_set_attributes(series="Fire and Ice")

deleted = dom.where(type="draft").bulk_delete()
new_markdown_text = dom.get_document()
```

### Structural filters

* Restrict to descendants of a container (`where_container`).
* Filter by node type (`where_type`), e.g. `node` vs `container`.

---

## Errors (quick reference)

* `JoplinAPIError`, `JoplinNotFoundError` (client / REST).
* `InvalidOperationError` (e.g., treating a container like a node).
* `JMLNodeNotFoundError` (JML tree / DOM node lookups).

---
