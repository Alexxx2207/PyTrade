from concurrent.futures import ThreadPoolExecutor
import selectors
import socket
import json
import traceback
from urllib.parse import parse_qs

from app.services.instruments import load_instrument_price_history
from app.price_generator import start_price_generation

HOST = "127.0.0.1"
PORT = 5000
ALLOWED_ORIGIN = "http://localhost:5173"
MAX_WORKERS = 8

selector = selectors.DefaultSelector()
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

def accept(server_sock: socket.socket):
    try:
        client_sock, addr = server_sock.accept()
        print(f"[+] Accepted connection from {addr}")
        
        client_sock.setblocking(False)
        
        selector.register(client_sock, selectors.EVENT_READ, read)
    except Exception as e:
        print("[!] Error in accept_connection:", e)
        traceback.print_exc()


def read(client_sock: socket.socket):
    try:
        request_bytes = client_sock.recv(4096)
        if not request_bytes:
            print("[*] Client closed connection")
            
            selector.unregister(client_sock)
            
            client_sock.close()
            return

        selector.unregister(client_sock)

        executor.submit(handle_http_request, client_sock, request_bytes)

    except Exception as e:
        print("[!] Error in handle_client_ready:", e)
        traceback.print_exc()
        try:
            selector.unregister(client_sock)
        except Exception:
            pass
        client_sock.close()


from urllib.parse import urlsplit, parse_qs


def parse_http_request(request_bytes: bytes):
    try:
        text = request_bytes.decode("iso-8859-1")
    except UnicodeDecodeError:
        text = request_bytes.decode("utf-8", errors="replace")

    header_part, _, body = text.partition("\r\n\r\n")
    lines = header_part.split("\r\n")
    request_line = lines[0]
    parts = request_line.split(" ")

    if len(parts) < 3:
        raise ValueError("Malformed request line")

    method, raw_target, http_version = parts[0], parts[1], parts[2]

    url = urlsplit(raw_target)
    path = url.path
    raw_query = url.query

    qs = parse_qs(raw_query, keep_blank_values=True)

    query_params: dict[str, str | list[str]] = {}
    for k, v in qs.items():
        query_params[k] = v[0] if len(v) == 1 else v

    headers: dict[str, str] = {}
    for line in lines[1:]:
        if not line:
            continue
        name, _, value = line.partition(":")
        headers[name.strip().lower()] = value.strip()

    return method, path, query_params, headers, body


def handle_http_request(client_sock: socket.socket, request_bytes: bytes):
    try:
        method, path, query_params, headers, body = parse_http_request(request_bytes)
        print(f"[HTTP] {method} {path} {query_params}")

        if method.upper() == "OPTIONS":
            resp = build_http_response(
                204,
                "",
                content_type="text/plain; charset=utf-8",
            )
        else:
            segments = [s for s in path.split("/") if s]
            ticks_raw = query_params.get("ticks")

            if len(segments) == 2 and segments[0] == "instruments" and isinstance(ticks_raw, str):
                try:
                    ticks = int(ticks_raw)
                except ValueError:
                    resp = build_http_response(400, "Invalid 'ticks' value\n")
                else:
                    data = load_instrument_price_history(segments[1], ticks)
                    resp_body = json.dumps(data)
                    resp = build_http_response(
                        200,
                        resp_body,
                        content_type="application/json; charset=utf-8",
                    )
            else:
                resp = build_http_response(404, f"Not found: {path}\n")

    except Exception as e:
        print("[!] Error in handle_http_request:", e)
        traceback.print_exc()
        resp = build_http_response(500, "Internal Server Error\n")

    try:
        client_sock.sendall(resp)
    except Exception as e:
        print("[!] Error sending response:", e)
        traceback.print_exc()
    finally:
        try:
            client_sock.close()
        except Exception:
            pass


def build_http_response(
    status_code: int,
    body: str,
    content_type: str = "text/plain; charset=utf-8",
    extra_headers: dict[str, str] | None = None,
) -> bytes:
    reason = {
        200: "OK",
        204: "No Content",
        400: "Bad Request",
        404: "Not Found",
        500: "Internal Server Error",
    }.get(status_code, "OK")

    body_bytes = body.encode("utf-8")

    headers = {
        "Content-Type": content_type,
        "Content-Length": str(len(body_bytes)),
        "Connection": "close",
        "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
    }

    if extra_headers:
        headers.update(extra_headers)

    header_lines = [f"HTTP/1.1 {status_code} {reason}"]
    header_lines += [f"{k}: {v}" for k, v in headers.items()]
    header_lines += ["", ""]

    header_bytes = "\r\n".join(header_lines).encode("ascii")
    return header_bytes + body_bytes


def create_listen_socket(host: str, port: int) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen()
    sock.setblocking(False)
    return sock


def main():
    server_sock = create_listen_socket(HOST, PORT)
    print(f"[*] Listening on {HOST}:{PORT}")

    selector.register(server_sock, selectors.EVENT_READ, accept)

    try:
        while True:
            events = selector.select(timeout=1.0)
            for key, _ in events:
                callback = key.data
                callback(key.fileobj)
    except KeyboardInterrupt:
        print("\n[!] Shutting down...")
    finally:
        selector.close()
        server_sock.close()
        executor.shutdown(wait=False)


if __name__ == "__main__":
    start_price_generation()
    main()
