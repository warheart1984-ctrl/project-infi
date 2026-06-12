from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from src.usl.lift.disasm import get_disasm_backend
from src.usl.lift.disasm.linear_x86_64 import LinearX86_64Backend
from src.usl.lift.disasm.aarch64 import LinearAarch64Backend


class DisasmBackendTests(unittest.TestCase):
    def test_default_linear_x86_64(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("USL_DISASM_BACKEND", None)
            backend = get_disasm_backend("x86_64")
        self.assertIsInstance(backend, LinearX86_64Backend)
        insns = backend.decode_instructions(bytes.fromhex("0f05c3"), 0x1000)
        kinds = [i.kind for i in insns]
        self.assertIn("syscall", kinds)
        self.assertIn("ret", kinds)

    def test_linear_aarch64_routing(self) -> None:
        backend = get_disasm_backend("aarch64")
        self.assertIsInstance(backend, LinearAarch64Backend)
        insns = backend.decode_instructions(bytes.fromhex("280080d2010000d4"), 0x400078)
        kinds = [i.kind for i in insns]
        self.assertIn("syscall", kinds)

    def test_capstone_falls_back_to_linear_when_unavailable(self) -> None:
        with patch.dict(os.environ, {"USL_DISASM_BACKEND": "capstone"}):
            backend = get_disasm_backend("x86_64")
        self.assertIsInstance(backend, LinearX86_64Backend)


if __name__ == "__main__":
    unittest.main()
