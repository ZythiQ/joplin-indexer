
class JoplinError(Exception): pass
class InvalidOperationError(JoplinError): pass

class JoplinAPIError(JoplinError): pass
class JoplinNotFoundError(JoplinError): pass

class JMLError(JoplinError): pass
class JMLNodeNotFoundError(JMLError): pass
