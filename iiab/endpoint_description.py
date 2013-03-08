class EndPointDescription(object):
    """Description of url for use with pagination"""
    def __init__(self, endpoint, values):
        """matches parameters used in url_for(endpoint, values) function
        :param endpoint: string description of endpoint such as blueprint_class.funcname
        :param values: dictionary of parameters to pass to url_for"""
        self._endpoint = endpoint
        self._values = values or {}

    @property
    def endpoint(self):
        return self._endpoint

    @property
    def values(self):
        return self._values
