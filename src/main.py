import socket
import threading
import sys
import os
from typing import Tuple, Optional

from http_handler import handle_find


from proxy_parse import parse_http_request
import http_handler

DEFAULT_PORT = 8080
MAX_CLIENTS = 1000
RECV_BUFFER = 4096
SOCKET_TIMEOUT = 30  

semaphore = threading.Semaphore(MAX_CLIENTS)
thread_count_lock = threading.Lock()
thread_counter = 0

def threaded_client_fn(client_socket: socket.socket, client_addr):
  
    global thread_counter

    acquired = False
    try:
        semaphore.acquire()
        acquired = True

        client_socket.settimeout(SOCKET_TIMEOUT)

       
        data = bytearray()
        try:
            while True:
                chunk = client_socket.recv(RECV_BUFFER)
                if not chunk:
                    break
                data.extend(chunk)
                
                if b"\r\n\r\n" in data:
                    break
               
                if len(data) > 2_000_000:
                    break
        except socket.timeout:
            
            pass
        except Exception as e:
            print(f"[THREAD {client_addr}] recv error: {e}")
            client_socket.close()
            return

        if not data:
            client_socket.close()
            return

       
        parsed, headers_bytes, body_bytes = parse_http_request(bytes(data))
        if parsed is None:
           
            try:
               
                resp = b"HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n"
                client_socket.sendall(resp)
            except Exception:
                pass
            client_socket.close()
            return

       
        content_length = int(parsed.headers.get('Content-Length', '0')) if 'Content-Length' in parsed.headers else 0
        already = len(body_bytes)
        to_read = content_length - already
        if to_read > 0:
            
            try:
                while to_read > 0:
                    chunk = client_socket.recv(min(RECV_BUFFER, to_read))
                    if not chunk:
                        break
                    body_bytes += chunk
                    to_read -= len(chunk)
            except socket.timeout:
                pass
            except Exception:
                pass

        
        raw_request = headers_bytes + b"\r\n\r\n" + body_bytes if headers_bytes else bytes(data)

       
        method = parsed.method.upper()

        print(f"[THREAD {client_addr}] Handling {method} for {parsed.path}")

        try:
            if method == "GET":
                
                if parsed.path.startswith("/find/"):
                    http_handler.handle_find(client_socket, parsed, raw_request)
                else:
                    http_handler.handle_get(client_socket, parsed, raw_request)

            elif method == "POST":
               
                if parsed.path.startswith("/upload/") or "multipart/form-data" in parsed.headers.get("Content-Type", ""):
                    
                    http_handler.handle_file_upload(client_socket, parsed, body_bytes)
                else:
                    http_handler.handle_post(client_socket, parsed, raw_request)

            elif method == "FIND":
                http_handler.handle_find(client_socket, parsed, raw_request)

            elif method == "PUT":
                http_handler.handle_put(client_socket, parsed, raw_request)

            else:
                
                try:
                    resp = b"HTTP/1.1 405 Method Not Allowed\r\nContent-Length: 0\r\n\r\n"
                    client_socket.sendall(resp)
                except Exception:
                    pass

        except Exception as e:
            print(f"[THREAD {client_addr}] Exception in handler: {e}")
            try:
                resp = b"HTTP/1.1 500 Internal Server Error\r\nContent-Length: 0\r\n\r\n"
                client_socket.sendall(resp)
            except Exception:
                pass

    finally:
        
        try:
            client_socket.close()
        except Exception:
            pass
        if acquired:
            semaphore.release()
      
        with thread_count_lock:

            global thread_counter
            thread_counter += 1
        print(f"[THREAD {client_addr}] Connection closed")

def start_server(listen_host: str = "0.0.0.0", listen_port: int = DEFAULT_PORT):
    
    try:
        os.makedirs("./uploads", exist_ok=True)
        os.makedirs("./find", exist_ok=True)
    except Exception:
        pass

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_sock.bind((listen_host, listen_port))
        server_sock.listen(MAX_CLIENTS)
    except Exception as e:
        print(f"[MAIN] Failed to bind/listen on {listen_host}:{listen_port} -> {e}")
        server_sock.close()
        return

    print(f"[MAIN] Proxy server listening on {listen_host}:{listen_port}")

    try:
        while True:
            try:
                client_sock, client_addr = server_sock.accept()
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[MAIN] accept error: {e}")
                continue

            print(f"[MAIN] Connection accepted from {client_addr[0]}:{client_addr[1]}")

            
            t = threading.Thread(target=threaded_client_fn, args=(client_sock, f"{client_addr[0]}:{client_addr[1]}"), daemon=True)
            t.start()

    except KeyboardInterrupt:
        print("\n[MAIN] Shutting down due to KeyboardInterrupt")
    finally:
        try:
            server_sock.close()
        except Exception:
            pass
        print("[MAIN] Server closed")

if __name__ == "__main__":
    
    port = DEFAULT_PORT
    if len(sys.argv) >= 2:
        try:
            port_arg = int(sys.argv[1])
            if 1 <= port_arg <= 65535:
                port = port_arg
            else:
                print("[MAIN] Invalid port number, using default 8080")
        except ValueError:
            print("[MAIN] Invalid port arg, using default 8080")

    start_server(listen_port=port)
