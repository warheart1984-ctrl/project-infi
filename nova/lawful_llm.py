"""Composed lawful LLM runtime for Nova over UL, LSG, Voss, and RSL."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from hashlib import sha256
import hmac
import json
import re
from typing import Any, Iterable

from nova.exceptions import GovernanceViolationError
from nova.governance import ledger
from nova.governance.proof_gate import require_admitted, run_proof_gate
from nova.identity import NovaIdentity, declare_identity


MemoryFact = tuple[str, str, str]


@dataclass(frozen=True)
class RuntimeSystemLaw:
    """Constitutional checks shared by the composed runtime."""

    allowed_capabilities: frozenset[str] = frozenset({"observe", "reason", "summarize"})
    max_prompt_chars: int = 4000

    def validate(self, *, tenant_id: str, capability: str, prompt: str) -> dict[str, str]:
        if not tenant_id.strip():
            raise GovernanceViolationError("tenant_id is required", code="RSL-TENANT-REQUIRED")
        if not capability.strip():
            raise GovernanceViolationError("capability is required", code="RSL-CAPABILITY-REQUIRED")
        if capability not in self.allowed_capabilities:
            raise GovernanceViolationError(
                f"capability denied: {capability}",
                code="RSL-CAPABILITY-DENIED",
            )
        if not prompt.strip():
            raise GovernanceViolationError("prompt is required", code="RSL-PROMPT-REQUIRED")
        if len(prompt) > self.max_prompt_chars:
            raise GovernanceViolationError("prompt exceeds RSL limit", code="RSL-PROMPT-LIMIT")
        return {"status": "SATISFIED"}


@dataclass(frozen=True)
class UnifiedLanguage:
    """Small deterministic UL parser for lawful cognition packets."""

    def parse(self, prompt: str) -> dict[str, str | list[str]]:
        words = re.findall(r"[A-Za-z0-9_'-]+", prompt.lower())
        intent = words[0] if words else "observe"
        subject = " ".join(words[1:]) if len(words) > 1 else prompt.strip().lower()
        return {
            "grammar": "UL",
            "intent": intent,
            "subject": subject,
            "tokens": words,
        }


@dataclass(frozen=True)
class LongScaleGraph:
    """In-memory LSG substrate for relationships used by Nova Cortex."""

    facts: tuple[MemoryFact, ...] = ()

    def traverse(self, ul_packet: dict[str, str | list[str]]) -> dict[str, list[str]]:
        tokens = set(ul_packet.get("tokens", []))
        facts_used = [
            f"{source} {relation} {target}"
            for source, relation, target in self.facts
            if source.lower() in tokens or target.lower() in tokens
        ]
        return {"substrate": "LSG", "facts_used": facts_used}


class NovaCortex:
    """Deterministic cognitive core: UL grammar over LSG memory."""

    def __init__(self, *, provider: Any | None = None) -> None:
        self.cognition_count = 0
        self.provider = provider

    def think(self, *, prompt: str, memory_facts: Iterable[MemoryFact]) -> dict[str, object]:
        self.cognition_count += 1
        ul = UnifiedLanguage().parse(prompt)
        lsg = LongScaleGraph(tuple(memory_facts)).traverse(ul)
        if self.provider is not None:
            return self._think_with_provider(prompt=prompt, ul=ul, lsg=lsg)
        return {
            "core": "Nova Cortex",
            "ul": ul,
            "lsg": lsg,
            "text": self._compose_text(ul=ul, lsg=lsg),
        }

    def _compose_text(self, *, ul: dict[str, object], lsg: dict[str, list[str]]) -> str:
        subject = ul.get("subject") or "the request"
        facts = lsg["facts_used"]
        if facts:
            return f"Under RSL, Nova Cortex reads {subject}: " + "; ".join(facts) + "."
        return f"Under RSL, Nova Cortex reads {subject} with no matching LSG facts."

    def _think_with_provider(
        self,
        *,
        prompt: str,
        ul: dict[str, str | list[str]],
        lsg: dict[str, list[str]],
    ) -> dict[str, object]:
        facts = "\n".join(f"- {fact}" for fact in lsg["facts_used"]) or "- no matching LSG facts"
        messages = [
            {
                "role": "system",
                "content": (
                    "You are Nova Cortex. Respond under RSL. Use UL intent and LSG facts.\n"
                    f"UL intent: {ul['intent']}\n"
                    f"UL subject: {ul['subject']}\n"
                    f"LSG facts:\n{facts}"
                ),
            },
            {"role": "user", "content": prompt},
        ]
        model = getattr(self.provider, "model", None)
        response = asyncio.run(
            self.provider.invoke(
                messages,
                model=model,
                max_tokens=2048,
                temperature=0.7,
            )
        )
        return {
            "core": "Nova Cortex",
            "ul": ul,
            "lsg": lsg,
            "text": response.content,
            "provider": response.provider or getattr(self.provider, "provider_id", None),
            "model": response.model or model,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
        }


@dataclass(frozen=True)
class APIKernel:
    """Tenant-scoped dispatch spine."""

    tenant_id: str
    capability: str

    def route(self) -> dict[str, str]:
        return {
            "kernel": "API Kernel",
            "tenant_id": self.tenant_id,
            "capability": self.capability,
            "channel": f"{self.tenant_id}:{self.capability}",
        }


class VossRuntime:
    """Immutable enforcement and receipt-signing runtime."""

    def __init__(self, *, signing_secret: str) -> None:
        self._signing_secret = signing_secret.encode("utf-8")

    def execute(
        self,
        *,
        identity: NovaIdentity,
        api_kernel: dict[str, str],
        nova_cortex: dict[str, object],
        rsl: dict[str, str],
    ) -> dict[str, object]:
        payload = {
            "instance_id": identity.instance_id,
            "tenant_id": api_kernel["tenant_id"],
            "capability": api_kernel["capability"],
            "decision": "EXECUTED",
            "rsl": rsl["status"],
            "text_sha256": sha256(str(nova_cortex["text"]).encode("utf-8")).hexdigest(),
        }
        if nova_cortex.get("provider"):
            payload["provider"] = str(nova_cortex["provider"])
        if nova_cortex.get("model"):
            payload["model"] = str(nova_cortex["model"])
        receipt = self.sign_receipt(payload)
        ledger.append_jsonl(
            {
                "event": "nova.lawful_llm.executed",
                "tenant_id": api_kernel["tenant_id"],
                "capability": api_kernel["capability"],
                "receipt_sha256": sha256(receipt["payload"].encode("utf-8")).hexdigest(),
            }
        )
        return {
            "runtime": "Voss Runtime",
            "decision": "EXECUTED",
            "receipt": receipt,
        }

    def sign_receipt(self, payload: dict[str, str]) -> dict[str, str]:
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        signature = hmac.new(
            self._signing_secret,
            serialized.encode("utf-8"),
            sha256,
        ).hexdigest()
        return {"payload": serialized, "signature": signature, "algorithm": "HMAC-SHA256"}

    def verify_receipt(self, receipt: dict[str, str]) -> bool:
        expected = hmac.new(
            self._signing_secret,
            receipt["payload"].encode("utf-8"),
            sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, receipt.get("signature", ""))


@dataclass(frozen=True)
class LawfulTurn:
    text: str
    gates_of_wonder: dict[str, str]
    nova_cortex: dict[str, object]
    api_kernel: dict[str, str]
    voss_runtime: dict[str, object]
    rsl: dict[str, str]
    receipt: dict[str, str]


class LawfulLLM:
    """Facade for Gates of Wonder -> Nova Cortex -> API Kernel -> Voss -> RSL."""

    def __init__(
        self,
        *,
        operator_session_id: str,
        signing_secret: str,
        law: RuntimeSystemLaw | None = None,
        identity: NovaIdentity | None = None,
        provider: Any | None = None,
    ) -> None:
        self.identity = identity or declare_identity(
            tier="nova",
            operator_session_id=operator_session_id,
        )
        require_admitted(run_proof_gate(self.identity, operator_session_active=True))
        self.law = law or RuntimeSystemLaw()
        self.cortex = NovaCortex(provider=provider)
        self.voss = VossRuntime(signing_secret=signing_secret)

    @property
    def cognition_count(self) -> int:
        return self.cortex.cognition_count

    def ask(
        self,
        prompt: str,
        *,
        tenant_id: str,
        capability: str,
        memory_facts: Iterable[MemoryFact] = (),
    ) -> LawfulTurn:
        rsl = self.law.validate(tenant_id=tenant_id, capability=capability, prompt=prompt)
        api_kernel = APIKernel(tenant_id=tenant_id, capability=capability).route()
        nova_cortex = self.cortex.think(prompt=prompt, memory_facts=memory_facts)
        voss_runtime = self.voss.execute(
            identity=self.identity,
            api_kernel=api_kernel,
            nova_cortex=nova_cortex,
            rsl=rsl,
        )
        gates = {
            "interface": "Gates of Wonder",
            "presentation": "human_readable_insight",
        }
        return LawfulTurn(
            text=str(nova_cortex["text"]),
            gates_of_wonder=gates,
            nova_cortex=nova_cortex,
            api_kernel=api_kernel,
            voss_runtime=voss_runtime,
            rsl=rsl,
            receipt=voss_runtime["receipt"],
        )

    def verify_receipt(self, receipt: dict[str, str]) -> bool:
        return self.voss.verify_receipt(receipt)
