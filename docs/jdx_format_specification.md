# JDX Format Specification

The **JoplinIndexer** is a high-level interface that combines the JoplinDAO (for Joplin API operations) and MMLDOM (for MML document manipulation) to manage a structured library of stories in a specific format.

## Story Data Model

Each story contains:

- **Title** - Story title
- **Author** - Author name
- **Author URL** - Link to author's website (defaults to "#" if unavailable)
- **Description** - Text description (single for shorts/series, list for anthology volumes)
- **Genres** - List of genre tags (1-N genres)
- **Category** - One of: `short`, `series`, `anthology`
- **Parts/Volumes** - Story content, which can be:
  - Single note (for shorts)
  - Multiple sequentially numbered parts (for series)
  - Multiple sequentially numbered volumes (for anthologies)
- **Optional Relations** - Links to related stories (prequel, sequel, etc.)

## Physical Organization (Joplin Folders)

```
/Library/
├── {Author Name}/
│   ├── Shorts/
│   │   ├── {Short Title}
│   │   └── {Short Title}
│   ├── {Series Title}/
│   │   ├── {Title}: Part 1
│   │   ├── {Title}: Part 2
│   │   └── {Title}: Part 3
│   └── {Anthology Title}/
│       ├── {Title}: Volume 1
│       └── {Title}: Volume 2
```

**Key rules:**

- All stories under `/Library` folder
- Organized by author name, then story title
- Exception: Shorts go under author's `/Shorts` subfolder instead of their own title folder
- Note titles use title case with ": Part N" or ": Volume N" suffix for multi-part works

## Logical Structure (MML Format)

### Story Notes

Each story note (short, part, or volume) contains 3 nodes:

1. **Header** (`type="peer.header"`) - Navigation header with links
2. **Body** (`type="peer.body"`) - Actual story content
3. **Footer** (`type="peer.footer"`) - Navigation footer (mirrors header)

**Fragments** in header/footer nodes:

- `num` - "Short", "Part N", or "Vol N"
- `index` - Link to table of contents note
- `prev` - Link to previous part (if exists)
- `next` - Link to next part (if exists)

### Table of Contents Note

Single note with hierarchical structure:

```
Root Container
├── Misc Node (human-editable, system doesn't touch)
└── TOC Container
    ├── Author Container (alphabetized, 3+ stories)
    │   ├── Delimiter Node (author heading)
    │   ├── Shorts Category Container
    │   │   ├── Delimiter Node (category heading)
    │   │   └── Summary Nodes (alphabetized by title)
    │   ├── Series Category Container
    │   │   └── ...
    │   └── Anthologies Category Container
    │       └── ...
    └── "Uncategorized" Author Container (authors with <3 stories)
        └── Summary Nodes
```

**Summary node fragments:**

- `title` - Link to story's first part
- `author` - Link to author website
- `relate` - Optional link to related story (prequel/sequel)
- `links` - All parts/volumes (for series/anthologies)
- `genre` - Genre tags (multiple occurrences)
- `desc` - Description(s) (one for shorts/series, multiple for anthology volumes)

## Key Operations Needed

The indexer should provide CRUD operations for stories:

1. **Create Story** - Add new story with all parts, create folder structure, update TOC
2. **Read Story** - Retrieve story metadata and content from notes
3. **Update Story** - Modify content, metadata, add/remove parts, maintain navigation links
4. **Delete Story** - Remove all notes and folders, clean up TOC

## Automatic Maintenance

The indexer must automatically:

- Generate and update navigation links (prev/next/index) when parts change
- Maintain TOC structure with proper:
  - Alphabetical ordering (authors and titles within categories)
  - Author grouping (3+ stories threshold for dedicated section)
  - Category ordering (fixed: Shorts, Series, Anthologies)
- Generate proper MML format for all notes
- Keep Joplin folder structure synchronized
