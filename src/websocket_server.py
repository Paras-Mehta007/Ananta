# websocket_server.py
"""
WebSocket server that accepts JSON messages:
  { "message": "...", "model": "llama3:8b" (optional) }
and responds with JSON:
  { "response": "..." }
It forwards the prompt to Ollama HTTP API and returns the result.

Run alongside your existing main.py server; it's non-blocking (runs in its own thread).
"""

import asyncio
import json
import traceback
from typing import Dict
import requests
import websockets

# Configure Ollama endpoint (use IP reachable from this machine)
OLLAMA_API_URL = "http://172.21.5.150:11434/api/generate"  # change if needed

# WebSocket listen config
WS_HOST = "0.0.0.0"   # listen on all interfaces so LAN clients can connect
WS_PORT = 8765        # choose a port not used by other services

# Timeout for HTTP call to Ollama (seconds)
OLLAMA_TIMEOUT = 300

async def call_ollama(prompt: str, model: str = "llama3:8b") -> str:
    """
    Optimized version: streaming enabled, limited tokens, faster response.
    Still uses the llama3:8b model.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,       # ✅ enable streaming for fast token output
        "max_tokens": 200,    # ✅ limit response size for speed
        "num_ctx": 2048,      # ✅ reduce context window
        "temperature": 0.7    # ✅ faster generation
    }

    def sync_request():
        with requests.post(OLLAMA_API_URL, json=payload, stream=True, timeout=OLLAMA_TIMEOUT) as r:
            r.raise_for_status()

            full_output = ""
            for line in r.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    text_piece = chunk.get("response") or chunk.get("text") or ""
                    full_output += text_piece
                except Exception:
                    pass
            return full_output.strip()

    return await asyncio.to_thread(sync_request)

async def ws_handler(ws):
    client = f"{ws.remote_address}"
    print(f"[WS] Connection from {client}")
    try:
        async for message in ws:
            # Expect message is JSON string or plain text prompt
            try:
                data = json.loads(message)
                if isinstance(data, dict) and "message" in data:
                    prompt = data["message"]
                    model = data.get("model", "llama3:8b")
                else:
                    # treat entire payload as prompt if no 'message' key
                    prompt = str(data)
                    model = "llama3:8b"
            except json.JSONDecodeError:
                # message is raw string
                prompt = message
                model = "llama3:8b"

            print(f"[WS] Prompt from {client}: {prompt[:100]}")

            # Call Ollama and send response (handle exceptions)
            try:
                ai_text = await call_ollama(prompt, model=model)
                # normalize to string
                if not isinstance(ai_text, str):
                    ai_text = str(ai_text)
                resp = {"response": ai_text}
            except Exception as e:
                traceback.print_exc()
                resp = {"error": "Failed to call Ollama", "detail": str(e)}

            try:
                await ws.send(json.dumps(resp))
            except Exception:
                print(f"[WS] Failed to send response to {client}")
                break

    except websockets.ConnectionClosed:
        pass
    except Exception:
        traceback.print_exc()
    finally:
        print(f"[WS] Connection closed: {client}")


def start_ws_server_forever(host: str = WS_HOST, port: int = WS_PORT):
    """
    Run the WebSocket server in a new asyncio loop (blocking call).
    Use this from a thread to run alongside your existing server.
    """
    async def runner():
        # ✅ Remove max_size from positional args, pass it as keyword if needed
        server = await websockets.serve(ws_handler, host, port)

        print(f"[WS] WebSocket server listening on ws://{host}:{port}")
        await server.wait_closed()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(runner())
    finally:
        loop.close()


if __name__ == "__main__":
    start_ws_server_forever()
