
import os
import socket
from cache import cache  

MAX_BYTES = 4096
MAX_RESPONSE_SIZE = 50 * 1024 * 1024  # 50MB
UPLOAD_DIR = "./uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def send_error_response(client_socket, status_code, message):
    status_texts = {
        400: "Bad Request",
        404: "Not Found",
        405: "Method Not Allowed",
        500: "Internal Server Error",
        502: "Bad Gateway",
        504: "Gateway Timeout"
    }
    status_text = status_texts.get(status_code, "Error")
    body = f"<html><head><title>{status_code} {status_text}</title></head>" \
           f"<body><h1>{status_code} {status_text}</h1><p>{message}</p></body></html>"
    response = f"HTTP/1.1 {status_code} {status_text}\r\n" \
               f"Content-Type: text/html\r\n" \
               f"Content-Length: {len(body)}\r\n" \
               f"Connection: close\r\n\r\n{body}"
    client_socket.sendall(response.encode())


def connect_remote_server(host, port):
    try:
        s = socket.create_connection((host, int(port)), timeout=30)
        return s
    except Exception as e:
        print(f"[HTTP] Failed to connect to {host}:{port} -> {e}")
        return None


def handle_get(client_socket, request, raw_request):
    if not request.path:
        send_error_response(client_socket, 400, "Invalid request")
        return -1

    # Check cache first
    cache_key = f"{request.host}:{request.port}{request.path}"
    cached = cache.cache_find(cache_key)
    if cached:
        client_socket.sendall(cached.data)
        return 1

    remote_sock = connect_remote_server(request.host, request.port or "80")
    if not remote_sock:
        send_error_response(client_socket, 502, "Failed to connect remote server")
        return -1

    http_req = f"GET {request.path} HTTP/1.1\r\nHost: {request.host}\r\nConnection: close\r\nUser-Agent: ProxyServer/1.0\r\n\r\n"
    remote_sock.sendall(http_req.encode())

    full_response = b""
    while True:
        data = remote_sock.recv(MAX_BYTES)
        if not data:
            break
        client_socket.sendall(data)
        full_response += data
        if len(full_response) > MAX_RESPONSE_SIZE:
            full_response = b""  # skip caching if too big

    remote_sock.close()
    if full_response:
        cache.cache_add(full_response, cache_key)
    return 1


def handle_post(client_socket, request, raw_request):
    if not request.host or not request.path:
        send_error_response(client_socket, 400, "Invalid request")
        return -1

    remote_sock = connect_remote_server(request.host, request.port or "80")
    if not remote_sock:
        send_error_response(client_socket, 502, "Failed to connect remote server")
        return -1

    remote_sock.sendall(raw_request.encode())
    while True:
        data = remote_sock.recv(MAX_BYTES)
        if not data:
            break
        client_socket.sendall(data)
    remote_sock.close()
    return 1


def handle_put(client_socket, request, raw_request):
    relative_path = request.path[9:] if request.path.startswith("/uploads/") else request.path
    filepath = os.path.join("./uploads", relative_path)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # Extract body as bytes
    split_data = raw_request.split(b"\r\n\r\n", 1)
    body = split_data[1] if len(split_data) > 1 else b""

    try:
        with open(filepath, "wb") as f:  # write as bytes
            f.write(body)
        response = b"HTTP/1.1 201 Created\r\nContent-Length:0\r\n\r\n"
        client_socket.sendall(response)
        print(f"[PUT] File saved: {filepath}")
        return 0
    except Exception as e:
        send_error_response(client_socket, 500, f"Failed to save file: {e}")
        return -1


def handle_find(client_socket, request, raw_request):
    relative_path = request.path[6:] if request.path.startswith("/find/") else request.path
    filepath = os.path.join("./find", relative_path)

   
    element = cache.cache_find(request.path)
    if element:
        client_socket.sendall(element.data)
        return 0

    if not os.path.exists(filepath):
        send_error_response(client_socket, 404, "File not found")
        return -1

    with open(filepath, "rb") as f:
        file_data = f.read()

    header = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(file_data)}\r\nConnection: close\r\n\r\n"
    full_response = header.encode() + file_data
    client_socket.sendall(full_response)

    cache.cache_add(full_response, request.path)
    print(f"[FIND] Cached {request.path} ({len(full_response)} bytes)")
    return 0


def handle_file_upload(client_socket, request, body, body_len):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = os.path.basename(request.path)
    if not filename:
        send_error_response(client_socket, 400, "No filename specified")
        return -1

    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(body[:MAX_FILE_SIZE])

    response_body = f"<html><body><h1>File uploaded successfully: {filename}</h1></body></html>"
    response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: {len(response_body)}\r\nConnection: close\r\n\r\n{response_body}"
    client_socket.sendall(response.encode())
    print(f"[UPLOAD] File saved as {filepath}")
    return 1


def handle_file_download(client_socket, request):
    if request.path.startswith("/files/"):
        filename = request.path[7:]
        if os.path.exists(filename):
            with open(filename, "rb") as f:
                data = f.read()
            headers = f"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Disposition: attachment; filename=\"{filename}\"\r\nContent-Length: {len(data)}\r\nConnection: close\r\n\r\n"
            client_socket.sendall(headers.encode() + data)
            return 1
        else:
            send_error_response(client_socket, 404, "File not found")
            return -1
    return handle_get(client_socket, request, "")
