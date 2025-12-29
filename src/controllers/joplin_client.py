from models.errors import JoplinAPIError, JoplinNotFoundError

from typing import Dict, List, Optional, Any
import requests


class JoplinClient:
    """
    Joplin REST API client.
    """
    
    _instance = None
    _discovered_port = None
    _discovery_attempted = False
    

    def __new__(cls, token: str, base_url: Optional[str] = None):
        """
        Singleton pattern to ensure port discovery happens once.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    

    def __init__(self, token: str, base_url: Optional[str] = None):
        """
        Initialize API client with optional base URL.
        """
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.token = token
        self.session = requests.Session()
        
        self.base_url = base_url if base_url else self._discover_port()
        self._warmup()
        
        self._initialized = True
    

    @classmethod
    def _discover_port(cls) -> str:
        """
        Discover Joplin API port by testing ports 41184-41194.
        """
        if cls._discovered_port is not None:
            return cls._discovered_port
            
        if cls._discovery_attempted:
            raise JoplinAPIError("Port discovery already failed")
        
        cls._discovery_attempted = True
        
        for port in range(41184, 41195):
            url = f"http://localhost:{port}"
            try:
                response = requests.get(f"{url}/ping", timeout=0.5)
                if response.status_code == 200 and response.text == 'JoplinClipperServer':
                    cls._discovered_port = url
                    return url
                
            except (requests.ConnectionError, requests.Timeout):
                continue
        
        raise JoplinAPIError("Could not discover Joplin API port (tested 41184-41194)")
        

    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """
        Make an API request.
        """
        url = f"{self.base_url}/{endpoint}"
        params = kwargs.get('params', {})
        params['token'] = self.token
        kwargs['params'] = params
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
        
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                raise JoplinNotFoundError(f"Resource not found: {endpoint}")
            raise JoplinAPIError(f"API error: {e}")
        
        except Exception as e:
            raise JoplinAPIError(f"Request failed: {e}")
        
    
    def _warmup(self) -> None:
        """
        Warm up the session and validate authentication.
        """
        try: self._request("GET", "notes", params={"limit": 1})
        except JoplinAPIError: raise
        except Exception: pass
        

    @classmethod
    def reset_discovery(cls):
        """
        Reset port discovery states.
        """
        cls._discovery_attempted = False
        cls._discovered_port = None
        cls._instance = None
        

    def get_paginated(self, endpoint: str, fields: Optional[List[str]] = None, **params) -> List[Dict]:
        """
        Get all items with pagination.
        """
        items = []
        page = 1
        
        while True:
            params['page'] = page

            if fields:
                params['fields'] = ','.join(fields)
            
            response = self.get(endpoint, **params)
            
            if not response.get('items'):
                break
                
            items.extend(response['items'])
            
            if not response.get('has_more'):
                break
            
            page += 1
        return items
    

    def get(self, endpoint: str, **params) -> Any:
        """
        GET request.
        """
        return self._request('GET', endpoint, params=params)
    

    def post(self, endpoint: str, data: Dict) -> Any:
        """
        POST request.
        """
        return self._request('POST', endpoint, json=data)
    

    def put(self, endpoint: str, data: Dict) -> Any:
        """
        PUT request.
        """
        return self._request('PUT', endpoint, json=data)
    

    def delete(self, endpoint: str) -> Any:
        """
        DELETE request.
        """
        return self._request('DELETE', endpoint)
