import unittest

from backend.crdt import BoardDoc, validate_op


class CrdtMoveTests(unittest.TestCase):
    def test_move_applies_dx_to_x_and_dy_to_y(self):
        doc = BoardDoc("test-board")

        add = validate_op({
            "op_id": "site:1", "site": "site", "lam": 1, "ts": 1,
            "type": "add_shape", "base_rev": 0,
            "shape": {"id": "shape1", "kind": "rect", "x": 100, "y": 200,
                      "w": 10, "h": 20},
        })
        move = validate_op({
            "op_id": "site:2", "site": "site", "lam": 2, "ts": 2,
            "type": "move", "base_rev": 0, "id": "shape1",
            "dx": 30, "dy": -40,
        })

        doc.apply_op(add)
        doc.apply_op(move)
        shape = doc.shapes["shape1"]

        self.assertEqual(shape["x"], 130)
        self.assertEqual(shape["y"], 160)


if __name__ == "__main__":
    unittest.main()
