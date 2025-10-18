import re

MAX_HEADERS = 50

class ParsedRequest:
    def __init__(self):
        self.method = None
        self.protocol = None
        self.host = None
        self.port = None
        self.path = None
        self.version = None
        self.headers = []
        self.body = b""
        self.body_length = 0

def parse_http_request(raw_data: bytes):
    try:
        decoded = raw_data.decode('iso-8859-1', errors='replace')
    except:
        return None, None, None

    
    parts = re.split(r'\r\n\r\n|\n\n', decoded, maxsplit=1)
    header_part = parts[0]
    body_part = parts[1] if len(parts) > 1 else b""
    header_bytes = header_part.encode('iso-8859-1')
    body_bytes = body_part.encode('iso-8859-1')

    pr = ParsedRequest()

    
    lines = header_part.splitlines()
    if not lines:
        return None, None, None

    first_line = lines[0].strip()
    parts = first_line.split()
    if len(parts) < 3:
        return None, None, None

    pr.method, url, pr.version = parts[0], parts[1], parts[2]

    
    if url.startswith("http://"):
        pr.protocol = "http"
        rest = url[len("http://"):]
        
        slash_pos = rest.find("/")
        if slash_pos >= 0:
            pr.host = rest[:slash_pos]
            pr.path = rest[slash_pos:]
        else:
            pr.host = rest
            pr.path = "/"

       
        if ":" in pr.host:
            host_part, port_part = pr.host.split(":", 1)
            pr.host = host_part
            pr.port = port_part
        else:
            pr.port = "80"

    else:
       
        pr.path = url
        pr.protocol = "http"

    header_lines = lines[1:]
    for h in header_lines[:MAX_HEADERS]:
        h = h.strip()
        if not h:
            break
        pr.headers.append(h)

 
    if not pr.host:
        for h in pr.headers:
            if h.lower().startswith("host:"):
                val = h.split(":", 1)[1].strip()
                if ":" in val:
                    host_val, port_val = val.split(":", 1)
                    pr.host = host_val.strip()
                    pr.port = port_val.strip()
                else:
                    pr.host = val
                    pr.port = pr.port or "80"
                break

 
    if not pr.host:
        pr.host = "localhost"
    if not pr.port:
        pr.port = "80"
    if not pr.path:
        pr.path = "/"

    
    pr.body = body_bytes
    pr.body_length = len(body_bytes)

    return pr, header_bytes, body_bytes


def unparse_http_request(pr: ParsedRequest):
    if not pr.method or not pr.path or not pr.version:
        return b""

    request_line = f"{pr.method} {pr.path} {pr.version}\r\n"
    headers_str = ""
    for h in pr.headers:
        headers_str += h + "\r\n"

    full = request_line + headers_str + "\r\n"

    if pr.body_length > 0:
        full = full.encode('iso-8859-1') + pr.body
    else:
        full = full.encode('iso-8859-1')

    return full
