import importlib.util
import re
import sys
import types
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "backend" / "export.py"


def load_export_module():
    """Load backend/export.py without requiring FastAPI or touching storage."""
    fastapi = types.ModuleType("fastapi")
    fastapi.APIRouter = lambda **_: types.SimpleNamespace(get=lambda *_, **__: (lambda f: f))
    fastapi.Depends = lambda *_args, **_kwargs: None
    fastapi.HTTPException = type("HTTPException", (Exception,), {})
    fastapi.Query = lambda default=None, **_: default

    responses = types.ModuleType("fastapi.responses")
    responses.Response = type("Response", (), {})

    backend = types.ModuleType("backend")
    backend.__path__ = [str(MODULE_PATH.parent)]
    auth = types.ModuleType("backend.auth")
    auth.current_user = None
    boards = types.ModuleType("backend.boards")
    boards.board_ctx = None
    boards.manager = object()
    crdt = types.ModuleType("backend.crdt")
    crdt.BoardDoc = type("BoardDoc", (), {})
    history = types.ModuleType("backend.history")
    history.history_service = object()

    saved = {
        name: sys.modules.get(name)
        for name in ("fastapi", "fastapi.responses", "backend", "backend.auth",
                    "backend.boards", "backend.crdt", "backend.history")
    }
    sys.modules.update({
        "fastapi": fastapi,
        "fastapi.responses": responses,
        "backend": backend,
        "backend.auth": auth,
        "backend.boards": boards,
        "backend.crdt": crdt,
        "backend.history": history,
    })
    try:
        spec = importlib.util.spec_from_file_location("backend.export", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        sys.modules["backend.export"] = module
        spec.loader.exec_module(module)
        return module
    finally:
        for name, value in saved.items():
            if value is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = value


export = load_export_module()


class ExportBboxTests(unittest.TestCase):
    def test_hand_drawn_points_use_shape_origin(self):
        path = {
            "id": "path1", "kind": "path", "x": 1000, "y": 2000,
            "points": [[0, 0], [120, -40], [240, 30]],
        }

        self.assertEqual(export._bbox(path), (1000, 1960, 1240, 2030))

    def test_arrow_points_use_shape_origin(self):
        arrow = {
            "id": "arrow1", "kind": "arrow", "x": 500, "y": 600,
            "points": [[0, 0], [-100, 80], [1000, 1000]],
        }

        self.assertEqual(export._bbox(arrow), (500, 600, 1500, 1600))

    def test_svg_viewbox_matches_actual_drawn_coordinates(self):
        shapes = [
            {"id": "rect", "kind": "rect", "x": 1000, "y": 1000, "w": 100, "h": 80},
            {"id": "path", "kind": "path", "x": 100, "y": 300,
             "points": [[0, 0], [120, -40], [240, 30]], "strokeWidth": 3},
            {"id": "arrow", "kind": "arrow", "x": 400, "y": 200,
             "points": [[0, 0], [-100, 80]]},
        ]

        svg = export.render_svg(shapes, padding=40)
        viewbox = [float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]

        self.assertEqual(viewbox, [60, 160, 1080, 960])
        self.assertIn('d="M 100.0 300.0', svg)
        self.assertIn('x1="400.0" y1="200.0" x2="300.0" y2="280.0"', svg)

    def test_edge_bbox_follows_endpoint_curve_not_shape_origin(self):
        shapes = [
            {"id": "src", "kind": "rect", "x": 0, "y": 0, "w": 100, "h": 100},
            {"id": "dst", "kind": "rect", "x": 200, "y": 0, "w": 100, "h": 100},
            {"id": "edge", "kind": "edge", "from": "src", "to": "dst",
             "x": 0, "y": 0, "w": 0, "h": 0},
        ]

        svg = export.render_svg(shapes, padding=10)
        viewbox = [float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]

        self.assertEqual(viewbox, [-10, -10, 320, 120])

    def test_orphan_edge_does_not_force_origin_into_canvas(self):
        shapes = [
            {"id": "rect", "kind": "rect", "x": 500, "y": 500, "w": 20, "h": 20},
            {"id": "edge", "kind": "edge", "from": "missing", "to": "also-missing"},
        ]

        svg = export.render_svg(shapes, padding=10)
        viewbox = [float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]

        self.assertEqual(viewbox, [490, 490, 40, 40])


if __name__ == "__main__":
    unittest.main()
