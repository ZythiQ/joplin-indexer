from models.errors import MMLNodeNotFoundError, InvalidOperationError
from models.data import MMLNode

from typing import Dict, List, Optional, Any, Callable
import secrets
import re


class MMLDoc:
    """
    Markdown Markup Language parser and document tree manager.
    """

    _TO_TAG = { MMLNode.Type.NODE: '@n', MMLNode.Type.CONTAINER: '@c', MMLNode.Type.FRAGMENT: '%' }

    _FRAGMENT_RE = re.compile(r'<!-- %(\w+) -->')
    _FRAGMENT_END_RE = re.compile(r'<!-- /%(\w+) -->')

    _ATTRIBUTE_RE = re.compile(r'(\w+)="([^"]*)"')

    _NODE_RE = re.compile(rf'<!-- {_TO_TAG[MMLNode.Type.NODE]} id="([^"]+)"(.*?)-->')
    _NODE_END_RE = re.compile(rf'<!-- /{_TO_TAG[MMLNode.Type.NODE]} -->')

    _CONTAINER_RE = re.compile(rf'<!-- {_TO_TAG[MMLNode.Type.CONTAINER]} id="([^"]+)"(.*?)-->')
    _CONTAINER_END_RE = re.compile(rf'<!-- /{_TO_TAG[MMLNode.Type.CONTAINER]} -->')


    def __init__(self, markdown: str):
        """
        Initialize tree by parsing JML markdown.
        """
        self._root = MMLNode(id='root', type=MMLNode.Type.CONTAINER, content='', attributes={'type': 'root'})
        self._idx: Dict[str, MMLNode] = {'root': self._root}
        if markdown: self._deserialize(markdown)


    def _create_id(self, prefix: str) -> str:
        """
        Generate a unique ID.
        """
        while True:
            new_id = f"{prefix or 'x'}_{secrets.token_hex(4)}"
            if new_id not in self._idx: return new_id
    

    def _is_empty(self, content: str) -> bool:
        """
        Check if content is empty (only whitespace).
        """
        return not content or content.strip() == ''


    def _wrap_content(self, parent: MMLNode, content: List[str]) -> None:
        """
        Wrap accumulated loose content in a new node and add to the parent.
        """
        if not content:
            return
        
        content_str = '\n'.join(content).strip()
        if not self._is_empty(content_str):
            node = MMLNode(id := self._create_id('n'), type=MMLNode.Type.NODE, content=content_str, attributes={})
            parent.children.append(node)

            node.parent = parent
            self._idx[id] = node


    def _prune_nodes(self, node: MMLNode) -> bool:
        """
        Recursively check for empty nodes and containers from the bottom-up.
        """
        children_to_remove = []

        for child in node.children:
            if self._prune_nodes(child):
                children_to_remove.append(child)
        
        for child in children_to_remove:
            node.children.remove(child)

            if child.id in self._idx:
                del self._idx[child.id]
        
        if node.id == 'root':
            return False
        
        if node.type == MMLNode.Type.FRAGMENT:
            return False
        
        if node.type == MMLNode.Type.NODE:
            return self._is_empty(node.content)
        
        else:
            return len(node.children) == 0
        

    def _deserialize_fragments(self) -> None:
        """
        Extract and deserialize fragments from node content.
        """
        for node in list(self._idx.values()):
            if (node.type != MMLNode.Type.NODE) or (not node.content):
                continue
            
            fragments: Dict[str, List[str]] = {}
            content = node.content
            pos = 0
            
            while pos < len(content):
                # Find opening:
                match = self._FRAGMENT_RE.search(content, pos)
                if not match:
                    break
                
                identifier = match.group(1)
                start = match.end()
                
                # Find closing:
                end_match = self._FRAGMENT_END_RE.search(content, start)
                if not end_match or end_match.group(1) != identifier:
                    pos = match.end()
                    continue
                
                fragment_content = content[start:end_match.start()].strip()

                if identifier not in fragments:
                    fragments[identifier] = []

                fragments[identifier].append(fragment_content)
                pos = end_match.end()
            
            for identifier, contents in fragments.items():
                fragment = MMLNode(
                    id=identifier,
                    type=MMLNode.Type.FRAGMENT,
                    content='',
                    attributes={str(i + 1): content for i, content in enumerate(contents)}
                )
                
                node.children.append(fragment)
                fragment.parent = node
        

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
        Parse markdown to JMLTree fixing any malformed JML.
        """
        lines = markdown.split('\n')
        loose_md = []
        node_md = []

        seen_root = False
        root_start = -1
        cid = None
        
        # Find root:
        for i, line in enumerate(lines):
            if match := self._CONTAINER_RE.match(line):
                if match.group(1) == 'root':
                    seen_root = True
                    root_start = i
                    break
        
        in_root = seen_root and root_start == 0
        stack = [self._root]
        
        # Container opening:
        for i, line in enumerate(lines):
            if match := self._CONTAINER_RE.match(line):
                cid = match.group(1)
                attrs_str = match.group(2).strip()
                attrs = self._deserialize_attributes(attrs_str)

                if loose_md:
                    self._wrap_content(stack[-1], loose_md)
                    loose_md = []

                if cid == 'root':
                    self._root.attributes.update(attrs)
                    in_root = True

                else:
                    container = MMLNode(id=cid, type=MMLNode.Type.CONTAINER, content='', attributes=attrs)
                    stack[-1].children.append(container)
                    container.parent = stack[-1]
                    self._idx[cid] = container
                    stack.append(container)
                continue

            # Node opening:
            if match := self._NODE_RE.match(line):
                if loose_md:
                    self._wrap_content(stack[-1], loose_md)
                    loose_md = []
                
                attrs = self._deserialize_attributes(match.group(2).strip())
                cid = match.group(1)
                node_md = []

                node = MMLNode(id=cid, type=MMLNode.Type.NODE, content='', attributes=attrs)
                stack[-1].children.append(node)
                node.parent = stack[-1]

                self._idx[cid] = node
                continue

            # Node closing:
            if self._NODE_END_RE.match(line):
                if cid:
                    self._idx[cid].content = '\n'.join(node_md).strip()
                    node_md = []
                    cid = None
                continue

            # Container closing:
            if self._CONTAINER_END_RE.match(line):
                if loose_md:
                    self._wrap_content(stack[-1], loose_md)
                    loose_md = []
                
                if len(stack) > 1: stack.pop()

                elif stack[-1].id == 'root':
                    in_root = False
                continue

            # Content pass:
            if cid is not None:
                node_md.append(line)

            elif in_root or not seen_root:
                loose_md.append(line)

            else:
                loose_md.append(line)
        
        # Final fix:
        if loose_md:
            self._wrap_content(self._root, loose_md)
        
        if cid and node_md:
            self._idx[cid].content = '\n'.join(node_md).strip()
        
        self._prune_nodes(self._root)
        self._deserialize_fragments()
    

    def _serialize_node(self, node: MMLNode, lines: List[str], depth: int = 0):
        """
        Recursively serialize a node.
        """
        tag = self._TO_TAG[node.type]
        
        if node.id == 'root':
            attrs = ' '.join(f'{k}="{v}"' for k, v in node.attributes.items())
            lines.append(f'<!-- {tag} id="{node.id}" {attrs} -->')

        elif node.type == MMLNode.Type.FRAGMENT:
            sorted_keys = sorted(node.attributes.keys(), key=int)
            for key in sorted_keys:
                lines.append(f'<!-- %{node.id} -->')
                lines.append(node.attributes[key])
                lines.append(f'<!-- /%{node.id} -->')
            return

        elif node.type == MMLNode.Type.CONTAINER:
            attrs = ' '.join(f'{k}="{v}"' for k, v in node.attributes.items())
            lines.append(f'<!-- {tag} id="{node.id}" {attrs} -->')

        else:
            attrs = ' '.join(f'{k}="{v}"' for k, v in node.attributes.items())
            lines.append(f'<!-- {tag} id="{node.id}" {attrs} -->')
            lines.append(node.content)
            lines.append(f'<!-- /{tag} -->')
            return

        for child in node.children:
            self._serialize_node(child, lines, depth + 1)
        lines.append(f'<!-- /{tag} -->')


    def _refresh_node_content(self, node: MMLNode) -> None:
        """
        Rebuild node content by replacing fragment markdown with current fragment values.
        """
        if node.type != MMLNode.Type.NODE:
            return
        
        fragments = {}

        for child in node.children:
            if child.type == MMLNode.Type.FRAGMENT:
                sorted_keys = sorted(child.attributes.keys(), key=int)
                fragments[child.id] = [child.attributes[k] for k in sorted_keys]
        
        content = node.content

        for identifier, contents in fragments.items():
            pattern = f'<!-- %{re.escape(identifier)} -->.*?<!-- /%{re.escape(identifier)} -->'
            matches = list(re.finditer(pattern, content, flags=re.DOTALL))
            
            for i in range(len(matches) - 1, -1, -1):
                if i < len(contents):
                    match = matches[i]
                    replacement = f'<!-- %{identifier} -->{contents[i]}<!-- /%{identifier} -->'
                    content = content[:match.start()] + replacement + content[match.end():]

        node.content = content


    def serialize(self) -> str:
        """
        Serialize MMLDoc to markdown.
        """
        lines = []
        self._serialize_node(self._root, lines)
        return '\n'.join(lines)


    def create_container(self, parent_id: str, **attributes) -> str:
        """
        Create a node container and return the generated ID.
        """
        container = MMLNode(id := self._create_id('c'), type=MMLNode.Type.CONTAINER, content='', attributes=attributes)
        parent = self._idx[parent_id]

        parent.children.append(container)
        container.parent = parent
        self._idx[id] = container
        return id


    def create_node(self, content: str, parent_id: str, **attributes) -> str:
        """
        Create a node with content and return the generated ID.
        """
        node = MMLNode(id := self._create_id('n'), type=MMLNode.Type.NODE, content=content, attributes=attributes)
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
            raise MMLNodeNotFoundError(f"Node {node_id} not found")
        
        if node.type != MMLNode.Type.NODE:
            raise InvalidOperationError(f"{node_id} is a container")
        return node.content


    def get_fragments(self, parent_id: str, identifier: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get fragments from a node: {identifier: [content1, content2, ...]}.
        """
        if not (parent := self._idx.get(parent_id)):
            raise MMLNodeNotFoundError(f"Parent {parent_id} not found")
        
        result = {}

        for child in parent.children:
            if child.type == MMLNode.Type.FRAGMENT:
                if identifier is None or child.id == identifier:
                    sorted_keys = sorted(child.attributes.keys(), key=int)
                    result[child.id] = [child.attributes[k] for k in sorted_keys]
        
        return result


    def read_attribute(self, node_id: str, key: str, default=None) -> Any:
        """
        Read a single attribute.
        """
        if not (node := self._idx.get(node_id)):
            raise MMLNodeNotFoundError(f"Node {node_id} not found")
        return node.attributes.get(key, default)
    

    def read_attributes(self, node_id: str) -> Dict[str, Any]:
        """
        Read all attributes.
        """
        if not (node := self._idx.get(node_id)):
            raise MMLNodeNotFoundError(f"Node {node_id} not found")
        return node.attributes.copy()


    def read_children(self, container_id: str) -> List[str]:
        """
        Read child node IDs.
        """
        if not (node := self._idx.get(container_id)):
            raise MMLNodeNotFoundError(f"Container {container_id} not found")
        return [child.id for child in node.children]


    def read_parent(self, node_id: str) -> Optional[str]:
        """
        Read parent node ID.
        """
        if not (node := self._idx.get(node_id)):
            raise MMLNodeNotFoundError(f"Node {node_id} not found")
        return node.parent.id if node.parent else None


    def read_type(self, node_id: str) -> str:
        """
        Read node type as string value.
        """
        if not (node := self._idx.get(node_id)):
            raise MMLNodeNotFoundError(f"Node {node_id} not found")
        return node.type.value


    def update_content(self, node_id: str, content: str) -> None:
        """
        Update node content.
        """
        if not (node := self._idx.get(node_id)):
            raise MMLNodeNotFoundError(f"Node {node_id} not found")
        
        if node.type != MMLNode.Type.NODE:
            raise InvalidOperationError(f"{node_id} is a container")
        node.content = content


    def update_fragment(self, parent_id: str, identifier: str, index: int, content: str) -> None:
        """
        Update fragment content at specific index.
        """
        if not (parent := self._idx.get(parent_id)):
            raise MMLNodeNotFoundError(f"Parent {parent_id} not found")
        
        key = str(index)
        fragment = next((c for c in parent.children 
                        if c.type == MMLNode.Type.FRAGMENT and c.id == identifier), None)
        
        if not fragment:
            raise MMLNodeNotFoundError(f"Fragment {identifier} not found in {parent_id}")
        
        if key not in fragment.attributes:
            raise InvalidOperationError(f"Fragment index {index} out of bounds")
        
        fragment.attributes[key] = content
        
        if parent.type == MMLNode.Type.NODE:
            self._refresh_node_content(parent)


    def update_attribute(self, node_id: str, key: str, value: Any) -> None:
        """
        Update a single attribute.
        """
        if not (node := self._idx.get(node_id)):
            raise MMLNodeNotFoundError(f"Node {node_id} not found")
        node.attributes[key] = value


    def update_attributes(self, node_id: str, **attributes) -> None:
        """
        Update multiple attributes.
        """
        if not (node := self._idx.get(node_id)):
            raise MMLNodeNotFoundError(f"Node {node_id} not found")
        node.attributes.update(attributes)


    def delete_node(self, node_id: str) -> None:
        """
        Delete node and all descendants.
        """
        if not (node := self._idx.get(node_id)):
            raise MMLNodeNotFoundError(f"Node {node_id} not found")

        for child in list(node.children):
            if child.id in self._idx:
                self.delete_node(child.id)

        if node.parent:
            node.parent.children.remove(node)
        del self._idx[node_id]


    def delete_attribute(self, node_id: str, key: str) -> None:
        """
        Delete an attribute.
        """
        if not (node := self._idx.get(node_id)):
            raise MMLNodeNotFoundError(f"Node {node_id} not found")
        node.attributes.pop(key, None)


    def move_node(self, node_id: str, new_parent_id: str, position: int = -1) -> None:
        """
        Move a node to different parent.
        """
        node = self._idx.get(node_id)
        parent = self._idx.get(new_parent_id)

        if not node:
            raise MMLNodeNotFoundError(f"Node {node_id} not found")
        
        if not parent:
            raise MMLNodeNotFoundError(f"Parent {new_parent_id} not found")
        
        if parent.type != MMLNode.Type.CONTAINER:
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
            if child.type == MMLNode.Type.CONTAINER:
                descendants.extend(self.get_all_descendants(child.id))
        return descendants


    def sort_children(self, parent_id: str, key_func: Callable) -> None:
        """
        Sort children using key function.
        """
        if not (parent := self._idx.get(parent_id)):
            raise MMLNodeNotFoundError(f"Parent {parent_id} not found")
        parent.children.sort(key=key_func)


    def generate_fragment_md(self, identifier: str, content: str) -> str:
        """
        Generate fragment markdown for manual insertion into node content.
        """
        return f'<!-- %{identifier} -->{content}<!-- /%{identifier} -->'


    def __repr__(self) -> str:
        """
        Return a string representation of the JML tree.
        """
        lines = []

        IMPT = "\x1b[36m"
        INFO = "\033[90m"
        RESET = "\033[0m"
        
        def _build_tree(node: MMLNode, prefix: str = "", is_last: bool = True):
            if node.id == "root": 
                lines.append(f"{IMPT}root/{RESET}")
            else:
                content = ""
                connector = "└── " if is_last else "├── "
                attrs = f" {IMPT}{node.attributes}{RESET}" if node.attributes else ""
                
                if node.type == MMLNode.Type.CONTAINER:
                    node_type = f"{IMPT}[C]{RESET}"
                    node_id = f"{node.id}"
                    attrs = f"{attrs}" if attrs else ""

                    lines.append(f"{prefix}{connector}{node_type} {node_id}{attrs}")

                elif node.type == MMLNode.Type.FRAGMENT:
                    sorted_keys = sorted(node.attributes.keys(), key=int)
                    contents = [node.attributes[k][:20] + ("..." if len(node.attributes[k]) > 20 else "") for k in sorted_keys]

                    lines.append(f"{prefix}{connector}{INFO}<F>{RESET} {node.id} {INFO}{contents} [len: {len(contents)}]{RESET}")
                    return

                else:
                    node_type = "(N)"
                    
                    if node.content:
                        snippet = node.content[:20].replace("\n", " ")
                        if len(node.content) > 20: 
                            snippet += "..."
                        content = f" {INFO}[{len(node.content)} chars: \"{snippet}\"]{RESET}"
                    
                    lines.append(f"{prefix}{connector}{node_type} {node.id}{attrs}{content}")
            
            if node.children:
                if node.id == "root": new_prefix = ""
                else: new_prefix = prefix + ("    " if is_last else "│   ")
                
                for i, child in enumerate(node.children):
                    _build_tree(child, new_prefix, i == len(node.children) - 1)
                    
                    if child.type != MMLNode.Type.FRAGMENT and i < len(node.children) - 1:
                        lines.append(new_prefix + "│   " + "\u200b")
        
        _build_tree(self._root)
        return "\n".join(lines)
