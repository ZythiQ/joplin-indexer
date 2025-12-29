
class JoplinError(Exception): pass
class InvalidOperationError(JoplinError): pass

class JoplinAPIError(JoplinError): pass
class JoplinNotFoundError(JoplinError): pass

class MMLError(JoplinError): pass
class MMLNodeNotFoundError(MMLError): pass
