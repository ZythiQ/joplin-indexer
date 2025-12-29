# JDX Format Specification

## Overview

This document defines the JDX format built atop the Markdown Markup Language (MML) for story notes and table of contents structures. MML uses HTML comment syntax to embed structured metadata within Markdown documents using containers (`@c`), nodes (`@n`), and fragments (`%`).

## Core MML Constructs

### Containers

```
<!-- @c id="..." type="..." [attributes...] -->
  ...content...
<!-- /@c -->
```

### Nodes

```
<!-- @n id="..." type="..." [attributes...] -->
  ...content...
<!-- /@n -->
```

### Fragments

```
<!-- %fragment_id -->content<!-- /%fragment_id -->
```

Fragments allow targeted access to specific content within nodes. Multiple occurrences of the same fragment ID within a node are indexed as a tuple.

---

## Story Note Format

Story notes represent individual stories or parts of a series/anthology. Each note contains three nodes: header, body, and footer.

### Categories

- `short` - Standalone short stories
- `series` - Multi-part stories (use "Part N" numbering)
- `anthology` - Multi-volume collections (use "Vol N" numbering)

### Structure

```
<!-- @c id="root" type="root" -->
  <!-- @n id="..." type="peer.header" category="..." -->
    [header content]
  <!-- /@n -->
  <!-- @n id="..." type="peer.body" category="..." -->
    [story content]
  <!-- /@n -->
  <!-- @n id="..." type="peer.footer" category="..." -->
    [footer content]
  <!-- /@n -->
<!-- /@c -->
```

### Node Types

- `peer.header` - Contains navigation header
- `peer.body` - Contains the actual story content
- `peer.footer` - Contains navigation footer

### Header/Footer Format

#### Short Stories

```
<!-- @n id="..." type="peer.header" category="short" -->
---
## **<!-- %num -->Short<!-- /%num -->** \[ <!-- %index -->[Index](:/index_id)<!-- /%index --> \]
---
•••
<!-- /@n -->
```

```
<!-- @n id="..." type="peer.footer" category="short" -->
•••

---
## **\[ End \]** \[ <!-- %index -->[Index](:/index_id)<!-- /%index --> \]
---
<!-- /@n -->
```

#### Series - First Part

```
<!-- @n id="..." type="peer.header" category="series" -->
---
## **<!-- %num -->Part 1<!-- /%num -->** [ <!-- %index -->[Index](:/index_id)<!-- /%index --> | <!-- %next -->[Next](:/next_part_id)<!-- /%next --> ]
---
•••
<!-- /@n -->
```

Footer uses identical format with matching fragments.

#### Series - Middle Part

```
<!-- @n id="..." type="peer.header" category="series" -->
---
## **<!-- %num -->Part N<!-- /%num -->** [ <!-- %index -->[Index](:/index_id)<!-- /%index --> | <!-- %prev -->[Prev](:/prev_part_id)<!-- /%prev --> | <!-- %next -->[Next](:/next_part_id)<!-- /%next --> ]
---
•••
<!-- /@n -->
```

#### Series - Final Part

```
<!-- @n id="..." type="peer.header" category="series" -->
---
## **<!-- %num -->Part N<!-- /%num -->** [ <!-- %index -->[Index](:/index_id)<!-- /%index --> | <!-- %prev -->[Prev](:/prev_part_id)<!-- /%prev --> ] (Final)
---
•••
<!-- /@n -->
```

Footer omits "(Final)" marker but otherwise matches.

#### Anthology

Identical to series format, but use "Vol N" instead of "Part N" in the `num` fragment.

### Note Fragments

| Fragment  | Description                                | Example                          |
| --------- | ------------------------------------------ | -------------------------------- |
| `num`   | Part/volume number or "Short"              | `Part 1`, `Vol 3`, `Short` |
| `index` | Full markdown link to table of contents    | `[Index](:/9bbc...)`           |
| `next`  | Full markdown link to next part/volume     | `[Next](:/0ccb...)`            |
| `prev`  | Full markdown link to previous part/volume | `[Prev](:/6b58...)`            |

**Important**: Header and footer nodes use identical fragment IDs, resulting in two occurrences of each fragment per note that do not collide as they are in different parent nodes.

---

## Table of Contents Format

The table of contents aggregates all stories with metadata and navigation links.

### Overall Structure

```
<!-- @c id="root" type="root" -->
  <!-- @n id="..." type="index.misc" -->
    [Human-editable content - system does not touch]
  <!-- /@n -->
  
  <!-- @c id="..." type="index.toc" -->
    <!-- @c id="..." type="index.toc.author" name="Author Name" -->
      <!-- @n id="..." type="label" -->
      ---
      ## [Author Name]
      <!-- /@n -->
  
      <!-- @c id="..." type="index.toc.category" name="Shorts" -->
        <!-- @n id="..." type="label" -->
        ---
        ### [Shorts]
        <!-- /@n -->
        [Short story summaries]
      <!-- /@c -->
  
      <!-- @c id="..." type="index.toc.category" name="Series" -->
        <!-- @n id="..." type="label" -->
        ---
        ### [Series]
        <!-- /@n -->
        [Series summaries]
      <!-- /@c -->
  
      <!-- @c id="..." type="index.toc.category" name="Anthologies" -->
        <!-- @n id="..." type="label" -->
        ---
        ### [Anthologies]
        <!-- /@n -->
        [Anthology summaries]
      <!-- /@c -->
    <!-- /@c -->
  
    <!-- @c id="..." type="index.toc.author" name="Uncategorized" -->
      <!-- @n id="..." type="label" -->
      ---
      ## [Uncategorized]
      <!-- /@n -->
      [Authors with fewer than 3 stories]
    <!-- /@c -->
  <!-- /@c -->
<!-- /@c -->
```

### Hierarchy Rules

1. **Root container** (`type="root"`)
1. **Misc node** (`type="index.misc"`) - Reserved for human editing, not touched by automation
1. **TOC container** (`type="index.toc"`) - Contains all story summaries
1. **Author containers** (`type="index.toc.author"`) - One per author with 3+ stories

   * Alphabetized by author name
   * Special "Uncategorized" container for authors with <3 stories
   * Each author container begins with a **delimiter node** containing the author heading
1. **Category containers** (`type="index.toc.category"`) - One per category if author has stories of that type

   * Categories appear in fixed order: Shorts, Series, Anthologies
   * Not alphabetized
   * Each category container begins with a **delimiter node** containing the category heading
1. **Summary nodes** (`type="index.toc.summary"`) - One per story

   * Alphabetized by story title within each category

### Delimiter Nodes

Delimiter nodes provide visual separation between sections in the table of contents. They contain only header text wrapped in horizontal rules and have no explicit type attribute.

#### Author Delimiter

```
<!-- @n id="..." type="label" -->
---
## [Author Name]
<!-- /@n -->
```

Appears as the first child of each author container (identified by `author` attribute). Uses level-2 heading (`##`).

#### Category Delimiter

```
<!-- @n id="..." type="label" -->
---
### [Category Name]
<!-- /@n -->
```

Appears as the first child of each category container (`type="shorts"`, `type="series"`, or `type="anthologies"`). Uses level-3 heading (`###`). Category name will be one of: "Shorts", "Series", or "Anthologies".

### Summary Node Format

#### Short Story Summary

```
<!-- @n id="..." type="index.toc.summary" author="Author Name" category="short" -->
#### **<!-- %title -->[Story Title](:/first_part_id)<!-- /%title --> \[<!-- %author -->[Author Name](author_url)<!-- /%author -->\] | <!-- %relate -->[Prequel](:/prequel_id)<!-- /%relate -->**

- **Summary:** <!-- %genre -->[Genre 1](#)<!-- /%genre -->, <!-- %genre -->[Genre 2](#)<!-- /%genre -->, <!-- %genre -->[Genre 3](#)<!-- /%genre -->, <!-- %genre -->[Genre 4](#)<!-- /%genre -->
    - <!-- %desc -->Description here.<!-- /%desc -->
  
        •••
<!-- /@n -->
```

**Note**: The related story link (`relate` fragment) and its preceding " | " are optional and should be omitted if no relation exists.

#### Series Summary

```
<!-- @n id="..." type="index.toc.summary" author="Author Name" category="series" -->
#### **<!-- %title -->[Story Title](:/first_part_id)<!-- /%title --> \[<!-- %author -->[Author Name](author_url)<!-- /%author -->\] | <!-- %relate -->[Sequel](:/sequel_first_part_id)<!-- /%relate -->** (5)

- **All:** \[ <!-- %links -->[1](:/part_id)<!-- /%links --> | <!-- %links -->[2](:/part_id)<!-- /%links --> | <!-- %links -->[3](:/part_id)<!-- /%links --> | <!-- %links -->[4](:/part_id)<!-- /%links --> | <!-- %links -->[5](:/part_id)<!-- /%links --> \]
- **Summary:** <!-- %genre -->[Genre 1](#)<!-- /%genre -->, <!-- %genre -->[Genre 2](#)<!-- /%genre -->, <!-- %genre -->[Genre 3](#)<!-- /%genre -->, <!-- %genre -->[Genre 4](#)<!-- /%genre -->
    - <!-- %desc -->Description here.<!-- /%desc -->
  
        •••
<!-- /@n -->
```

The number in parentheses after the title indicates the total number of parts.

#### Anthology Summary

```
<!-- @n id="..." type="index.toc.summary" author="Author Name" category="anthology" -->
#### **<!-- %title -->[Story Title](:/first_volume_id)<!-- /%title --> \[<!-- %author -->[Author Name](author_url)<!-- /%author -->\] | <!-- %relate -->[Sequel](:/sequel_first_volume_id)<!-- /%relate -->** (5)

- **All:** \[ <!-- %links -->[1](:/volume_id)<!-- /%links --> | <!-- %links -->[2](:/volume_id)<!-- /%links --> | <!-- %links -->[3](:/volume_id)<!-- /%links --> | <!-- %links -->[4](:/volume_id)<!-- /%links --> | <!-- %links -->[5](:/volume_id)<!-- /%links --> \]
- **Summary:** <!-- %genre -->[Genre 1](#)<!-- /%genre -->, <!-- %genre -->[Genre 2](#)<!-- /%genre -->, <!-- %genre -->[Genre 3](#)<!-- /%genre -->, <!-- %genre -->[Genre 4](#)<!-- /%genre -->
    1.  <!-- %desc -->Description for volume 1 here.<!-- /%desc -->
    2.  <!-- %desc -->Description for volume 2 here.<!-- /%desc -->
  
        •••
<!-- /@n -->
```

**Key difference**: Anthology descriptions use numbered list format, with one description per volume.

### Summary Node Attributes

- `author` - Author name (used for organizational purposes)
- `category` - One of: `short`, `series`, `anthology`

### TOC Fragments

| Fragment   | Description                         | Example                                 | Occurrences                  |
| ---------- | ----------------------------------- | --------------------------------------- | ---------------------------- |
| `title`  | Full markdown link to story         | `[Story Title](:/id)`                 | 1                            |
| `author` | Full markdown link to author page   | `[Author Name](url)`                  | 1                            |
| `relate` | Full markdown link to related story | `[Prequel](:/id)`, `[Sequel](:/id)` | 0-1                          |
| `links`  | Full markdown link to part/volume   | `[1](:/id)`                           | N (one per part/volume)      |
| `genre`  | Full markdown link to genre tag     | `[Genre Name](#)`                     | 1-N                          |
| `desc`   | Description text (not a link)       | `Description text here.`              | 1-N (anthology has multiple) |
