# Joplin Indexing Tools

This project uses a Joplin workspace as a small database. Minimally represented `notes` / `folders` / `tags` are controlled via a DAO and API client pair and their markdown contents are structured and navigatable using JML, a comment-based markup language, which can be safely queried with a DOM.

## Requirements

* Joplin Desktop with the Web Clipper service enabled (REST API).
* Python dependencies: `requests` (used by the API client).

## Modules

* **JoplinClient** : REST client + port discovery + pagination.
* **JoplinDAO** : Cached database-like operations over `notes` / `folders` / `tags`.
* **JMLDoc** : Parses and edits JML-tagged markdown into a `node` / `container` tree document.
* **JMLDOM** : Query builder over a JMLDoc (SQL-styled ops).
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

## 3) JML Document (JMLDoc)

Joplin Markup Language is embedded in markdown using HTML-style comments with two constructs:

* containers: `<!-- container id="..." ... --> ... <!-- /container -->`
* nodes: `<!-- node id="..." ... --> ... <!-- /node -->`

Attributes are parsed from `key="value"` pairs. Malformed JML will be autofixed during deserialization. This will remove empty nodes, wrap loose markdown content, and move all nodes into a root container.

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
from controllers.joplin_dom import JMLDoc

doc = JMLDoc(markdown_text)

cid = doc.create_container("root", name="stuff")
nid = doc.create_node("Fire and Ice", cid, type="something", tag="it")

doc.update_content(nid, "Updated content...")
new_markdown_text = doc.serialize()
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

### Render the tree after deserializing

```python
dom = JMLDOM()
dom.set_document(markdown)
print(repr(dom))
```

#### Example Output

```powershell
root/
├── [C] c_b3e18bcd {'author': 'John'}
│   ├── (N) n_82dcc4d8 [13 chars: "--- ## [John]"]
│   ├── [C] c_66ff3471 {'type': 'shorts', 'author': 'John'}
│   │   ├── (N) n_77050bff [16 chars: "--- ### [Shorts]"]
│   │   ├── (N) n_3eb8ad5e {'type': 'summary', 'author': 'John', 'kind': 'short'} [204 chars: "#### **Deep Sea Post..."]
│   │   ├── (N) n_54e94cef {'type': 'summary', 'author': 'John', 'kind': 'short'} [188 chars: "#### **Borrowed Grav..."]
│   │   └── (N) n_5fa1c395 {'type': 'summary', 'author': 'John', 'kind': 'short'} [177 chars: "#### **The Quiet Sta..."]
│   │   
│   └── [C] c_032fb238 {'type': 'series', 'author': 'John'}
│       ├── (N) n_10b88dee [16 chars: "--- ### [Series]"]
│       ├── (N) n_b9664b68 {'type': 'summary', 'author': 'John', 'kind': 'series'} [218 chars: "#### **Lantern Distr..."]
│       └── (N) n_fda63c3a {'type': 'summary', 'author': 'John', 'kind': 'series'} [179 chars: "#### **Midnight Tran..."]
│   
└── [C] c_384a733a {'author': 'Hasmov'}
    ├── (N) n_6bac7e3b [13 chars: "--- ## [Hasmov]"]
    ├── [C] c_5a9aefee {'type': 'shorts', 'author': 'Hasmov'}
    │   ├── (N) n_324f2694 [16 chars: "--- ### [Shorts]"]
    │   ├── (N) n_55879353 {'type': 'summary', 'author': 'Hasmov', 'kind': 'short'} [207 chars: "#### **Echo Orchard*..."]
    │   └── (N) n_ddfd3094 {'type': 'summary', 'author': 'Hasmov', 'kind': 'short'} [170 chars: "#### **Spare Teeth**..."]
    │   
    └── [C] c_b46ad5be {'type': 'series', 'author': 'Hasmov'}
        ├── (N) n_497e5cb3 [16 chars: "--- ### [Series]"]
        ├── (N) n_f9ef0b5d {'type': 'summary', 'author': 'Hasmov', 'kind': 'series'} [202 chars: "#### **Salt & Thunde..."]
        ├── (N) n_edfdaf66 {'type': 'summary', 'author': 'Hasmov', 'kind': 'series'} [186 chars: "#### **Glass Rivers*..."]
        └── (N) n_8860a513 {'type': 'summary', 'author': 'Hasmov', 'kind': 'series'} [173 chars: "#### **Ash Choir** \..."]
```

---

## Errors (quick reference)

* `JoplinAPIError`, `JoplinNotFoundError` (client / REST).
* `InvalidOperationError` (e.g., treating a container like a node).
* `JMLNodeNotFoundError` (JML document / DOM node lookups).

---
