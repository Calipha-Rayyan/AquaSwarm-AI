"""AquaSwarm AI Backend Package.

Provides platform stability fixes for Windows asyncio proactor socket closures.
"""
from __future__ import annotations

import sys

# Silence [WinError 10054] ConnectionResetError on Windows when browser tabs close/reload.
if sys.platform == "win32":
    try:
        import socket
        from asyncio.proactor_events import _ProactorBasePipeTransport

        _orig_call_connection_lost = _ProactorBasePipeTransport._call_connection_lost

        def _silence_connection_lost(self, exc):
            try:
                _orig_call_connection_lost(self, exc)
            except (ConnectionResetError, ConnectionAbortedError):
                pass
            except OSError as err:
                if getattr(err, "winerror", None) in (10054, 10053, 10038):
                    pass
                else:
                    raise
            finally:
                if hasattr(self, "_sock") and self._sock is not None:
                    try:
                        self._sock.close()
                    except Exception:
                        pass
                    self._sock = None
                server = getattr(self, "_server", None)
                if server is not None:
                    try:
                        server._detach(self)
                    except Exception:
                        pass
                    self._server = None
                self._called_connection_lost = True

        _ProactorBasePipeTransport._call_connection_lost = _silence_connection_lost
    except Exception:
        pass
