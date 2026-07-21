from __future__ import annotations

from runtime.codex_loader import CodexLoader
from runtime.agent_loop import build_sovereign_environment
from runtime.federation_bootstrapper import FederationBootstrapper
from runtime.prime_architect import build_prime_architect_runtime
from runtime.temporal import TemporalAPI
from cep.client import CEPClient
from runtime.state import SovereignRuntimeContext


class SovereignRuntimeOrchestrator:
    def __init__(self, codex: CodexLoader | None = None, federation: FederationBootstrapper | None = None):
        self.codex = codex or CodexLoader()
        self.federation = federation or FederationBootstrapper(self.codex)
        self.architect = build_prime_architect_runtime()
        self.cep = None
        self.agent_loop = None
        self.temporal_api = None
        self.cep_client = None
        self.ctx = None

    def boot(self):
        self.codex.load_all()
        self.federation.bootstrap()
        self.agent_loop = build_sovereign_environment()
        self.cep = self.agent_loop.cep
        self.temporal_api = TemporalAPI(self.agent_loop.replay_store)
        self.cep_client = CEPClient(self.cep)
        self.ctx = SovereignRuntimeContext(
            codex=self.codex,
            federation=self.federation,
            architect=self.architect,
            cep=self.cep,
            cep_client=self.cep_client,
            agent_loop=self.agent_loop,
            temporal_api=self.temporal_api,
        )
        return self.ctx
