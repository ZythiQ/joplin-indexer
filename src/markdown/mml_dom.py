from markdown.mml_doc import MMLDoc
from models.errors import InvalidOperationError
from models.data import MMLNode

from typing import Dict, List, Optional, Any, Callable


class MMLDOM:
    """
    Query-based document object manager for selecting and manipulating (Markdown Markup Language) tagged markdown.
    """

    def __init__(self):
        """
        Initialize an empty query builder.
        """
        self._mml: Optional[MMLDoc] = None
        self._results: List[str] = []


    def _get_mml(self) -> MMLDoc:
        """
        Returns a JML instance.
        """
        if (mml := self._mml) is None:
            raise InvalidOperationError("No document loaded. Call set_document() first.")
        return mml
    

    def _clone(self, results: Optional[List[str]] = None) -> 'MMLDOM':
        """
        Create a new MMLDOM instance sharing the same document.
        """
        dom = MMLDOM()
        dom._mml = self._get_mml()
        dom._results = results if results is not None else self._results.copy()
        
        return dom


    def _reset(self) -> 'MMLDOM':
        """
        Reset query to include all nodes.
        """
        self._results = self._mml.get_node_ids() if self._mml else []
        return self


    def set_document(self, markdown: str) -> 'MMLDOM':
        """
        Load a markdown document for querying and editing.
        """
        self._mml = MMLDoc(markdown)
        self._reset()
        return self


    def get_document(self) -> str:
        """
        Serialize the current document to markdown.
        """
        mml = self._get_mml()
        return mml.serialize()


    def create_container(self, parent_id: str = "root", **attributes) -> str:
        """
        Create a container node to organize other nodes.
        """
        mml = self._get_mml()
        return mml.create_container(parent_id, **attributes)


    def create_node(self, content: str, parent_id: str, **attributes) -> str:
        """
        Create a non-container node with markdown content.
        """
        mml = self._get_mml()
        return mml.create_node(content, parent_id, **attributes)
    

    def exists(self, node_id: str) -> bool:
        """
        Check if node exists.
        """
        mml = self._get_mml()
        return mml.exists(node_id)
    

    def get_parent(self, node_id: str) -> Optional[str]:
        """
        Get the node's parent container ID.
        """
        mml = self._get_mml()
        return mml.read_parent(node_id)


    def get_children(self, container_id: str) -> List[str]:
        """
        Get list of child node IDs.
        """
        mml = self._get_mml()
        return mml.read_children(container_id)


    def get_type(self, node_id: str) -> str:
        """
        Get node type: 'container' or 'node'.
        """
        mml = self._get_mml()
        return mml.read_type(node_id)
    

    def get_content(self, node_id: str) -> str:
        """
        Get the markdown content of a node.
        """
        mml = self._get_mml()
        return mml.read_content(node_id)


    def get_fragments(self, parent_id: str, identifier: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get fragments from a node: {identifier: [content1, content2, ...]}.
        """
        mml = self._get_mml()
        return mml.get_fragments(parent_id, identifier)


    def get_attribute(self, node_id: str, key: str, default=None) -> Any:
        """
        Get a specific attribute's value.
        """
        mml = self._get_mml()
        return mml.read_attribute(node_id, key, default)


    def get_attributes(self, node_id: str) -> Dict[str, Any]:
        """
        Get all attributes.
        """
        mml = self._get_mml()
        return mml.read_attributes(node_id)


    def set_content(self, node_id: str, content: str) -> None:
        """
        Overwrite the markdown content of a node.
        """
        mml = self._get_mml()
        mml.update_content(node_id, content)


    def set_attribute(self, node_id: str, key: str, value: Any) -> None:
        """
        Set a single attribute.
        """
        mml = self._get_mml()
        mml.update_attribute(node_id, key, value)


    def set_attributes(self, node_id: str, **attributes) -> None:
        """
        Set multiple attributes.
        """
        mml = self._get_mml()
        mml.update_attributes(node_id, **attributes)


    def update_fragment(self, parent_id: str, identifier: str, index: int, content: str) -> None:
        """
        Update fragment content at index within a node.
        """
        mml = self._get_mml()
        mml.update_fragment(parent_id, identifier, index, content)


    def delete_attribute(self, node_id: str, key: str) -> None:
        """
        Remove an attribute.
        """
        mml = self._get_mml()
        mml.delete_attribute(node_id, key)


    def move(self, node_id: str, new_parent_id: str, position: int = -1) -> None:
        """
        Move the node to different parent.
        """
        mml = self._get_mml()
        mml.move_node(node_id, new_parent_id, position)


    def delete(self, node_id: str) -> None:
        """
        Delete the node and all descendants.
        """
        mml = self._get_mml()
        mml.delete_node(node_id)


    def generate_fragment(self, identifier: str, content: str) -> str:
        """
        Generate fragment markdown for manual insertion into node content.
        - Example usage:
            dom.set_content(node_id, f"Text with {dom.generate_fragment('tag', 'value')} embedded")
        """
        mml = self._get_mml()
        return mml.generate_fragment_md(identifier, content)


    def where(self, **attributes) -> 'MMLDOM':
        """
        Filter nodes by attributes.
        """
        mml = self._get_mml()
        
        return self._clone([
            id for id in self._results
            if all(mml.read_attribute(id, k) == v for k, v in attributes.items())
        ])
    

    def where_in(self, key: str, values: list) -> 'MMLDOM':
        """
        Filter nodes where the attribute is in the list of values.
        """
        mml = self._get_mml()

        return self._clone([
            id for id in self._results 
            if mml.read_attribute(id, key) in values
        ])


    def where_contains(self, key: str, substring: str) -> 'MMLDOM':
        """
        Filter nodes where the attribute contains a substring.
        """
        mml = self._get_mml()

        return self._clone([
            id for id in self._results 
            if substring in str(mml.read_attribute(id, key, ''))
        ])
    

    def where_container(self, container_id: str, recursive: bool = True) -> 'MMLDOM':
        """
        Filter nodes to descendants of container.
        """
        mml = self._get_mml()

        nodes = set(mml.get_all_descendants(container_id)) if recursive else \
                set(mml.read_children(container_id))
        
        return self._clone([id for id in self._results if id in nodes])


    def where_type(self, node_type: str) -> 'MMLDOM':
        """
        Filter nodes by type: 'container' or 'node'.
        Note: The 'fragment' type cannot be queried directly, use where_has_fragment().
        """
        mml = self._get_mml()

        return self._clone([
            id for id in self._results 
            if mml.read_type(id) == node_type
        ])


    def where_has_fragment(self, identifier: str) -> 'MMLDOM':
        """
        Filter to nodes that contain fragments with the specified identifier.
        Returns the nodes themselves.
        """
        mml = self._get_mml()
        
        def has_fragment(node_id: str) -> bool:
            node = mml._idx[node_id]

            return any(c.type == MMLNode.Type.FRAGMENT and c.id == identifier 
                    for c in node.children)
        
        return self._clone([id for id in self._results if has_fragment(id)])


    def where_lambda(self, func: Callable[[str, Dict[str, Any]], bool]) -> 'MMLDOM':
        """
        Filter nodes using a custom function.
        """
        mml = self._get_mml()

        return self._clone([
            id for id in self._results 
            if func(id, mml.read_attributes(id))
        ])
    

    def where_not(self, *node_ids: str) -> 'MMLDOM':
        """
        Exclude specific nodes from the results.
        """
        return self._clone([id for id in self._results if id not in set(node_ids)])


    def bulk_set_attributes(self, **attributes) -> 'MMLDOM':
        """
        Set the attributes to all selected nodes.
        """
        mml = self._get_mml()

        for id in self._results: mml.update_attributes(id, **attributes)
        return self


    def bulk_set_content(self, transformer: Callable[[str, Dict[str, Any]], str]) -> 'MMLDOM':
        """
        Transform the content of matched nodes: Function taking (content, attributes) -> new_content.
        """
        mml = self._get_mml()

        for id in self._results:
            if mml.read_type(id) == 'node':
                mml.update_content(id,
                    transformer(
                      mml.read_content(id), 
                      mml.read_attributes(id)
                    )
                )
        return self


    def bulk_delete(self) -> int:
        """
        Delete all matched nodes. Returns deleted count.
        """
        mml = self._get_mml()
        rmc = len(self._results)

        for id in list(self._results):
            if mml.exists(id):
                mml.delete_node(id)

        self._results = []
        return rmc


    def bulk_move(self, container_id: str) -> 'MMLDOM':
        """
        Move all matched nodes to the container.
        """
        mml = self._get_mml()

        for id in self._results:
            if mml.exists(id):
                mml.move_node(id, container_id)
        return self


    def sort_parents_children(self, key: str, reverse: bool = False) -> 'MMLDOM':
        """
        Sort children within their parent containers by attribute.
        """
        mml = self._get_mml()
        by_parent = {}

        for id in self._results:
            if pid := mml.read_parent(id):
                if pid not in by_parent:
                    by_parent[pid] = []
                by_parent[pid].append(id)

        for pid in by_parent:
            mml.sort_children(pid, lambda n: n.attributes.get(key, ''))
            if reverse: mml._idx[pid].children.reverse()

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


    def each(self, func: Callable[[str], None]) -> 'MMLDOM':
        """
        Execute a custom function for each matched node ID.
        """
        for id in self._results: func(id)
        return self
    

    def __repr__(self) -> str:
        """
        Return a string representation.
        """
        if self._mml is None: return "MMLDOM(no document loaded)"
        return repr(self._mml)
