from __future__ import annotations

import os


class FederationBootstrapper:
    def __init__(self, codex_loader, port: int | None = None):
        self.codex = codex_loader
        self.port = port if port is not None else int(os.environ.get("FEDERATION_PORT", "8787"))
        self.bootstrapped = False

    def bootstrap(self):
        self.bootstrapped = True
        message = "[Federation] Bootstrap: harmonics, epochs, lineage, CAS-1 online."
        print(message)
        return {
            "bootstrapped": self.bootstrapped,
            "message": message,
            "port": self.port,
        }
