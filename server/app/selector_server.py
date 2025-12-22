from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import selectors
import socket
import json
import traceback
from typing import Iterable
from urllib.parse import parse_qs, urlsplit

from app.services.instruments import load_instrument_price_history
from app.price_generator import start_price_generation
from app.services.hurst_exponent import hurst_exponent_minutes_rs_multiprocessed
from app.services.permutation_entropy import permutation_entropy_minutes_multiprocessed
from app.utils.tick_time_converter import Tick, minute_bars_from_ticks

HOST = "0.0.0.0"
PORT = 5000
ALLOWED_ORIGIN = "http://localhost:5173"
# ALLOWED_ORIGIN = "http://192.168.100.94:5173"
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

            if len(segments) == 2 and segments[0] == "instruments":
                resp = handle_price_fetch(segments, query_params)
            elif len(segments) == 3 and segments[0] == "instruments" and segments[2] == "hurst":
                resp = handle_hurst_fetch(segments, query_params)
            elif len(segments) == 3 and segments[0] == "instruments" and segments[2] == "permutation-entropy":
                resp = handle_pe_fetch(segments, query_params)
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


def handle_price_fetch(
    segments: list[str],
    query_params: dict[str, str|list[str]]
    ) -> bytes:
    try:
        minutes_raw = query_params.get("minutes")

        if not isinstance(minutes_raw, str):
            raise TypeError

        minutes = int(minutes_raw)
    except TypeError or ValueError:
        resp = build_http_response(400, "Invalid 'minutes' value\n")

    data = load_instrument_price_history(segments[1], minutes)

    resp_body = json.dumps([tick.to_dict() for tick in data])
    resp = build_http_response(
        200,
        resp_body,
        content_type="application/json; charset=utf-8",
    )
    
    return resp


def handle_hurst_fetch(
    segments: list[str],
    query_params: dict[str, str|list[str]]
    ) -> bytes:
    try:
        minutes_raw = query_params.get("minutes")
        workers_raw = query_params.get("workers")
    
        if not isinstance(minutes_raw, str) or not isinstance(workers_raw, str):
            raise TypeError
        
        minutes = int(minutes_raw)
        workers = int(workers_raw)
    except TypeError or ValueError:
        resp = build_http_response(400, "Invalid query params\n")
    
    result = load_instrument_price_history(segments[1], minutes)

    ticksIterable: Iterable[Tick] = sorted([
        (datetime.fromtimestamp(tick.timestamp), tick.price) for tick in result
    ])
    
    try:
        minutesClosePrice = [bar.close for bar in minute_bars_from_ticks(ticksIterable, fill_missing_minutes=False)]
        hurst_coefficient = hurst_exponent_minutes_rs_multiprocessed(minutesClosePrice, num_workers=workers)
    
        resp_body = json.dumps(hurst_coefficient)
        resp = build_http_response(
            200,
            resp_body,
            content_type="application/json; charset=utf-8",
        )
    except:
        resp = build_http_response(400, "Invalid hurst calculation\n")
        
    return resp


def handle_pe_fetch(
    segments: list[str],
    query_params: dict[str, str|list[str]]
    ) -> bytes:
    try:
        minutes_raw = query_params.get("minutes")
        workers_raw = query_params.get("workers")
    
        if not isinstance(minutes_raw, str) or not isinstance(workers_raw, str):
            raise TypeError
        
        minutes = int(minutes_raw)
        workers = int(workers_raw)
    except TypeError or ValueError:
        resp = build_http_response(400, "Invalid query params\n")
    
    result = load_instrument_price_history(segments[1], minutes)

    ticksIterable: Iterable[Tick] = sorted([
        (datetime.fromtimestamp(tick.timestamp), tick.price) for tick in result
    ])
    
    try:
        minutesClosePrice = [bar.close for bar in minute_bars_from_ticks(ticksIterable, fill_missing_minutes=False)]
        pe_coefficient = permutation_entropy_minutes_multiprocessed(minutesClosePrice, workers=workers)
    
        resp_body = json.dumps(pe_coefficient)
        resp = build_http_response(
            200,
            resp_body,
            content_type="application/json; charset=utf-8",
        )
    except:
        resp = build_http_response(400, "Invalid hurst calculation\n")
        
    return resp


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
