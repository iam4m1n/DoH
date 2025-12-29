from rest_framework.renderers import JSONRenderer, BaseRenderer


class DNSJsonRenderer(JSONRenderer):
    media_type = 'application/dns-json'
    format = 'dns-json'
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        # Use parent's render method which handles JSON encoding
        return super().render(data, accepted_media_type, renderer_context)


class DNSMessageRenderer(BaseRenderer):
    media_type = 'application/dns-message'
    format = 'dns-message'
    charset = None  # Binary data, no charset
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        # For binary DNS messages, data should already be bytes
        if isinstance(data, bytes):
            return data
        # If it's a string, try to encode it
        if isinstance(data, str):
            return data.encode('latin-1')
        return b''

