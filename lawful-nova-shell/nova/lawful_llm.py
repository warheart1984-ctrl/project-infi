"""Composed lawful LLM runtime for Nova over UL, LSG, Voss, and RSL."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import hmac
import json
from pathlib import Path
import re
from typing import Any, Iterable

from nova.exceptions import GovernanceViolationError
from nova.governance import ledger
from nova.governance.proof_gate import require_admitted, run_proof_gate
from nova.identity import NovaIdentity, declare_identity


MemoryFact = tuple[str, str, str]
TOOL_BY_CAPABILITY = {
    "search": "search",
    "files": "files",
    "code": "code",
    "memory_write": "memory_write",
    "graph_query": "graph_query",
    "summarize": "summarization",
    "planning": "planning",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _trace_id(*, instance_id: str, tenant_id: str, capability: str, prompt: str) -> str:
    seed = f"{instance_id}|{tenant_id}|{capability}|{_sha256_text(prompt)}"
    return "nova-turn-" + _sha256_text(seed)[:16]


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

    def parse(self, prompt: str) -> dict[str, object]:
        words = re.findall(r"[A-Za-z0-9_'-]+", prompt.lower())
        intent = words[0] if words else "observe"
        subject = " ".join(words[1:]) if len(words) > 1 else prompt.strip().lower()
        constraints = self._extract_constraints(prompt)
        risk_level = self._risk_level(words)
        return {
            "grammar": "UL",
            "frame_version": "ul.intent_frame.v1",
            "intent": intent,
            "subject": subject,
            "constraints": constraints,
            "evidence_needed": "lsg_grounding" if intent in {"explain", "summarize", "compare"} else "none",
            "risk_level": risk_level,
            "output_contract": {
                "format": self._output_format(intent),
                "must_cite_lsg": intent in {"explain", "summarize", "compare"},
                "max_style": "concise",
            },
            "tokens": words,
        }

    def _extract_constraints(self, prompt: str) -> list[str]:
        lowered = prompt.lower()
        constraints: list[str] = []
        for marker in ("without", "only", "must", "do not", "don't"):
            if marker in lowered:
                constraints.append(marker)
        return constraints

    def _risk_level(self, words: list[str]) -> str:
        high_risk = {"delete", "execute", "write", "spend", "deploy", "secret", "key"}
        medium_risk = {"code", "search", "file", "plan", "route"}
        token_set = set(words)
        if token_set & high_risk:
            return "high"
        if token_set & medium_risk:
            return "medium"
        return "low"

    def _output_format(self, intent: str) -> str:
        if intent in {"explain", "summarize", "compare"}:
            return "explanation"
        if intent in {"plan", "route"}:
            return "plan"
        return "answer"


@dataclass(frozen=True)
class LongScaleGraph:
    """In-memory LSG substrate for relationships used by Nova Cortex."""

    facts: tuple[MemoryFact, ...] = ()

    def traverse(self, ul_packet: dict[str, object]) -> dict[str, object]:
        tokens = set(ul_packet.get("tokens", []))
        matches = []
        for source, relation, target in self.facts:
            if source.lower() in tokens or target.lower() in tokens:
                fact = f"{source} {relation} {target}"
                matches.append({"fact": fact, "score": 1.0, "source": "inline"})
        return {
            "substrate": "LSG",
            "facts_used": [match["fact"] for match in matches],
            "matches": matches,
        }


class LongScaleGraphStore:
    """Persistent tenant-scoped JSONL graph store for Nova memory."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def add_fact(
        self,
        *,
        tenant_id: str,
        source: str,
        relation: str,
        target: str,
        confidence: float = 1.0,
        source_ref: str = "operator",
    ) -> dict[str, Any]:
        record = {
            "tenant_id": tenant_id,
            "source": source,
            "relation": relation,
            "target": target,
            "confidence": max(0.0, min(1.0, float(confidence))),
            "source_ref": source_ref,
            "created_at": _now_iso(),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True, ensure_ascii=True) + "\n")
        return record

    def query(self, *, tenant_id: str, ul_packet: dict[str, object], limit: int = 5) -> dict[str, object]:
        tokens = set(ul_packet.get("tokens", []))
        matches: list[dict[str, Any]] = []
        for record in self._iter_records():
            if record.get("tenant_id") != tenant_id:
                continue
            source = str(record.get("source") or "")
            relation = str(record.get("relation") or "")
            target = str(record.get("target") or "")
            haystack = set(re.findall(r"[A-Za-z0-9_'-]+", f"{source} {relation} {target}".lower()))
            overlap = tokens & haystack
            if not overlap:
                continue
            confidence = float(record.get("confidence") or 0.0)
            score = round(confidence * len(overlap), 6)
            matches.append(
                {
                    **record,
                    "fact": f"{source} {relation} {target}",
                    "score": score,
                }
            )
        matches.sort(key=lambda item: item["score"], reverse=True)
        selected = matches[:limit]
        return {
            "substrate": "LSG",
            "facts_used": [item["fact"] for item in selected],
            "matches": selected,
        }

    def _iter_records(self) -> Iterable[dict[str, Any]]:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                cleaned = line.strip()
                if not cleaned:
                    continue
                yield json.loads(cleaned)


class NovaCortex:
    """Deterministic cognitive core: UL grammar over LSG memory."""

    def __init__(self, *, provider: Any | None = None, lsg_store: LongScaleGraphStore | None = None) -> None:
        self.cognition_count = 0
        self.provider = provider
        self.lsg_store = lsg_store

    def think(
        self,
        *,
        prompt: str,
        tenant_id: str,
        memory_facts: Iterable[MemoryFact],
    ) -> dict[str, object]:
        self.cognition_count += 1
        ul = UnifiedLanguage().parse(prompt)
        if self.lsg_store is not None:
            lsg = self.lsg_store.query(tenant_id=tenant_id, ul_packet=ul)
            inline_lsg = LongScaleGraph(tuple(memory_facts)).traverse(ul)
            if inline_lsg["facts_used"]:
                lsg = {
                    "substrate": "LSG",
                    "facts_used": list(lsg["facts_used"]) + list(inline_lsg["facts_used"]),
                    "matches": list(lsg["matches"]) + list(inline_lsg["matches"]),
                }
        else:
            lsg = LongScaleGraph(tuple(memory_facts)).traverse(ul)
        if self.provider is not None:
            return self._think_with_provider(prompt=prompt, ul=ul, lsg=lsg)
        return {
            "core": "Nova Cortex",
            "ul": ul,
            "lsg": lsg,
            "text": self._compose_text(ul=ul, lsg=lsg),
        }

    def _compose_text(self, *, ul: dict[str, object], lsg: dict[str, object]) -> str:
        subject = ul.get("subject") or "the request"
        facts = lsg["facts_used"]
        if facts:
            return f"Under RSL, Nova Cortex reads {subject}: " + "; ".join(facts) + "."
        return f"Under RSL, Nova Cortex reads {subject} with no matching LSG facts."

    def _think_with_provider(
        self,
        *,
        prompt: str,
        ul: dict[str, object],
        lsg: dict[str, object],
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

    tools: dict[str, Any] | None = None

    def route(self, *, prompt: str) -> dict[str, object]:
        tool_calls: list[dict[str, Any]] = []
        tool_name = TOOL_BY_CAPABILITY.get(self.capability)
        if tool_name and self.tools and tool_name in self.tools:
            payload = {
                "tenant_id": self.tenant_id,
                "capability": self.capability,
                "prompt": prompt,
            }
            result = self.tools[tool_name](payload)
            tool_calls.append({"tool": tool_name, "result": result})
        return {
            "kernel": "API Kernel",
            "tenant_id": self.tenant_id,
            "capability": self.capability,
            "channel": f"{self.tenant_id}:{self.capability}",
            "tool_calls": tool_calls,
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
        prompt: str,
    ) -> dict[str, object]:
        memory_facts_used = list((nova_cortex.get("lsg") or {}).get("facts_used") or [])
        tool_calls = list(api_kernel.get("tool_calls") or [])
        output_sha256 = _sha256_text(str(nova_cortex["text"]))
        payload = {
            "instance_id": identity.instance_id,
            "tenant_id": api_kernel["tenant_id"],
            "capability": api_kernel["capability"],
            "decision": "EXECUTED",
            "rsl": rsl["status"],
            "policy_decision": rsl["status"],
            "prompt_sha256": _sha256_text(prompt),
            "output_sha256": output_sha256,
            "text_sha256": output_sha256,
            "memory_facts_used": memory_facts_used,
            "tool_calls": tool_calls,
        }
        payload["identity"] = {
            "instance_id": identity.instance_id,
            "tier": identity.tier,
            "operator_session_id": identity.operator_session_id,
            "tenant_id": api_kernel["tenant_id"],
        }
        payload["trace"] = {
            "trace_id": _trace_id(
                instance_id=identity.instance_id,
                tenant_id=api_kernel["tenant_id"],
                capability=api_kernel["capability"],
                prompt=prompt,
            ),
            "stages": [
                "rsl.validate",
                "api_kernel.route",
                "nova_cortex.think",
                "voss.execute",
            ],
            "ledger_event": "nova.lawful_llm.executed",
        }
        payload["authority_boundary"] = {
            "operator_authority": "external",
            "runtime_authority": "execute_after_rsl",
            "rsl_decision": rsl["status"],
            "tool_boundary": "api_kernel",
        }
        payload["reproducibility"] = {
            "prompt_sha256": payload["prompt_sha256"],
            "output_sha256": output_sha256,
            "text_sha256": output_sha256,
            "deterministic_core": self._is_deterministic_core(nova_cortex),
            "memory_facts_sha256": _sha256_text(json.dumps(memory_facts_used, sort_keys=True)),
            "tool_calls_sha256": _sha256_text(json.dumps(tool_calls, sort_keys=True)),
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

    def _is_deterministic_core(self, nova_cortex: dict[str, object]) -> bool:
        return not bool(nova_cortex.get("provider"))

    def sign_receipt(self, payload: dict[str, Any]) -> dict[str, Any]:
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        signature = hmac.new(
            self._signing_secret,
            serialized.encode("utf-8"),
            sha256,
        ).hexdigest()
        receipt = {"payload": serialized, "signature": signature, "algorithm": "HMAC-SHA256"}
        receipt["verified"] = self.verify_receipt(receipt)
        return receipt

    def verify_receipt(self, receipt: dict[str, Any]) -> bool:
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
    receipt: dict[str, Any]


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
        lsg_store: LongScaleGraphStore | None = None,
        tools: dict[str, Any] | None = None,
    ) -> None:
        self.identity = identity or declare_identity(
            tier="nova",
            operator_session_id=operator_session_id,
        )
        require_admitted(run_proof_gate(self.identity, operator_session_active=True))
        self.law = law or RuntimeSystemLaw()
        self.cortex = NovaCortex(provider=provider, lsg_store=lsg_store)
        self.voss = VossRuntime(signing_secret=signing_secret)
        self.tools = tools or {}

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
        api_kernel = APIKernel(
            tenant_id=tenant_id,
            capability=capability,
            tools=self.tools,
        ).route(prompt=prompt)
        nova_cortex = self.cortex.think(
            prompt=prompt,
            tenant_id=tenant_id,
            memory_facts=memory_facts,
        )
        voss_runtime = self.voss.execute(
            identity=self.identity,
            api_kernel=api_kernel,
            nova_cortex=nova_cortex,
            rsl=rsl,
            prompt=prompt,
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

    def verify_receipt(self, receipt: dict[str, Any]) -> bool:
        return self.voss.verify_receipt(receipt)
