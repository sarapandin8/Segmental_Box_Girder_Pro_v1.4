"""Enable native-fault diagnostics before Streamlit imports the app."""
from __future__ import annotations

import faulthandler
import sys

try:
    faulthandler.enable(file=sys.stderr, all_threads=True)
except Exception:
    pass

print("[SBGP STARTUP] sitecustomize loaded", file=sys.stderr, flush=True)
