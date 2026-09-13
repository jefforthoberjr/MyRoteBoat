"""Generate openapi.yaml (repo root) from the Flask routes' docstrings.

Each route handler in src/main.py carries an OpenAPI block in its docstring
after a "---" line; apispec's FlaskPlugin extracts them. Tags separate the
two API surfaces: [ui] (browser-facing) vs [agent] (runtime assistant).

Run from the repo root (venv active):

    python tools/generate_swagger.py

Local document only -- not served by the app (may change later). Re-run
after any route add/change; the dev assistant does this agentically."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from apispec import APISpec
from apispec_webframeworks.flask import FlaskPlugin

from main import create_app

OUTPUT_PATH = REPO_ROOT / "openapi.yaml"


def build_spec():
    app = create_app()
    spec = APISpec(
        title="MyRoteBoat",
        version="0.1.0",
        openapi_version="3.0.3",
        info={"description": "Local single-user dossier app. Two surfaces: "
                             "the ui tag is browser-facing, the agent tag "
                             "is the runtime assistant's localhost API."},
        plugins=[FlaskPlugin()],
    )
    with app.test_request_context():
        for name in sorted(app.view_functions):
            if name != "static":
                spec.path(view=app.view_functions[name], app=app)
    return spec


# MAIN
built = build_spec()
OUTPUT_PATH.write_text(built.to_yaml())
print("wrote " + str(OUTPUT_PATH))
