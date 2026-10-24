"""Write the API contract to ../openapi.json (the frontend generates its types from it).

uv run python scripts/export_openapi.py && (cd ../frontend && npm run gen:api)
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["MOCK_WHOP"] = "true"  # the contract includes the dev routes, like the tests see it

from app.main import app  # noqa: E402

out = Path(__file__).resolve().parents[2] / "openapi.json"
out.write_text(json.dumps(app.openapi(), indent=2) + "\n")
print(f"wrote {out}")
