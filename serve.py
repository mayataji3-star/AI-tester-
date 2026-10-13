"""Serve only the synthetic shop, bound to loopback."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
if __name__ == '__main__':
    handler=partial(SimpleHTTPRequestHandler,directory=str(Path(__file__).parent/'shop'))
    print('Shop: http://127.0.0.1:8000 (Ctrl+C to stop)',flush=True)
    ThreadingHTTPServer(('127.0.0.1',8000),handler).serve_forever()
