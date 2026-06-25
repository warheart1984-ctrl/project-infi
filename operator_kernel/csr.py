"""Process-wide Constitutional State Runtime for the operator kernel."""

from __future__ import annotations

from constitutional.runtime import ConstitutionalStateRuntime

from operator_kernel.config import load_config

CSR = ConstitutionalStateRuntime(persist_root=load_config().tasks_dir())
