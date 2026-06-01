from __future__ import annotations

from dataclasses import asdict
import json
import re

from story_forge.contracts.pipeline import TARGET_MOVIE
from story_forge.contracts.validators import build_contract
from story_forge.contracts.translation import Act, SceneGrammar, SceneUnit, TranslationLaneInput
from story_forge.llm import TranslationProposal


_EMOTIONAL_KEYWORDS = {
    "dread": ("dread", "fear", "terror", "ominous", "wrong", "unsettled"),
    "longing": ("longing", "yearning", "desire", "want", "ache"),
    "grief": ("grief", "mourning", "loss", "funeral", "dead"),
    "wonder": ("wonder", "awe", "strange", "beautiful", "radiant"),
    "tension": ("tension", "pressure", "threat", "knife", "risk", "danger"),
    "intimacy": ("intimate", "touch", "kiss", "confession", "close"),
}

_MOVIE_TARGET_BLOCKS_PER_SCENE = 14
_MOVIE_MIN_BLOCKS_FOR_MULTI_SCENE_ACT = 20
_MOVIE_MAX_SCENES = 72


class DeterministicTranslationLane:
    """Deterministic translation lane that extracts a lawful scene grammar from prose."""

    def run(self, lane_input: TranslationLaneInput) -> SceneGrammar:
        normalized_text = self._normalize_text(lane_input.raw_text)
        blocks = self._text_blocks(normalized_text)
        acts = self._build_acts(blocks, lane_input.title, target=lane_input.target)
        if not any(act.scenes for act in acts) and normalized_text:
            acts = [
                Act(
                    act_id="act_01",
                    title=lane_input.title.strip() or "Act One",
                    scenes=[
                        SceneUnit(
                            scene_id="scene_001",
                            title=self._scene_title(normalized_text, 1),
                            summary=self._scene_summary(normalized_text),
                            source_span="block_001",
                            emotional_tags=self._emotional_tags(normalized_text),
                            structural_markers=self._scene_markers(normalized_text),
                        )
                    ],
                )
            ]
        scenes = [scene for act in acts for scene in act.scenes]
        emotional_tags = self._emotional_tags(normalized_text)
        structural_markers = self._structural_markers(
            blocks,
            acts,
            scenes,
            target=lane_input.target,
        )

        return SceneGrammar(
            title=lane_input.title.strip() or "Untitled Source",
            acts=acts,
            total_scenes=len(scenes),
            emotional_tags=emotional_tags,
            structural_markers=structural_markers,
            implemented=True,
            valid=bool(scenes),
        )

    def _normalize_text(self, raw_text: str) -> str:
        text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _text_blocks(self, text: str) -> list[tuple[int, str]]:
        if not text:
            return []
        blocks: list[tuple[int, str]] = []
        for raw_index, block in enumerate(re.split(r"\n\s*\n", text), start=1):
            normalized = block.strip()
            if not normalized or self._is_separator_block(normalized):
                continue
            blocks.append((raw_index, normalized))
        return blocks

    def _build_acts(
        self,
        blocks: list[tuple[int, str]],
        fallback_title: str,
        *,
        target: str,
    ) -> list[Act]:
        if not blocks:
            return [
                Act(
                    act_id="act_01",
                    title=fallback_title.strip() or "Act One",
                    scenes=[],
                )
            ]

        act_inputs = self._partition_acts(blocks, fallback_title)
        if target == TARGET_MOVIE:
            desired_scene_count = self._desired_movie_scene_count(act_inputs)
            scene_allocations = self._allocate_movie_scene_counts(act_inputs, desired_scene_count)
        else:
            scene_allocations = [len(act_blocks) for _, act_blocks in act_inputs]

        acts: list[Act] = []
        scene_index = 1
        for act_index, ((act_title, act_blocks), scene_count) in enumerate(
            zip(act_inputs, scene_allocations),
            start=1,
        ):
            scene_groups = (
                self._chunk_movie_blocks(act_blocks, scene_count)
                if target == TARGET_MOVIE
                else [[block] for block in act_blocks]
            )
            scenes: list[SceneUnit] = []
            for chunk in scene_groups:
                scene_text = "\n\n".join(block for _, block in chunk)
                structural_markers = self._scene_markers(scene_text)
                if target == TARGET_MOVIE and len(chunk) > 1:
                    structural_markers = self._merge_unique(structural_markers, ["movie_chunked"])
                scenes.append(
                    SceneUnit(
                        scene_id=f"scene_{scene_index:03d}",
                        title=self._scene_title(scene_text, scene_index),
                        summary=self._scene_summary(scene_text),
                        source_span=self._source_span(chunk),
                        emotional_tags=self._emotional_tags(scene_text),
                        structural_markers=structural_markers,
                    )
                )
                scene_index += 1
            if scenes:
                acts.append(
                    Act(
                        act_id=f"act_{act_index:02d}",
                        title=act_title,
                        scenes=scenes,
                    )
                )
        return acts

    def _partition_acts(
        self,
        blocks: list[tuple[int, str]],
        fallback_title: str,
    ) -> list[tuple[str, list[tuple[int, str]]]]:
        current_title = fallback_title.strip() or "Act One"
        current_blocks: list[tuple[int, str]] = []
        acts: list[tuple[str, list[tuple[int, str]]]] = []

        for block_index, block in blocks:
            heading = self._classify_heading(block)
            if heading is not None:
                if current_blocks:
                    acts.append((current_title, current_blocks))
                    current_blocks = []
                current_title = heading
                continue
            current_blocks.append((block_index, block))

        if current_blocks:
            acts.append((current_title, current_blocks))
        return acts or [(fallback_title.strip() or "Act One", [])]

    def _desired_movie_scene_count(
        self,
        acts: list[tuple[str, list[tuple[int, str]]]],
    ) -> int:
        total_blocks = sum(len(blocks) for _, blocks in acts)
        desired = round(total_blocks / _MOVIE_TARGET_BLOCKS_PER_SCENE)
        desired = max(12, desired)
        desired = max(len(acts) * 2, desired)
        return min(_MOVIE_MAX_SCENES, desired)

    def _allocate_movie_scene_counts(
        self,
        acts: list[tuple[str, list[tuple[int, str]]]],
        desired_scene_count: int,
    ) -> list[int]:
        if not acts:
            return []

        minimums = [
            2 if len(blocks) >= _MOVIE_MIN_BLOCKS_FOR_MULTI_SCENE_ACT else 1
            for _, blocks in acts
        ]
        capacities = [max(1, len(blocks)) for _, blocks in acts]
        minimum_total = sum(minimums)
        desired = max(minimum_total, desired_scene_count)
        desired = min(sum(capacities), desired)

        allocations = [min(minimum, capacity) for minimum, capacity in zip(minimums, capacities)]
        remaining = desired - sum(allocations)
        if remaining <= 0:
            return allocations

        total_weight = sum(capacities) or 1
        for index, capacity in enumerate(capacities):
            if remaining <= 0:
                break
            available = capacity - allocations[index]
            if available <= 0:
                continue
            additional = round((desired - minimum_total) * capacity / total_weight)
            if additional <= 0:
                continue
            granted = min(available, additional, remaining)
            allocations[index] += granted
            remaining -= granted

        while remaining > 0:
            progressed = False
            for index in sorted(
                range(len(capacities)),
                key=lambda item: capacities[item] - allocations[item],
                reverse=True,
            ):
                if remaining <= 0:
                    break
                if allocations[index] >= capacities[index]:
                    continue
                allocations[index] += 1
                remaining -= 1
                progressed = True
            if not progressed:
                break
        return allocations

    def _chunk_movie_blocks(
        self,
        blocks: list[tuple[int, str]],
        scene_count: int,
    ) -> list[list[tuple[int, str]]]:
        if not blocks:
            return []

        target_scenes = max(1, min(scene_count, len(blocks)))
        base_size = len(blocks) // target_scenes
        extra = len(blocks) % target_scenes

        chunks: list[list[tuple[int, str]]] = []
        cursor = 0
        for index in range(target_scenes):
            chunk_size = base_size + (1 if index < extra else 0)
            next_cursor = cursor + chunk_size
            chunks.append(blocks[cursor:next_cursor])
            cursor = next_cursor
        return [chunk for chunk in chunks if chunk]

    def _classify_heading(self, block: str) -> str | None:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) != 1:
            return None
        line = lines[0]
        cleaned = self._clean_heading(line)
        lowered = cleaned.lower()
        if re.match(r"^#{1,6}\s+", line):
            return cleaned or None
        if re.match(r"^(chapter|act|part|scene)\b", lowered):
            return cleaned
        if cleaned and len(cleaned.split()) <= 6 and cleaned == cleaned.upper():
            return cleaned.title()
        return None

    def _scene_title(self, block: str, scene_index: int) -> str:
        collapsed = block.replace("\n", " ").strip()
        first_sentence = re.split(r"(?<=[.!?])\s+", collapsed, maxsplit=1)[0].strip()
        if not first_sentence:
            return f"Scene {scene_index}"
        title = first_sentence[:72].strip(" .,:;")
        if len(first_sentence) > 72:
            title = title.rstrip() + "..."
        return title or f"Scene {scene_index}"

    def _scene_summary(self, block: str) -> str:
        summary = block.strip().replace("\n", " ")
        if len(summary) <= 220:
            return summary
        clipped = summary[:217].rsplit(" ", 1)[0].strip()
        return f"{clipped}..."

    def _emotional_tags(self, text: str) -> list[str]:
        lowered = text.lower()
        tags = [
            tag
            for tag, keywords in _EMOTIONAL_KEYWORDS.items()
            if any(keyword in lowered for keyword in keywords)
        ]
        return tags[:4]

    def _scene_markers(self, block: str) -> list[str]:
        lowered = block.lower()
        markers: list[str] = []
        if "?" in block:
            markers.append("question")
        if any(word in lowered for word in ("arrive", "arrival", "enter", "return")):
            markers.append("arrival")
        if any(word in lowered for word in ("discover", "find", "realize", "learn")):
            markers.append("discovery")
        if any(word in lowered for word in ("escape", "flee", "run", "leave")):
            markers.append("escape")
        if any(word in lowered for word in ("kiss", "seduce", "desire", "touch")):
            markers.append("seduction")
        return markers[:4]

    def _structural_markers(
        self,
        blocks: list[tuple[int, str]],
        acts: list[Act],
        scenes: list[SceneUnit],
        *,
        target: str,
    ) -> list[str]:
        markers: list[str] = []
        if acts and len(acts) > 1:
            markers.append("multi_act")
        if scenes:
            markers.append("scene_grammar")
        if any(self._classify_heading(block) for _, block in blocks):
            markers.append("headed_source")
        if len(scenes) >= 3:
            markers.append("sequenced_progression")
        if target == TARGET_MOVIE and len(scenes) < len(blocks):
            markers.append("movie_chunked")
        return markers

    def _is_separator_block(self, block: str) -> bool:
        return bool(re.fullmatch(r"[-*_]{3,}", block.strip()))

    def _clean_heading(self, line: str) -> str:
        cleaned = re.sub(r"^#{1,6}\s*", "", line.strip())
        cleaned = cleaned.strip("*_` ")
        return re.sub(r"\s+", " ", cleaned).strip()

    def _source_span(self, chunk: list[tuple[int, str]]) -> str:
        start = chunk[0][0]
        end = chunk[-1][0]
        if start == end:
            return f"block_{start:03d}"
        return f"block_{start:03d}_to_{end:03d}"

    def _merge_unique(self, items: list[str], extras: list[str]) -> list[str]:
        merged = list(items)
        for item in extras:
            if item not in merged:
                merged.append(item)
        return merged


class LlmTranslationLane:
    """Deterministic translation with optional bounded LLM refinement."""

    def __init__(
        self,
        *,
        provider: object | None = None,
        requested: bool = False,
        deterministic_lane: DeterministicTranslationLane | None = None,
    ) -> None:
        self.provider = provider
        self.requested = requested or provider is not None
        self.deterministic_lane = deterministic_lane or DeterministicTranslationLane()
        self.last_status: dict[str, object] = {
            "requested": self.requested,
            "configured": provider is not None,
            "mode": "translation_only",
            "provider": "none",
            "approved": False,
            "degraded": False,
            "used": False,
            "audit": [],
        }

    def run(self, lane_input: TranslationLaneInput) -> SceneGrammar:
        baseline = self.deterministic_lane.run(lane_input)
        if self.provider is None:
            self.last_status = {
                "requested": self.requested,
                "configured": False,
                "mode": "translation_only",
                "provider": "none",
                "approved": False,
                "degraded": False,
                "used": False,
                "audit": [],
            }
            return baseline

        prompt = self._build_prompt(lane_input, baseline)
        context = {
            "title": lane_input.title,
            "raw_text": lane_input.raw_text,
            "baseline": asdict(baseline),
        }
        try:
            proposal = self.provider.propose_scene_grammar(prompt=prompt, context=context)
            proposal_grammar = self._apply_provider_payload(baseline, proposal.payload)
        except Exception as exc:
            self.last_status = {
                "requested": self.requested,
                "configured": True,
                "mode": "translation_fallback",
                "provider": getattr(self.provider, "provider_name", "llm"),
                "approved": False,
                "degraded": True,
                "used": False,
                "audit": [f"Translation provider failed closed: {exc}"],
            }
            return baseline

        issues = self._validate_refinement(baseline, proposal_grammar)
        if issues:
            self.last_status = {
                "requested": self.requested,
                "configured": True,
                "mode": "translation_fallback",
                "provider": proposal.provider,
                "approved": False,
                "degraded": True,
                "used": False,
                "audit": issues,
            }
            return baseline

        self.last_status = {
            "requested": self.requested,
            "configured": True,
            "mode": "translation",
            "provider": proposal.provider,
            "approved": True,
            "degraded": False,
            "used": True,
            "audit": ["LLM translation refinement approved under baseline-shape validation."],
        }
        return proposal_grammar

    def _build_prompt(self, lane_input: TranslationLaneInput, baseline: SceneGrammar) -> str:
        baseline_json = json.dumps(asdict(baseline), indent=2)
        return (
            "Source text:\n"
            f"{lane_input.raw_text}\n\n"
            "Deterministic baseline scene grammar:\n"
            f"{baseline_json}\n\n"
            "Refine only act titles, scene titles, scene summaries, emotional_tags, "
            "and structural_markers. Preserve act ids, scene ids, scene order, and total "
            "scene count exactly. Return only a refinement object containing acts, "
            "emotional_tags, and structural_markers."
        )

    def _apply_provider_payload(self, baseline: SceneGrammar, payload: dict[str, object]) -> SceneGrammar:
        if "total_scenes" in payload and "implemented" in payload:
            return build_contract(payload, SceneGrammar, stage="translation")

        if not isinstance(payload, dict):
            raise ValueError("Translation provider did not return a refinement object.")

        refinement_acts = payload.get("acts")
        if not isinstance(refinement_acts, list):
            raise ValueError("Translation refinement did not include an acts list.")

        if len(refinement_acts) != len(baseline.acts):
            raise ValueError("Translation refinement changed the act count.")

        merged_acts: list[Act] = []
        for base_act, refined_act in zip(baseline.acts, refinement_acts):
            if not isinstance(refined_act, dict):
                raise ValueError("Translation refinement contained a non-object act.")
            if str(refined_act.get("act_id", "")).strip() != base_act.act_id:
                raise ValueError(f"Translation refinement changed act id '{base_act.act_id}'.")

            refined_scenes = refined_act.get("scenes")
            if not isinstance(refined_scenes, list):
                raise ValueError(f"Translation refinement for '{base_act.act_id}' did not include scenes.")
            if len(refined_scenes) != len(base_act.scenes):
                raise ValueError(f"Translation refinement changed scene count inside act '{base_act.act_id}'.")

            merged_scenes: list[SceneUnit] = []
            for base_scene, refined_scene in zip(base_act.scenes, refined_scenes):
                if not isinstance(refined_scene, dict):
                    raise ValueError("Translation refinement contained a non-object scene.")
                if str(refined_scene.get("scene_id", "")).strip() != base_scene.scene_id:
                    raise ValueError(f"Translation refinement changed scene id '{base_scene.scene_id}'.")

                title = str(refined_scene.get("title", "")).strip()
                summary = str(refined_scene.get("summary", "")).strip()
                if not title:
                    raise ValueError(f"Translation refinement returned an empty title for '{base_scene.scene_id}'.")
                if not summary:
                    raise ValueError(f"Translation refinement returned an empty summary for '{base_scene.scene_id}'.")

                emotional_tags = refined_scene.get("emotional_tags", [])
                structural_markers = refined_scene.get("structural_markers", [])
                if not isinstance(emotional_tags, list) or not all(isinstance(tag, str) for tag in emotional_tags):
                    raise ValueError(f"Translation refinement returned invalid emotional_tags for '{base_scene.scene_id}'.")
                if not isinstance(structural_markers, list) or not all(isinstance(tag, str) for tag in structural_markers):
                    raise ValueError(
                        f"Translation refinement returned invalid structural_markers for '{base_scene.scene_id}'."
                    )

                merged_scenes.append(
                    SceneUnit(
                        scene_id=base_scene.scene_id,
                        title=title,
                        summary=summary,
                        source_span=base_scene.source_span,
                        emotional_tags=[str(tag) for tag in emotional_tags],
                        structural_markers=[str(tag) for tag in structural_markers],
                    )
                )

            merged_acts.append(
                Act(
                    act_id=base_act.act_id,
                    title=str(refined_act.get("title", base_act.title)).strip() or base_act.title,
                    scenes=merged_scenes,
                )
            )

        emotional_tags = payload.get("emotional_tags", baseline.emotional_tags)
        structural_markers = payload.get("structural_markers", baseline.structural_markers)
        if not isinstance(emotional_tags, list) or not all(isinstance(tag, str) for tag in emotional_tags):
            raise ValueError("Translation refinement returned invalid top-level emotional_tags.")
        if not isinstance(structural_markers, list) or not all(isinstance(tag, str) for tag in structural_markers):
            raise ValueError("Translation refinement returned invalid top-level structural_markers.")

        return SceneGrammar(
            title=baseline.title,
            acts=merged_acts,
            total_scenes=baseline.total_scenes,
            emotional_tags=[str(tag) for tag in emotional_tags],
            structural_markers=[str(tag) for tag in structural_markers],
            implemented=True,
            valid=baseline.valid,
        )

    def _validate_refinement(self, baseline: SceneGrammar, proposal: SceneGrammar) -> list[str]:
        issues: list[str] = []
        if proposal.total_scenes != baseline.total_scenes:
            issues.append("LLM translation changed the total scene count.")
        if len(proposal.acts) != len(baseline.acts):
            issues.append("LLM translation changed the act count.")
            return issues
        for base_act, proposed_act in zip(baseline.acts, proposal.acts):
            if proposed_act.act_id != base_act.act_id:
                issues.append(f"LLM translation changed act id '{base_act.act_id}'.")
            if len(proposed_act.scenes) != len(base_act.scenes):
                issues.append(f"LLM translation changed scene count inside act '{base_act.act_id}'.")
                continue
            for base_scene, proposed_scene in zip(base_act.scenes, proposed_act.scenes):
                if proposed_scene.scene_id != base_scene.scene_id:
                    issues.append(f"LLM translation changed scene id '{base_scene.scene_id}'.")
                if not proposed_scene.title.strip():
                    issues.append(f"LLM translation returned an empty title for '{base_scene.scene_id}'.")
                if not proposed_scene.summary.strip():
                    issues.append(f"LLM translation returned an empty summary for '{base_scene.scene_id}'.")
        return issues


class TranslationLaneStub:
    """Fail-closed scaffold kept for explicit contract tests."""

    def run(self, lane_input: TranslationLaneInput) -> SceneGrammar:
        return SceneGrammar(
            title=lane_input.title,
            acts=[],
            total_scenes=0,
            emotional_tags=[],
            structural_markers=[],
            implemented=False,
            valid=True,
        )
