from models.joplin_errors import JMLNodeNotFoundError, InvalidOperationError
from models.joplin_data import JMLNode

from typing import Dict, List, Optional, Any, Callable
import secrets
import re


class JMLDoc:
    """
    Joplin Markup Language parser and document tree manager.
    """

    _TAG_NODE = 'node'
    _TAG_CONTAINER = 'container'

    _ATTRIBUTE_RE = re.compile(r'(\w+)="([^"]*)"')

    _NODE_RE = re.compile(rf'<!-- {_TAG_NODE} id="([^"]+)"(.*?)-->')
    _NODE_END_RE = re.compile(rf'<!-- /{_TAG_NODE} -->')

    _CONTAINER_RE = re.compile(rf'<!-- {_TAG_CONTAINER} id="([^"]+)"(.*?)-->')
    _CONTAINER_END_RE = re.compile(rf'<!-- /{_TAG_CONTAINER} -->')


    def __init__(self, markdown: str):
        """
        Initialize tree by parsing JML markdown.
        """
        self._root = JMLNode(id='root', type='container', content='', attributes={'type': 'root'})
        self._idx: Dict[str, JMLNode] = {'root': self._root}
        if markdown: self._deserialize(markdown)


    def _create_id(self, prefix: str) -> str:
        """
        Generate a unique ID.
        """
        while True:
            new_id = f"{prefix or 'x'}_{secrets.token_hex(4)}"
            if new_id not in self._idx: return new_id


    def _deserialize_attributes(self, attrs_str: str) -> Dict[str, Any]:
        """
        Parse an attribute string.
        """
        attrs = {}
        if not attrs_str:
            return attrs

        for match in self._ATTRIBUTE_RE.finditer(attrs_str):
            key, value = match.groups()
            attrs[key] = value

        return attrs
    

    def _deserialize(self, markdown: str) -> None:
        """
        Parse markdown to JMLDoc.
        """
        lines = markdown.split('\n')
        stack = [self._root]
        content = []
        nid = None

        for line in lines:
            # Container opening:
            if match := self._CONTAINER_RE.match(line):
                cid = match.group(1)
                attrs_str = match.group(2).strip()
                attrs = self._deserialize_attributes(attrs_str)

                if cid != 'root':
                    container = JMLNode(id=cid, type=self._TAG_CONTAINER, content='', attributes=attrs)
                    stack[-1].children.append(container)
                    container.parent = stack[-1]
                    self._idx[cid] = container
                    stack.append(container)

                else:
                    self._root.attributes.update(attrs)
                continue

            # Node opening:
            if match := self._NODE_RE.match(line):
                nid = match.group(1)
                attrs_str = match.group(2).strip()
                attrs = self._deserialize_attributes(attrs_str)
                content = []

                node = JMLNode(id=nid, type=self._TAG_NODE, content='', attributes=attrs)
                stack[-1].children.append(node)
                node.parent = stack[-1]
                self._idx[nid] = node
                continue

            # Node closing:
            if self._NODE_END_RE.match(line):
                if nid:
                    self._idx[nid].content = '\n'.join(content).strip()
                    content = []
                    nid = None
                continue

            # Container closing:
            if self._CONTAINER_END_RE.match(line):
                if len(stack) > 1: stack.pop()
                continue

            # Content:
            if nid: content.append(line)
    

    def _serialize_node(self, node: JMLNode, lines: List[str], depth: int = 0):
        """
        Recursively serialize a node.
        """
        if node.id == 'root':
            attrs = ' '.join(f'{k}="{v}"' for k, v in node.attributes.items())
            lines.append(f'<!-- {self._TAG_CONTAINER} id="{node.id}" {attrs} -->')

        elif node.type == 'container':
            attrs = ' '.join(f'{k}="{v}"' for k, v in node.attributes.items())
            lines.append(f'<!-- {self._TAG_CONTAINER} id="{node.id}" {attrs} -->')

        else:
            attrs = ' '.join(f'{k}="{v}"' for k, v in node.attributes.items())
            lines.append(f'<!-- {self._TAG_NODE} id="{node.id}" {attrs} -->')
            lines.append(node.content)
            lines.append(f'<!-- /{self._TAG_NODE} -->')
            return

        for child in node.children:
            self._serialize_node(child, lines, depth + 1)
        lines.append(f'<!-- /{self._TAG_CONTAINER} -->')


    def serialize(self) -> str:
        """
        Serialize JMLDoc to markdown.
        """
        lines = []
        self._serialize_node(self._root, lines)
        return '\n'.join(lines)


    def create_container(self, parent_id: str, **attributes) -> str:
        """
        Create a node container and return the generated ID.
        """
        container = JMLNode(id := self._create_id('c'), type='container', content='', attributes=attributes)
        parent = self._idx[parent_id]

        parent.children.append(container)
        container.parent = parent
        self._idx[id] = container
        return id


    def create_node(self, content: str, parent_id: str, **attributes) -> str:
        """
        Create a node with content and return the generated ID.
        """
        node = JMLNode(id := self._create_id('n'), type='node', content=content, attributes=attributes)
        parent = self._idx[parent_id]

        parent.children.append(node)
        node.parent = parent
        self._idx[id] = node
        return id


    def read_content(self, node_id: str) -> str:
        """
        Read node content.
        """
        if not (node := self._idx.get(node_id)):
            raise JMLNodeNotFoundError(f"Node {node_id} not found")
        
        if node.type != 'node':
            raise InvalidOperationError(f"{node_id} is a container")
        return node.content


    def read_attribute(self, node_id: str, key: str, default=None) -> Any:
        """
        Read a single attribute.
        """
        if not (node := self._idx.get(node_id)):
            raise JMLNodeNotFoundError(f"Node {node_id} not found")
        return node.attributes.get(key, default)
    

    def read_attributes(self, node_id: str) -> Dict[str, Any]:
        """
        Read all attributes.
        """
        if not (node := self._idx.get(node_id)):
            raise JMLNodeNotFoundError(f"Node {node_id} not found")
        return node.attributes.copy()


    def read_children(self, container_id: str) -> List[str]:
        """
        Read child node IDs.
        """
        if not (node := self._idx.get(container_id)):
            raise JMLNodeNotFoundError(f"Container {container_id} not found")
        return [child.id for child in node.children]


    def read_parent(self, node_id: str) -> Optional[str]:
        """
        Read parent node ID.
        """
        if not (node := self._idx.get(node_id)):
            raise JMLNodeNotFoundError(f"Node {node_id} not found")
        return node.parent.id if node.parent else None


    def read_type(self, node_id: str) -> str:
        """
        Read node type.
        """
        if not (node := self._idx.get(node_id)):
            raise JMLNodeNotFoundError(f"Node {node_id} not found")
        return node.type


    def update_content(self, node_id: str, content: str) -> None:
        """
        Update node content.
        """
        if not (node := self._idx.get(node_id)):
            raise JMLNodeNotFoundError(f"Node {node_id} not found")
        
        if node.type != 'node':
            raise InvalidOperationError(f"{node_id} is a container")
        node.content = content


    def update_attribute(self, node_id: str, key: str, value: Any) -> None:
        """
        Update a single attribute.
        """
        if not (node := self._idx.get(node_id)):
            raise JMLNodeNotFoundError(f"Node {node_id} not found")
        node.attributes[key] = value


    def update_attributes(self, node_id: str, **attributes) -> None:
        """
        Update multiple attributes.
        """
        if not (node := self._idx.get(node_id)):
            raise JMLNodeNotFoundError(f"Node {node_id} not found")
        node.attributes.update(attributes)


    def delete_node(self, node_id: str) -> None:
        """
        Delete node and all descendants.
        """
        if not (node := self._idx.get(node_id)):
            raise JMLNodeNotFoundError(f"Node {node_id} not found")

        for child in list(node.children):
            self.delete_node(child.id)

        if node.parent:
            node.parent.children.remove(node)
        del self._idx[node_id]


    def delete_attribute(self, node_id: str, key: str) -> None:
        """
        Delete an attribute.
        """
        if not (node := self._idx.get(node_id)):
            raise JMLNodeNotFoundError(f"Node {node_id} not found")
        node.attributes.pop(key, None)


    def move_node(self, node_id: str, new_parent_id: str, position: int = -1) -> None:
        """
        Move a node to different parent.
        """
        node = self._idx.get(node_id)
        parent = self._idx.get(new_parent_id)

        if not node:
            raise JMLNodeNotFoundError(f"Node {node_id} not found")
        
        if not parent:
            raise JMLNodeNotFoundError(f"Parent {new_parent_id} not found")
        
        if parent.type != 'container':
            raise InvalidOperationError(f"{new_parent_id} is not a container")

        if node.parent:
            node.parent.children.remove(node)

        if position == -1:
            parent.children.append(node)
        else:
            parent.children.insert(position, node)
        node.parent = parent


    def exists(self, node_id: str) -> bool:
        """
        Check if a node exists.
        """
        return node_id in self._idx


    def get_node_ids(self) -> List[str]:
        """
        Get all node IDs.
        """
        return list(self._idx.keys())


    def get_all_descendants(self, container_id: str) -> List[str]:
        """
        Get all descendant node IDs recursively.
        """
        
        if not (node := self._idx.get(container_id)):
            return []

        descendants = []

        for child in node.children:
            descendants.append(child.id)
            if child.type == 'container':
                descendants.extend(self.get_all_descendants(child.id))
        return descendants


    def sort_children(self, parent_id: str, key_func: Callable) -> None:
        """
        Sort children using key function.
        """
        if not (parent := self._idx.get(parent_id)):
            raise JMLNodeNotFoundError(f"Parent {parent_id} not found")
        parent.children.sort(key=key_func)


class JMLDOM:
    """
    Query-based document object manager for selecting and manipulating (Joplin Markup Language) tagged markdown.
    """

    def __init__(self):
        """
        Initialize an empty query builder.
        """
        self._jml: Optional[JMLDoc] = None
        self._results: List[str] = []


    def _get_jml(self) -> JMLDoc:
        """
        Returns a JML instance.
        """
        if (jml := self._jml) is None:
            raise InvalidOperationError("No document loaded. Call set_document() first.")
        return jml


    def _reset(self) -> 'JMLDOM':
        """
        Reset query to include all nodes.
        """
        self._results = self._jml.get_node_ids() if self._jml else []
        return self


    def set_document(self, markdown: str) -> 'JMLDOM':
        """
        Load a markdown document for querying and editing.
        """
        self._jml = JMLDoc(markdown)
        self._reset()
        return self


    def get_document(self) -> str:
        """
        Serialize the current document to markdown.
        """
        jml = self._get_jml()
        return jml.serialize()


    def create_container(self, parent_id: str = "root", **attributes) -> str:
        """
        Create a container node to organize other nodes.
        """
        jml = self._get_jml()
        return jml.create_container(parent_id, **attributes)


    def create_node(self, content: str, parent_id: str, **attributes) -> str:
        """
        Create a non-container node with markdown content.
        """
        jml = self._get_jml()
        return jml.create_node(content, parent_id, **attributes)
    

    def exists(self, node_id: str) -> bool:
        """
        Check if node exists.
        """
        jml = self._get_jml()
        return jml.exists(node_id)
    

    def get_parent(self, node_id: str) -> Optional[str]:
        """
        Get the node's parent container ID.
        """
        jml = self._get_jml()
        return jml.read_parent(node_id)


    def get_children(self, container_id: str) -> List[str]:
        """
        Get list of child node IDs.
        """
        jml = self._get_jml()
        return jml.read_children(container_id)


    def get_type(self, node_id: str) -> str:
        """
        Get node type: 'container' or 'node'.
        """
        jml = self._get_jml()
        return jml.read_type(node_id)
    

    def get_content(self, node_id: str) -> str:
        """
        Get the markdown content of a node.
        """
        jml = self._get_jml()
        return jml.read_content(node_id)


    def get_attribute(self, node_id: str, key: str, default=None) -> Any:
        """
        Get a specific attribute's value.
        """
        jml = self._get_jml()
        return jml.read_attribute(node_id, key, default)


    def get_attributes(self, node_id: str) -> Dict[str, Any]:
        """
        Get all attributes.
        """
        jml = self._get_jml()
        return jml.read_attributes(node_id)


    def set_content(self, node_id: str, content: str) -> None:
        """
        Overwrite the markdown content of a node.
        """
        jml = self._get_jml()
        jml.update_content(node_id, content)


    def set_attribute(self, node_id: str, key: str, value: Any) -> None:
        """
        Set a single attribute.
        """
        jml = self._get_jml()
        jml.update_attribute(node_id, key, value)


    def set_attributes(self, node_id: str, **attributes) -> None:
        """
        Set multiple attributes.
        """
        jml = self._get_jml()
        jml.update_attributes(node_id, **attributes)


    def delete_attribute(self, node_id: str, key: str) -> None:
        """
        Remove an attribute.
        """
        jml = self._get_jml()
        jml.delete_attribute(node_id, key)


    def move(self, node_id: str, new_parent_id: str, position: int = -1) -> None:
        """
        Move the node to different parent.
        """
        jml = self._get_jml()
        jml.move_node(node_id, new_parent_id, position)


    def delete(self, node_id: str) -> None:
        """
        Delete the node and all descendants.
        """
        jml = self._get_jml()
        jml.delete_node(node_id)


    def where(self, **attributes) -> 'JMLDOM':
        """
        Filter nodes by attributes.
        """
        jml = self._get_jml()

        self._results = [
            id for id in self._results
            if all(
                jml.read_attribute(id, k) == v
                for k, v in attributes.items()
            )
        ]
        return self
    

    def where_in(self, key: str, values: list) -> 'JMLDOM':
        """
        Filter nodes where the attribute is in the list of values.
        """
        jml = self._get_jml()

        self._results = [id for id in self._results if jml.read_attribute(id, key) in values]
        return self


    def where_contains(self, key: str, substring: str) -> 'JMLDOM':
        """
        Filter nodes where the attribute contains a substring.
        """
        jml = self._get_jml()

        self._results = [id for id in self._results if substring in str(jml.read_attribute(id, key, ''))]
        return self
    

    def where_container(self, container_id: str, recursive: bool = True) -> 'JMLDOM':
        """
        Filter nodes to descendants of container.
        """
        jml = self._get_jml()

        nodes = set(jml.get_all_descendants(container_id)) if recursive else \
                set(jml.read_children(container_id))

        self._results = [id for id in self._results if id in nodes]
        return self


    def where_type(self, node_type: str) -> 'JMLDOM':
        """
        Filter nodes by type: 'container' or 'node'.
        """
        jml = self._get_jml()

        self._results = [id for id in self._results if jml.read_type(id) == node_type]
        return self


    def where_lambda(self, func: Callable[[str, Dict[str, Any]], bool]) -> 'JMLDOM':
        """
        Filter nodes using a custom function.
        """
        jml = self._get_jml()

        self._results = [id for id in self._results if func(id, jml.read_attributes(id))]
        return self
    

    def where_not(self, *node_ids: str) -> 'JMLDOM':
        """
        Exclude specific nodes from the results.
        """
        self._results = [id for id in self._results if id not in set(node_ids)]
        return self


    def bulk_set_attributes(self, **attributes) -> 'JMLDOM':
        """
        Set the attributes to all selected nodes.
        """
        jml = self._get_jml()

        for id in self._results: jml.update_attributes(id, **attributes)
        return self


    def bulk_set_content(self, transformer: Callable[[str, Dict[str, Any]], str]) -> 'JMLDOM':
        """
        Transform the content of matched nodes: Function taking (content, attributes) -> new_content.
        """
        jml = self._get_jml()

        for id in self._results:
            if jml.read_type(id) == 'node':
                jml.update_content(id,
                    transformer(
                      jml.read_content(id), 
                      jml.read_attributes(id)
                    )
                )
        return self


    def bulk_delete(self) -> int:
        """
        Delete all matched nodes. Returns deleted count.
        """
        jml = self._get_jml()
        rmc = len(self._results)

        for id in list(self._results):
            if jml.exists(id):
                jml.delete_node(id)

        self._results = []
        return rmc


    def bulk_move(self, container_id: str) -> 'JMLDOM':
        """
        Move all matched nodes to the container.
        """
        jml = self._get_jml()

        for id in self._results:
            if jml.exists(id):
                jml.move_node(id, container_id)
        return self


    def sort_parents_children(self, key: str, reverse: bool = False) -> 'JMLDOM':
        """
        Sort children within their parent containers by attribute.
        """
        jml = self._get_jml()
        by_parent = {}

        for id in self._results:
            if pid := jml.read_parent(id):
                if pid not in by_parent:
                    by_parent[pid] = []
                by_parent[pid].append(id)

        for pid in by_parent:
            jml.sort_children(pid, lambda n: n.attributes.get(key, ''))
            if reverse: jml._idx[pid].children.reverse()

        return self


    def get_ids(self) -> List[str]:
        """
        Get a list of matching node IDs.
        """
        return self._results.copy()


    def get_count(self) -> int:
        """
        Count matching nodes.
        """
        return len(self._results)


    def get_first(self) -> Optional[str]:
        """
        Get first matching node ID.
        """
        return self._results[0] if self._results else None


    def get_at(self, index: int) -> Optional[str]:
        """
        Get the node ID at a specific index.
        """
        return self._results[index] if 0 <= index < len(self._results) else None


    def has_results(self) -> bool:
        """
        Check if any node matches exist.
        """
        return len(self._results) > 0


    def each(self, func: Callable[[str], None]) -> 'JMLDOM':
        """
        Execute a custom function for each matched node ID.
        """
        for id in self._results: func(id)
        return self
