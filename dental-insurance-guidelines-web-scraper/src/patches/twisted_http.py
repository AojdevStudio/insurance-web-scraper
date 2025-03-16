"""
Modern alternatives to cgi module functions for Twisted compatibility.
Uses standard library modules instead of deprecated cgi module.
"""

import email.parser
import urllib.parse
import html
from io import BytesIO
from email.message import Message

def parse_header(line):
    """Parse a Content-type like header using email.message.Message."""
    if not line:
        return '', {}
        
    if isinstance(line, bytes):
        line = line.decode('utf-8')
        
    msg = Message()
    msg['content-type'] = line
    
    return msg.get_content_type(), dict(msg.get_params([], header='content-type'))

def parse_multipart(fp, boundary):
    """Parse multipart form data using email.parser."""
    if isinstance(boundary, str):
        boundary = boundary.encode('utf-8')
        
    # Create email parser
    parser = email.parser.BytesParser()
    
    # Prepare headers for multipart message
    headers = [
        b'Content-Type: multipart/form-data; boundary=' + boundary,
        b'',
        b''
    ]
    
    # Create message from file
    data = b'\r\n'.join(headers) + fp.read()
    msg = parser.parsebytes(data)
    
    # Parse parts
    result = {}
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
            
        name = part.get_param('name', header='content-disposition')
        if name:
            value = part.get_payload(decode=True)
            filename = part.get_filename()
            if filename:
                result[name] = [value, filename]
            else:
                result[name] = [value]
                
    return result

def parse_qs(qs, keep_blank_values=False):
    """Parse a query string using urllib.parse."""
    return urllib.parse.parse_qs(qs, keep_blank_values=keep_blank_values)

def escape(s, quote=None):
    """HTML-escape a string using html.escape."""
    return html.escape(s, quote=bool(quote)) 