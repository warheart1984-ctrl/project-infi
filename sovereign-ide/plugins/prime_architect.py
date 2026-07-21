from __future__ import annotations

from runtime.ulx_bridge import ULXBridge
from runtime.orchestrator import SovereignRuntimeOrchestrator
from runtime.prime_architect import build_prime_architect_runtime


class PrimeArchitectPlugin:
    def __init__(self, ide_api):
        self.ide = ide_api
        self.orchestrator = SovereignRuntimeOrchestrator()
        self.runtime = build_prime_architect_runtime()
        self.ulx = ULXBridge()
        self.ctx = None

    def activate(self):
        self.ctx = self.orchestrator.boot()
        self.ctx.architect = self.runtime
        self.ctx.ulx = self.ulx
        self.ctx.cep = self.orchestrator.cep
        self.ctx.agent_loop = self.orchestrator.agent_loop
        self.ide.register_command("sovereign.start", self.open_shell)
        self.ide.register_command("promotion.approve_selected", self.approve_selected)
        self.ide.register_command("lineage.trace", self.trace_lineage)
        self.ide.register_command("replay.verify", self.verify_replay)
        self.ide.register_command("ulx.compile", self.compile_ulx)
        self.ide.register_command("ulx.run", self.run_ulx)
        self.ide.register_command("ulx.trace", self.trace_ulx)

    def open_shell(self):
        from ui.shell.sovereign_ide_window import SovereignIDEWindow

        shell = SovereignIDEWindow(self.ctx)
        shell.show()
        return shell

    def approve_selected(self):
        return self.runtime.approve_selected()

    def trace_lineage(self):
        return self.runtime.trace_lineage()

    def verify_replay(self):
        return self.runtime.verify_replay()

    def compile_ulx(self):
        return self.ulx.compile()

    def run_ulx(self):
        return self.ulx.run()

    def trace_ulx(self):
        return self.ulx.trace()
