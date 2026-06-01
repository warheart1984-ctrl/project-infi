from __future__ import annotations

import base64
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
import re
import shutil
from typing import Any
from urllib import request
from urllib.parse import urlparse

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def _slug(value: str) -> str:
    lowered = str(value or "").strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    return slug or "render"


def _write_binary_asset(reference: str, target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    raw = str(reference or "").strip()
    if not raw:
        raise RenderAdapterExecutionError("Generated asset reference was empty.")

    if raw.startswith("data:"):
        _, encoded = raw.split(",", 1)
        target_path.write_bytes(base64.b64decode(encoded))
        return

    parsed = urlparse(raw)
    if parsed.scheme in {"http", "https"}:
        with request.urlopen(raw, timeout=120.0) as response:
            target_path.write_bytes(response.read())
        return

    source_path = Path(raw)
    if not source_path.exists():
        raise RenderAdapterExecutionError(f"Generated asset reference was not found: {reference}")
    shutil.copyfile(source_path, target_path)


def _provider_configured(adapter: Any) -> bool:
    if adapter is None:
        return False
    config = getattr(adapter, "config", None)
    if config is None:
        return True
    api_key = getattr(config, "api_key", None)
    if api_key is None:
        return True
    return bool(str(api_key or "").strip())


def _extract_single_asset(
    result: dict[str, Any],
    *,
    adapter_name: str,
    action: str,
    key: str,
) -> str:
    if not result.get("ok"):
        message = str(result.get("message", "") or f"{adapter_name.title()} render failed.")
        details = result.get("details", {})
        if isinstance(details, dict):
            exception = str(details.get("exception", "") or "").strip()
            if exception:
                message = f"{message} ({exception})"
        raise RenderAdapterExecutionError(message)

    data = result.get("data", {})
    assets = data.get(key, []) if isinstance(data, dict) else []
    if not isinstance(assets, list) or not assets:
        raise RenderAdapterExecutionError(
            f"{adapter_name.title()} adapter returned no assets for action '{action}'."
        )

    asset = str(assets[0] or "").strip()
    if not asset:
        raise RenderAdapterExecutionError(
            f"{adapter_name.title()} adapter returned an empty asset reference for action '{action}'."
        )
    return asset


@dataclass(slots=True, frozen=True)
class RenderIntent:
    scene_id: str
    shot_id: str
    subject: str
    action: str
    environment: str
    environment_id: str
    intent: str
    visual_intent: str
    framing: str
    camera_motion: str
    pacing: str
    duration_seconds: float
    frame_count: int
    motion_curve: str
    lens_profile: str
    color_profile: str
    grain_profile: str
    seed: int
    style: dict[str, Any]
    style_hash: str
    style_version: str


RenderRequest = RenderIntent


@dataclass(slots=True)
class RenderResult:
    frames: list[str]
    clip_path: str | None
    duration_seconds: float
    metadata: dict[str, Any]


@dataclass(slots=True, frozen=True)
class AdapterCapabilities:
    max_resolution: tuple[int, int]
    supports_motion: bool
    deterministic: bool
    latency_class: str
    requires_api_key: bool


@dataclass(slots=True, frozen=True)
class RuntimeCapabilities:
    gpu_ok: bool
    local_ready: bool
    provider_ready: bool


@dataclass(slots=True, frozen=True)
class PromptBundle:
    still_prompt: str
    motion_prompt: str


class RenderManagerError(RuntimeError):
    pass


class RenderAdapterExecutionError(RenderManagerError):
    pass


def intent_to_prompt(intent: RenderIntent) -> PromptBundle:
    style = dict(intent.style or {})
    subject = str(intent.subject or "central figure").strip()
    action = str(intent.action or intent.intent or "holds frame").strip()
    environment = str(intent.environment or "cinematic environment").strip()
    mood = str(intent.intent or intent.visual_intent or "cinematic").strip()
    visual_intent = str(intent.visual_intent or mood).strip()
    lighting = str(style.get("lighting", mood) or mood).strip()
    composition = str(style.get("composition", "centered_tension") or "centered_tension").strip()
    depth = str(style.get("depth", "layered_midground") or "layered_midground").strip()
    atmosphere = str(style.get("atmosphere", "clean_air") or "clean_air").strip()
    texture = str(style.get("texture", "aged_film") or "aged_film").strip()
    practicals = str(style.get("practicals", "sparse_practicals") or "sparse_practicals").strip()
    blocking = str(style.get("blocking", "single_subject_center") or "single_subject_center").strip()
    contrast = str(style.get("contrast", "soft_crush") or "soft_crush").strip()
    movement_energy = str(style.get("movement_energy", "measured") or "measured").strip()
    frame_signature = str(style.get("frame_signature", "soft_halo") or "soft_halo").strip()
    base = (
        f"{subject} {action} in {environment}, "
        f"{intent.framing} shot, camera motion {intent.camera_motion or 'restrained drift'}, "
        f"mood {mood}, visual intent {visual_intent}, "
        f"lighting {lighting}, composition {composition}, depth {depth}, "
        f"atmosphere {atmosphere}, texture {texture}, practical lighting {practicals}, "
        f"blocking {blocking}, contrast {contrast}, frame signature {frame_signature}, "
        f"{intent.color_profile}, {intent.lens_profile} lens, {intent.grain_profile} film grain, "
        f"environment lock {intent.environment_id}, cinematic, highly detailed, cohesive scene"
    )
    still_prompt = (
        f"{base}, decisive frame, grounded live-action realism, "
        f"scene-specific shot language, no text, no watermark"
    )
    motion_prompt = (
        f"{base}, movement energy {movement_energy}, preserve continuity across motion, "
        f"premium live-action realism"
    )
    return PromptBundle(still_prompt=still_prompt, motion_prompt=motion_prompt)


class BaseRenderAdapter:
    adapter_name = "adapter"
    provider_name = "local"
    capabilities = AdapterCapabilities(
        max_resolution=(640, 360),
        supports_motion=True,
        deterministic=True,
        latency_class="med",
        requires_api_key=False,
    )

    def availability(self) -> tuple[bool, str]:
        return True, ""

    def render(
        self,
        intent: RenderIntent,
        *,
        output_root: Path,
        prompts: PromptBundle,
    ) -> RenderResult:
        raise NotImplementedError


class StoryboardAdapter(BaseRenderAdapter):
    adapter_name = "storyboard"
    provider_name = "local"
    capabilities = AdapterCapabilities(
        max_resolution=(1280, 720),
        supports_motion=True,
        deterministic=True,
        latency_class="low",
        requires_api_key=False,
    )

    def __init__(self, *, resolution: tuple[int, int] = (640, 360), fps: float = 12.0) -> None:
        self.resolution = resolution
        self.fps = fps

    def render(
        self,
        intent: RenderIntent,
        *,
        output_root: Path,
        prompts: PromptBundle,
    ) -> RenderResult:
        shot_slug = _slug(intent.shot_id)
        images_dir = output_root / "images"
        clips_dir = output_root / "clips"
        images_dir.mkdir(parents=True, exist_ok=True)
        clips_dir.mkdir(parents=True, exist_ok=True)
        image_path = images_dir / f"{shot_slug}_storyboard.png"
        clip_path = clips_dir / f"{shot_slug}.mp4"

        width, height = self.resolution
        canvas = Image.new("RGB", (width, height), color=(14, 14, 18))
        draw = ImageDraw.Draw(canvas)
        lines = [
            intent.shot_id,
            intent.subject or "Subject unknown",
            intent.action or intent.intent or "Hold",
            intent.environment or "Environment unknown",
            intent.camera_motion or "Locked frame",
        ]
        y = max(32, height // 8)
        for line in lines:
            draw.text((36, y), line[:110], fill=(236, 236, 240))
            y += 34
        canvas.save(image_path)

        frame_total = max(12, int(intent.frame_count))
        _write_video_from_images([image_path] * frame_total, clip_path, fps=self.fps)
        return RenderResult(
            frames=[str(image_path)],
            clip_path=str(clip_path),
            duration_seconds=float(intent.duration_seconds),
            metadata={
                "adapter": self.adapter_name,
                "provider": self.provider_name,
                "fps": self.fps,
                "frame_count": frame_total,
                "seed_image_path": str(image_path),
            },
        )


class LocalCinematicAdapter(BaseRenderAdapter):
    adapter_name = "local_cinematic"
    provider_name = "local"
    capabilities = AdapterCapabilities(
        max_resolution=(1280, 720),
        supports_motion=True,
        deterministic=True,
        latency_class="med",
        requires_api_key=False,
    )

    def __init__(self, *, resolution: tuple[int, int] = (640, 360), fps: float = 12.0) -> None:
        self.resolution = resolution
        self.fps = fps

    def availability(self) -> tuple[bool, str]:
        try:
            import_module("cv2")
        except ModuleNotFoundError as exc:
            return False, str(exc)
        return True, ""

    def render(
        self,
        intent: RenderIntent,
        *,
        output_root: Path,
        prompts: PromptBundle,
    ) -> RenderResult:
        shot_slug = _slug(intent.shot_id)
        images_dir = output_root / "images"
        clips_dir = output_root / "clips"
        frames_dir = output_root / "frames" / shot_slug
        images_dir.mkdir(parents=True, exist_ok=True)
        clips_dir.mkdir(parents=True, exist_ok=True)
        image_path = images_dir / f"{shot_slug}_seed.png"
        clip_path = clips_dir / f"{shot_slug}.mp4"
        frames_dir.mkdir(parents=True, exist_ok=True)

        base_image = self._generate_base_frame(intent, prompts)
        base_image.save(image_path)

        frame_total = int(intent.frame_count)
        frame_paths: list[Path] = []
        for index in range(frame_total):
            t = 0.0 if frame_total == 1 else index / (frame_total - 1)
            frame = self._apply_motion(base_image, intent, t)
            frame_path = frames_dir / f"frame_{index:03d}.png"
            frame.save(frame_path)
            frame_paths.append(frame_path)

        _write_video_from_images(frame_paths, clip_path, fps=self.fps)
        return RenderResult(
            frames=[str(path) for path in frame_paths],
            clip_path=str(clip_path),
            duration_seconds=float(intent.duration_seconds),
            metadata={
                "adapter": self.adapter_name,
                "provider": self.provider_name,
                "fps": self.fps,
                "frame_count": len(frame_paths),
                "resolution": self.resolution,
                "seed_image_path": str(image_path),
                "prompt_still": prompts.still_prompt,
                "prompt_motion": prompts.motion_prompt,
            },
        )

    def _generate_base_frame(self, intent: RenderIntent, prompts: PromptBundle) -> Image.Image:
        width, height = self.resolution
        rng = np.random.default_rng(intent.seed)
        top, bottom, accent = self._palette(intent)
        flags = self._scene_flags(intent, prompts)
        horizon = self._horizon_line(intent, flags)

        y_gradient = np.linspace(0.0, 1.0, height, dtype=np.float32)[:, None]
        base = np.zeros((height, width, 3), dtype=np.float32)
        top_arr = np.array(top, dtype=np.float32)
        bottom_arr = np.array(bottom, dtype=np.float32)
        accent_arr = np.array(accent, dtype=np.float32)
        base[:] = top_arr * (1.0 - y_gradient[..., None]) + bottom_arr * y_gradient[..., None]
        cloud_noise = self._low_frequency_noise(width, height, rng, scale_divisor=18)
        cloud_arr = np.asarray(cloud_noise, dtype=np.float32) / 255.0
        base *= 0.88 + (cloud_arr[..., None] * 0.18)
        base[:, :, 0] += (cloud_arr - 0.5) * 18.0
        base[:, :, 2] += cloud_arr * 12.0

        if flags["water"] or flags["rain"]:
            reflection_band = np.clip((np.arange(height, dtype=np.float32) - horizon) / max(1.0, height - horizon), 0.0, 1.0)
            base[:, :, 0] += reflection_band[:, None] * accent_arr[0] * 0.06
            base[:, :, 1] += reflection_band[:, None] * accent_arr[1] * 0.04
            base[:, :, 2] += reflection_band[:, None] * accent_arr[2] * 0.08

        image = Image.fromarray(np.clip(base, 0, 255).astype("uint8"), mode="RGB").convert("RGBA")
        geometry_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        practical_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        atmosphere_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))

        focal_x, focal_y = self._focal_point(intent)
        geometry_draw = ImageDraw.Draw(geometry_layer)
        practical_draw = ImageDraw.Draw(practical_layer)
        atmosphere_draw = ImageDraw.Draw(atmosphere_layer)

        self._draw_horizon_glow(
            practical_draw,
            width=width,
            height=height,
            horizon=horizon,
            focal_x=focal_x,
            focal_y=focal_y,
            accent=accent,
        )
        if flags["urban"] or flags["interior"]:
            self._draw_urban_mass(geometry_draw, rng, width=width, height=height, horizon=horizon, accent=accent)
        else:
            self._draw_landscape_mass(geometry_draw, rng, width=width, height=height, horizon=horizon, accent=accent)
        self._draw_practical_lights(
            practical_draw,
            rng,
            width=width,
            height=height,
            horizon=horizon,
            accent=accent,
            reflective=flags["water"] or flags["rain"],
            dense=flags["urban"] or flags["interior"],
        )
        self._draw_atmosphere(
            atmosphere_draw,
            rng,
            width=width,
            height=height,
            horizon=horizon,
            accent=accent,
            flags=flags,
        )
        rim_layer, subject_layer = self._build_subject_layers(
            intent,
            rng,
            width=width,
            height=height,
            focal_x=focal_x,
            focal_y=focal_y,
            accent=accent,
        )

        image = Image.alpha_composite(image, geometry_layer.filter(ImageFilter.GaussianBlur(radius=max(2, width // 220))))
        image = Image.alpha_composite(image, practical_layer.filter(ImageFilter.GaussianBlur(radius=max(8, width // 42))))
        image = Image.alpha_composite(image, atmosphere_layer.filter(ImageFilter.GaussianBlur(radius=max(3, width // 320))))
        image = Image.alpha_composite(image, rim_layer.filter(ImageFilter.GaussianBlur(radius=max(8, width // 120))))
        image = Image.alpha_composite(image, subject_layer)

        rgb = self._apply_color_grade(image.convert("RGB"), intent, accent, flags)
        rgb *= self._vignette(width, height)[..., None]
        rgb += rng.normal(0.0, self._grain_strength(intent.grain_profile), size=rgb.shape)
        rgb = np.clip(rgb, 0, 255).astype("uint8")
        return Image.fromarray(rgb, mode="RGB")

    def _apply_motion(self, base_image: Image.Image, intent: RenderIntent, progress: float) -> Image.Image:
        width, height = self.resolution
        focal_x, focal_y = self._focal_point(intent)
        x_direction, y_direction, zoom_start, zoom_end = self._motion_profile(intent.camera_motion)
        curved = self._curve(progress, intent.motion_curve)
        zoom = zoom_start + ((zoom_end - zoom_start) * curved)
        jitter_x, jitter_y = self._gate_weave(intent, progress, width=width, height=height)

        crop_width = max(width // 2, int(width / zoom))
        crop_height = max(height // 2, int(height / zoom))
        margin_x = max(0, width - crop_width)
        margin_y = max(0, height - crop_height)

        anchor_x = focal_x / max(1, width)
        anchor_y = focal_y / max(1, height)
        pan_x = anchor_x + (x_direction * 0.12 * (curved - 0.5))
        pan_y = anchor_y + (y_direction * 0.08 * (curved - 0.5))
        left = int(max(0, min(margin_x, (margin_x * pan_x) + jitter_x)))
        top = int(max(0, min(margin_y, (margin_y * pan_y) + jitter_y)))

        frame = base_image.crop((left, top, left + crop_width, top + crop_height)).resize(
            self.resolution,
            Image.Resampling.LANCZOS,
        )
        rng = np.random.default_rng(intent.seed + int(progress * 10_000))
        frame_arr = np.asarray(frame, dtype=np.float32)
        exposure = 1.0 + (np.sin((progress * np.pi * 2.0) + (intent.seed % 17)) * 0.018)
        frame_arr *= exposure
        frame_arr += rng.normal(0.0, self._grain_strength(intent.grain_profile) * 0.55, size=frame_arr.shape)
        frame_arr = np.clip(frame_arr, 0, 255).astype("uint8")
        return Image.fromarray(frame_arr, mode="RGB")

    def _palette(self, intent: RenderIntent) -> tuple[tuple[int, int, int], ...]:
        profile = str(intent.color_profile or "").strip().lower()
        corpus = " ".join(
            [
                str(intent.environment or ""),
                str(intent.intent or ""),
                str(intent.visual_intent or ""),
                str(intent.action or ""),
            ]
        ).lower()
        seed_rng = np.random.default_rng(intent.seed + 97)
        palette_map = {
            "cold_blue_amber": ((12, 28, 52), (28, 52, 90), (224, 154, 64)),
            "sodium_teal_noir": ((10, 22, 34), (20, 46, 60), (236, 145, 58)),
            "ember_crimson_smoke": ((26, 18, 22), (66, 24, 34), (236, 92, 50)),
            "moon_silver_blue": ((20, 26, 40), (46, 66, 98), (214, 226, 236)),
            "verdigris_gold_decay": ((16, 30, 26), (38, 74, 54), (198, 164, 84)),
            "bone_charcoal_amber": ((24, 22, 18), (62, 54, 42), (216, 170, 96)),
        }
        if profile in palette_map:
            top, bottom, accent = (np.array(values, dtype=np.float32) for values in palette_map[profile])
            if any(token in corpus for token in ("blood", "fire", "ritual", "sunset", "burn")) and profile == "cold_blue_amber":
                accent = np.array((232, 96, 54), dtype=np.float32)
                bottom = np.array((46, 34, 66), dtype=np.float32)
            elif any(token in corpus for token in ("forest", "moss", "verdant", "garden")) and profile == "cold_blue_amber":
                accent = np.array((126, 188, 106), dtype=np.float32)
                top = np.array((10, 24, 34), dtype=np.float32)
            top += seed_rng.integers(-5, 6, size=3)
            bottom += seed_rng.integers(-7, 8, size=3)
            accent += seed_rng.integers(-10, 11, size=3)
            return tuple(tuple(int(np.clip(value, 0, 255)) for value in palette) for palette in (top, bottom, accent))
        return (
            tuple(int(value) for value in seed_rng.integers(12, 64, size=3)),
            tuple(int(value) for value in seed_rng.integers(48, 128, size=3)),
            tuple(int(value) for value in seed_rng.integers(140, 228, size=3)),
        )

    def _focal_point(self, intent: RenderIntent) -> tuple[int, int]:
        width, height = self.resolution
        framing = str(intent.framing or "").strip().lower()
        composition = self._style_value(intent, "composition", "")
        if "close" in framing:
            x = width * 0.52
            y = height * 0.42
        elif "wide" in framing:
            x = width * 0.50
            y = height * 0.54
        else:
            x = width * 0.50
            y = height * 0.48
        if "left" in composition:
            x = width * 0.38
        elif "right" in composition:
            x = width * 0.62
        elif "center" in composition:
            x = width * 0.50
        if "negative_space" in composition:
            y = min(height * 0.58, y + (height * 0.04))
        return int(x), int(y)

    def _motion_profile(self, camera_motion: str) -> tuple[float, float, float, float]:
        move = str(camera_motion or "").strip().lower()
        x_direction = -1.0 if "left" in move else 1.0 if "right" in move else 0.0
        y_direction = -1.0 if "up" in move else 1.0 if "down" in move else 0.0
        if any(token in move for token in ("pull back", "zoom out", "dolly out")):
            return x_direction, y_direction, 1.08, 1.0
        if any(token in move for token in ("push", "zoom in", "dolly in")):
            return x_direction, y_direction, 1.0, 1.12
        if "pan" in move or "drift" in move:
            return x_direction or 1.0, y_direction, 1.0, 1.06
        return x_direction, y_direction, 1.0, 1.04

    def _curve(self, progress: float, motion_curve: str) -> float:
        normalized = str(motion_curve or "").strip().lower()
        if normalized == "ease_in":
            return progress * progress
        if normalized == "ease_out":
            return 1.0 - ((1.0 - progress) * (1.0 - progress))
        if normalized == "ease_in_out":
            return (1.0 - np.cos(np.pi * progress)) / 2.0
        return progress

    def _grain_strength(self, grain_profile: str) -> float:
        normalized = str(grain_profile or "").strip().lower()
        if normalized == "heavy":
            return 10.0
        if normalized == "clean":
            return 2.5
        return 5.0

    def _vignette(self, width: int, height: int) -> np.ndarray:
        yy, xx = np.mgrid[0:height, 0:width]
        norm_x = (xx - (width / 2)) / max(1.0, width / 2)
        norm_y = (yy - (height / 2)) / max(1.0, height / 2)
        radius = np.sqrt((norm_x * norm_x) + (norm_y * norm_y))
        vignette = 1.0 - np.clip(radius, 0.0, 1.2) * 0.42
        return np.clip(vignette, 0.55, 1.0).astype(np.float32)

    def _scene_flags(self, intent: RenderIntent, prompts: PromptBundle) -> dict[str, bool]:
        style = dict(intent.style or {})
        corpus = " ".join(
            [
                str(intent.environment or ""),
                str(intent.subject or ""),
                str(intent.action or ""),
                str(intent.intent or ""),
                str(intent.visual_intent or ""),
                str(prompts.still_prompt or ""),
                str(style.get("atmosphere", "") or ""),
                str(style.get("practicals", "") or ""),
                str(style.get("texture", "") or ""),
            ]
        ).lower()
        return {
            "urban": any(token in corpus for token in ("city", "street", "neon", "tower", "archive", "observatory", "station", "hall")),
            "interior": any(token in corpus for token in ("interior", "room", "hall", "archive", "corridor", "chamber", "cathedral")),
            "water": any(token in corpus for token in ("water", "ocean", "river", "lake", "shore", "flood", "rain-soaked")),
            "rain": any(token in corpus for token in ("rain", "storm", "wet", "drizzle", "downpour")),
            "fog": any(token in corpus for token in ("fog", "mist", "smoke", "haze", "dream")),
        }

    def _horizon_line(self, intent: RenderIntent, flags: dict[str, bool]) -> int:
        width, height = self.resolution
        framing = str(intent.framing or "").strip().lower()
        if flags["interior"]:
            ratio = 0.58
        elif "wide" in framing:
            ratio = 0.64
        elif "close" in framing:
            ratio = 0.54
        else:
            ratio = 0.60
        if flags["water"]:
            ratio = min(0.68, ratio + 0.04)
        return int(max(height * 0.34, min(height * 0.78, height * ratio)))

    def _low_frequency_noise(
        self,
        width: int,
        height: int,
        rng: np.random.Generator,
        *,
        scale_divisor: int,
    ) -> Image.Image:
        small_width = max(18, width // scale_divisor)
        small_height = max(18, height // scale_divisor)
        noise = rng.integers(0, 255, size=(small_height, small_width), dtype=np.uint8)
        return Image.fromarray(noise, mode="L").resize((width, height), Image.Resampling.BICUBIC)

    def _draw_horizon_glow(
        self,
        draw: ImageDraw.ImageDraw,
        *,
        width: int,
        height: int,
        horizon: int,
        focal_x: int,
        focal_y: int,
        accent: tuple[int, int, int],
    ) -> None:
        bloom_radius = int(min(width, height) * 0.36)
        draw.ellipse(
            (
                focal_x - bloom_radius,
                focal_y - bloom_radius,
                focal_x + bloom_radius,
                focal_y + bloom_radius,
            ),
            fill=(accent[0], accent[1], accent[2], 74),
        )
        draw.rectangle(
            (0, horizon - max(14, height // 18), width, horizon + max(18, height // 10)),
            fill=(accent[0], accent[1], accent[2], 18),
        )

    def _draw_urban_mass(
        self,
        draw: ImageDraw.ImageDraw,
        rng: np.random.Generator,
        *,
        width: int,
        height: int,
        horizon: int,
        accent: tuple[int, int, int],
    ) -> None:
        depth_specs = (
            (0.16, (24, 28, 40, 132), 10),
            (0.10, (18, 20, 30, 168), 8),
            (0.05, (12, 14, 20, 216), 6),
        )
        for depth_offset, color, count in depth_specs:
            x = -width * 0.08
            baseline = horizon + int(height * depth_offset)
            while x < width + (width * 0.08):
                building_width = int(rng.integers(max(28, width // count), max(54, width // max(2, count - 2))))
                building_height = int(rng.integers(max(60, height // 4), max(100, int(height * 0.62))))
                left = int(x)
                right = left + building_width
                top = baseline - building_height
                draw.rounded_rectangle((left, top, right, baseline), radius=max(4, building_width // 12), fill=color)
                roof_height = int(rng.integers(8, max(12, building_width // 5)))
                draw.polygon(
                    [(left, top), (left + building_width // 2, top - roof_height), (right, top)],
                    fill=(color[0], color[1], color[2], min(255, color[3] + 12)),
                )
                if color[3] >= 160:
                    window_cols = max(2, building_width // 22)
                    window_rows = max(2, building_height // 28)
                    for col in range(window_cols):
                        for row in range(window_rows):
                            if rng.random() < 0.38:
                                continue
                            wx = left + 6 + (col * max(10, building_width // max(1, window_cols)))
                            wy = top + 8 + (row * max(12, building_height // max(1, window_rows)))
                            draw.rounded_rectangle(
                                (wx, wy, wx + 4, wy + 7),
                                radius=1,
                                fill=(accent[0], accent[1], accent[2], int(rng.integers(46, 112))),
                            )
                x += int(building_width * rng.uniform(0.68, 0.96))

    def _draw_landscape_mass(
        self,
        draw: ImageDraw.ImageDraw,
        rng: np.random.Generator,
        *,
        width: int,
        height: int,
        horizon: int,
        accent: tuple[int, int, int],
    ) -> None:
        depth_specs = (
            (0.18, (18, 24, 34, 120)),
            (0.10, (14, 18, 24, 164)),
            (0.02, (10, 12, 18, 214)),
        )
        for depth_offset, color in depth_specs:
            ridge_base = horizon + int(height * depth_offset)
            points: list[tuple[int, int]] = [(0, height)]
            points.append((0, ridge_base + int(rng.integers(-18, 18))))
            segment_count = 7
            for segment in range(1, segment_count):
                x = int(segment * width / (segment_count - 1))
                y = ridge_base + int(rng.integers(-height // 10, height // 12))
                points.append((x, y))
            points.append((width, height))
            draw.polygon(points, fill=color)
            for x, y in points[1:-1]:
                if rng.random() < 0.4:
                    continue
                crown = int(rng.integers(10, max(14, width // 48)))
                draw.ellipse(
                    (x - crown, y - crown, x + crown, y + crown),
                    fill=(accent[0] // 2, accent[1] // 2, accent[2] // 2, 42),
                )

    def _draw_practical_lights(
        self,
        draw: ImageDraw.ImageDraw,
        rng: np.random.Generator,
        *,
        width: int,
        height: int,
        horizon: int,
        accent: tuple[int, int, int],
        reflective: bool,
        dense: bool,
    ) -> None:
        light_count = 14 if dense else 8
        for _ in range(light_count):
            x = int(rng.integers(width // 12, width - (width // 12)))
            y = int(rng.integers(max(horizon - height // 8, height // 4), horizon + height // 8))
            radius = int(rng.integers(max(8, width // 96), max(14, width // 36)))
            alpha = int(rng.integers(38, 96))
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(accent[0], accent[1], accent[2], alpha))
            if reflective:
                reflection_length = int(radius * rng.uniform(2.2, 4.0))
                draw.rounded_rectangle(
                    (x - max(2, radius // 5), y, x + max(2, radius // 5), y + reflection_length),
                    radius=max(1, radius // 6),
                    fill=(accent[0], accent[1], accent[2], max(16, alpha // 3)),
                )

    def _draw_atmosphere(
        self,
        draw: ImageDraw.ImageDraw,
        rng: np.random.Generator,
        *,
        width: int,
        height: int,
        horizon: int,
        accent: tuple[int, int, int],
        flags: dict[str, bool],
    ) -> None:
        if flags["rain"]:
            streaks = max(120, width // 4)
            for _ in range(streaks):
                start_x = int(rng.integers(-width // 12, width))
                start_y = int(rng.integers(0, height))
                length = int(rng.integers(max(8, height // 28), max(16, height // 16)))
                draw.line(
                    (start_x, start_y, start_x + int(length * 0.45), start_y + length),
                    fill=(220, 228, 255, int(rng.integers(18, 48))),
                    width=max(1, width // 640),
                )
        else:
            particles = 26 if flags["fog"] else 16
            for _ in range(particles):
                radius = int(rng.integers(max(10, width // 100), max(24, width // 40)))
                x = int(rng.integers(-radius, width))
                y = int(rng.integers(max(0, horizon - height // 6), height))
                fill = (accent[0], accent[1], accent[2], int(rng.integers(8, 28)))
                draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill)
        if flags["fog"]:
            fog_bands = 4
            for index in range(fog_bands):
                band_top = horizon - (height // 14) + (index * max(14, height // 18))
                band_bottom = band_top + max(18, height // 12)
                draw.rectangle(
                    (0, band_top, width, band_bottom),
                    fill=(210, 214, 226, 12 + (index * 4)),
                )

    def _build_subject_layers(
        self,
        intent: RenderIntent,
        rng: np.random.Generator,
        *,
        width: int,
        height: int,
        focal_x: int,
        focal_y: int,
        accent: tuple[int, int, int],
    ) -> tuple[Image.Image, Image.Image]:
        framing = str(intent.framing or "").strip().lower()
        if "wide" in framing:
            subject_width = int(width * 0.14)
            subject_height = int(height * 0.38)
        elif "close" in framing:
            subject_width = int(width * 0.26)
            subject_height = int(height * 0.62)
        else:
            subject_width = int(width * 0.20)
            subject_height = int(height * 0.50)

        composition = self._style_value(intent, "composition", "")
        if "left" in composition:
            anchor_x = width * 0.38
        elif "right" in composition:
            anchor_x = width * 0.62
        else:
            anchor_x = focal_x
        center_x = int(max(subject_width, min(width - subject_width, anchor_x + rng.integers(-width // 42, width // 42))))
        base_y = int(max(subject_height, min(height - 20, focal_y + (subject_height * 0.55))))
        torso_top = base_y - subject_height
        head_radius = max(14, subject_width // 5)

        subject_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        rim_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        subject_draw = ImageDraw.Draw(subject_layer)
        rim_draw = ImageDraw.Draw(rim_layer)

        silhouette_color = (14, 16, 20, 224)
        rim_color = (accent[0], accent[1], accent[2], 118)
        shoulder_width = int(subject_width * 0.90)
        waist_width = int(subject_width * 0.52)

        body_points = [
            (center_x - shoulder_width // 2, torso_top + subject_height // 4),
            (center_x + shoulder_width // 2, torso_top + subject_height // 4),
            (center_x + waist_width // 2, base_y),
            (center_x - waist_width // 2, base_y),
        ]
        head_box = (
            center_x - head_radius,
            torso_top,
            center_x + head_radius,
            torso_top + (head_radius * 2),
        )

        for draw_target, color, x_offset in ((rim_draw, rim_color, 8), (subject_draw, silhouette_color, 0)):
            shifted_points = [(x + x_offset, y) for x, y in body_points]
            shifted_head = (head_box[0] + x_offset, head_box[1], head_box[2] + x_offset, head_box[3])
            draw_target.polygon(shifted_points, fill=color)
            draw_target.ellipse(shifted_head, fill=color)
            draw_target.rounded_rectangle(
                (
                    center_x - max(4, subject_width // 7) + x_offset,
                    torso_top + subject_height // 3,
                    center_x + max(4, subject_width // 7) + x_offset,
                    base_y,
                ),
                radius=max(4, subject_width // 14),
                fill=color,
            )
        return rim_layer, subject_layer

    def _apply_color_grade(
        self,
        image: Image.Image,
        intent: RenderIntent,
        accent: tuple[int, int, int],
        flags: dict[str, bool],
    ) -> np.ndarray:
        width, height = image.size
        base_arr = np.asarray(image, dtype=np.float32)
        blurred = np.asarray(image.filter(ImageFilter.GaussianBlur(radius=max(8, width // 84))), dtype=np.float32)

        luma = base_arr.mean(axis=2)
        highlight_mask = np.clip((luma - 154.0) / 92.0, 0.0, 1.0)
        accent_arr = np.array(accent, dtype=np.float32)
        base_arr += (blurred * highlight_mask[..., None] * 0.08)
        base_arr += accent_arr * highlight_mask[..., None] * 0.05

        contrast_profile = self._style_value(intent, "contrast", "soft_crush")
        if contrast_profile == "hard_crush":
            contrast = 1.14
        elif contrast_profile == "soft_bloom":
            contrast = 1.01
            base_arr += blurred * 0.05
        else:
            contrast = 1.08 if flags["urban"] else 1.04
        base_arr = ((base_arr - 127.5) * contrast) + 127.5
        base_arr[:, :, 2] *= 1.04
        base_arr[:, :, 0] *= 0.98 if flags["rain"] else 1.01
        return np.clip(base_arr, 0, 255)

    def _gate_weave(
        self,
        intent: RenderIntent,
        progress: float,
        *,
        width: int,
        height: int,
    ) -> tuple[float, float]:
        x = np.sin((progress * np.pi * 3.2) + (intent.seed % 13)) * (width * 0.0032)
        y = np.cos((progress * np.pi * 2.4) + (intent.seed % 7)) * (height * 0.0028)
        return float(x), float(y)

    def _style_value(self, intent: RenderIntent, key: str, default: str) -> str:
        value = dict(intent.style or {}).get(key, default)
        return str(value or default).strip()


class ProviderAdapter(BaseRenderAdapter):
    capabilities = AdapterCapabilities(
        max_resolution=(1280, 720),
        supports_motion=True,
        deterministic=False,
        latency_class="high",
        requires_api_key=True,
    )

    def __init__(
        self,
        *,
        image_adapter: Any,
        video_adapter: Any,
        resolution: tuple[int, int] = (1280, 720),
    ) -> None:
        self.image_adapter = image_adapter
        self.video_adapter = video_adapter
        self.resolution = resolution
        provider_name = str(
            getattr(image_adapter, "provider_name", "")
            or getattr(getattr(image_adapter, "config", None), "provider", "")
            or "provider"
        ).strip().lower()
        self.provider_name = provider_name or "provider"
        self.adapter_name = self.provider_name

    def availability(self) -> tuple[bool, str]:
        if self.image_adapter is None or self.video_adapter is None:
            return False, "provider image/video adapters are not attached"
        if not _provider_configured(self.image_adapter) or not _provider_configured(self.video_adapter):
            return False, "provider adapters are present but not configured with credentials"
        return True, ""

    def render(
        self,
        intent: RenderIntent,
        *,
        output_root: Path,
        prompts: PromptBundle,
    ) -> RenderResult:
        shot_slug = _slug(intent.shot_id)
        images_dir = output_root / "images"
        clips_dir = output_root / "clips"
        images_dir.mkdir(parents=True, exist_ok=True)
        clips_dir.mkdir(parents=True, exist_ok=True)
        image_path = images_dir / f"{shot_slug}_seed.png"
        clip_path = clips_dir / f"{shot_slug}.mp4"

        image_result = self.image_adapter.execute(
            "generate",
            {
                "prompt": prompts.still_prompt,
                "response_format": "b64_json",
                "aspect_ratio": "16:9",
                "n": 1,
                "seed": intent.seed,
            },
        )
        image_reference = _extract_single_asset(
            image_result,
            adapter_name="image",
            action="generate",
            key="images",
        )
        _write_binary_asset(image_reference, image_path)

        video_result = self.video_adapter.execute(
            "generate",
            {
                "prompt": prompts.motion_prompt,
                "image": str(image_path),
                "duration": max(1, int(round(intent.duration_seconds))),
                "aspect_ratio": "16:9",
                "resolution": f"{self.resolution[1]}p",
                "seed": intent.seed,
            },
        )
        video_reference = _extract_single_asset(
            video_result,
            adapter_name="video",
            action="generate",
            key="videos",
        )
        _write_binary_asset(video_reference, clip_path)

        return RenderResult(
            frames=[str(image_path)],
            clip_path=str(clip_path),
            duration_seconds=float(intent.duration_seconds),
            metadata={
                "adapter": self.adapter_name,
                "provider": self.provider_name,
                "seed_image_path": str(image_path),
                "image_meta": image_result.get("meta", {}),
                "video_meta": video_result.get("meta", {}),
                "prompt_still": prompts.still_prompt,
                "prompt_motion": prompts.motion_prompt,
            },
        )


class RenderManager:
    def __init__(
        self,
        *,
        mode: str = "auto",
        local_adapter: BaseRenderAdapter | None = None,
        provider_adapter: BaseRenderAdapter | None = None,
        storyboard_adapter: BaseRenderAdapter | None = None,
        runtime_capabilities: RuntimeCapabilities | None = None,
    ) -> None:
        self.mode = self._normalize_mode(mode)
        self.local_adapter = local_adapter or LocalCinematicAdapter()
        self.provider_adapter = provider_adapter
        self.storyboard_adapter = storyboard_adapter or StoryboardAdapter()
        self._runtime_capabilities_override = runtime_capabilities

    def render_intents(
        self,
        intents: list[RenderIntent],
        *,
        output_root: str | Path,
        mode: str | None = None,
    ) -> dict[str, RenderResult]:
        output_dir = Path(output_root)
        output_dir.mkdir(parents=True, exist_ok=True)
        requested_mode = self._normalize_mode(mode or self.mode)
        runtime_caps = self._runtime_capabilities()

        results: dict[str, RenderResult] = {}
        for intent in intents:
            prompts = intent_to_prompt(intent)
            results[intent.shot_id] = self._render_single(
                intent,
                prompts=prompts,
                output_root=output_dir,
                mode=requested_mode,
                runtime_caps=runtime_caps,
            )
        return results

    def select(self, intent: RenderIntent, mode: str, caps: RuntimeCapabilities) -> BaseRenderAdapter:
        normalized = self._normalize_mode(mode)
        if normalized == "debug":
            return self.storyboard_adapter
        if normalized == "local":
            return self.local_adapter
        if normalized == "external":
            return self.provider_adapter or self.storyboard_adapter
        if normalized == "auto":
            if caps.gpu_ok and caps.local_ready:
                return self.local_adapter
            if caps.provider_ready and self.provider_adapter is not None:
                return self.provider_adapter
            if caps.local_ready:
                return self.local_adapter
            return self.storyboard_adapter
        return self.storyboard_adapter

    def _render_single(
        self,
        intent: RenderIntent,
        *,
        prompts: PromptBundle,
        output_root: Path,
        mode: str,
        runtime_caps: RuntimeCapabilities,
    ) -> RenderResult:
        primary = self.select(intent, mode, runtime_caps)
        chain = self._fallback_chain(mode, primary, runtime_caps)
        attempts: list[dict[str, Any]] = []
        last_error: Exception | None = None

        for adapter in chain:
            if adapter is None:
                continue
            available, reason = adapter.availability()
            if not available:
                attempts.append(
                    {
                        "adapter": adapter.adapter_name,
                        "provider": adapter.provider_name,
                        "status": "skipped",
                        "reason": reason,
                    }
                )
                continue

            try:
                result = adapter.render(intent, output_root=output_root, prompts=prompts)
                self._validate_result(intent, result)
                metadata = dict(result.metadata)
                metadata.update(
                    {
                        "adapter": adapter.adapter_name,
                        "provider": adapter.provider_name,
                        "seed": intent.seed,
                        "style_hash": intent.style_hash,
                        "attempts": attempts
                        + [
                            {
                                "adapter": adapter.adapter_name,
                                "provider": adapter.provider_name,
                                "status": "used",
                            }
                        ],
                    }
                )
                result.metadata = metadata
                return result
            except Exception as exc:  # noqa: BLE001 - deterministic fallback boundary
                last_error = exc
                attempts.append(
                    {
                        "adapter": adapter.adapter_name,
                        "provider": adapter.provider_name,
                        "status": "failed",
                        "error": str(exc),
                    }
                )

        raise RenderManagerError(
            f"All render adapters failed for shot '{intent.shot_id}'."
            + (f" Last error: {last_error}" if last_error is not None else "")
        )

    def _runtime_capabilities(self) -> RuntimeCapabilities:
        if self._runtime_capabilities_override is not None:
            return self._runtime_capabilities_override
        local_available, _ = self.local_adapter.availability()
        provider_available = False
        if self.provider_adapter is not None:
            provider_available, _ = self.provider_adapter.availability()
        return RuntimeCapabilities(
            gpu_ok=False,
            local_ready=local_available,
            provider_ready=provider_available,
        )

    def _fallback_chain(
        self,
        mode: str,
        primary: BaseRenderAdapter,
        caps: RuntimeCapabilities,
    ) -> list[BaseRenderAdapter | None]:
        normalized = self._normalize_mode(mode)
        if normalized == "debug":
            return [self.storyboard_adapter]
        if normalized == "local":
            return [self.local_adapter, self.storyboard_adapter]
        if normalized == "external":
            return [self.provider_adapter, self.local_adapter, self.storyboard_adapter]
        if normalized == "auto":
            ordered = [primary]
            if primary is not self.local_adapter and caps.local_ready:
                ordered.append(self.local_adapter)
            if (
                primary is not self.provider_adapter
                and self.provider_adapter is not None
                and caps.provider_ready
            ):
                ordered.append(self.provider_adapter)
            if primary is not self.storyboard_adapter:
                ordered.append(self.storyboard_adapter)
            return ordered
        return [primary, self.storyboard_adapter]

    def _validate_result(self, intent: RenderIntent, result: RenderResult) -> None:
        if not isinstance(result.frames, list) or not result.frames:
            raise RenderManagerError(f"Render result returned no frames for {intent.shot_id}.")
        if result.clip_path is None:
            raise RenderManagerError(f"Render result returned no clip for {intent.shot_id}.")
        clip_path = Path(result.clip_path)
        if not clip_path.exists() or clip_path.stat().st_size <= 0:
            raise RenderManagerError(f"Render clip was not created for {intent.shot_id}.")
        if abs(float(result.duration_seconds) - float(intent.duration_seconds)) > 0.51:
            raise RenderManagerError(f"Render duration drifted for {intent.shot_id}.")

        frame_numbers: list[int] = []
        for frame in result.frames:
            frame_path = Path(frame)
            if not frame_path.exists():
                raise RenderManagerError(f"Render frame missing for {intent.shot_id}: {frame}")
            match = re.search(r"_(\d{3})$", frame_path.stem)
            if match:
                frame_numbers.append(int(match.group(1)))

        if frame_numbers:
            expected = list(range(len(frame_numbers)))
            if frame_numbers != expected:
                raise RenderManagerError(f"Render frames were not contiguous for {intent.shot_id}.")
        if len(result.frames) not in {1, int(intent.frame_count)}:
            raise RenderManagerError(f"Render frame count mismatch for {intent.shot_id}.")

    def _normalize_mode(self, mode: str | None) -> str:
        normalized = str(mode or "auto").strip().lower().replace("-", "_")
        if normalized in {"", "auto"}:
            return "auto"
        if normalized in {"debug", "storyboard"}:
            return "debug"
        if normalized in {"local", "cinematic", "local_cinematic"}:
            return "local"
        if normalized in {"external", "provider"}:
            return "external"
        return normalized


def _write_video_from_images(frame_paths: list[Path], clip_path: Path, *, fps: float) -> None:
    if not frame_paths:
        raise RenderAdapterExecutionError("No frames were provided for video assembly.")

    try:
        cv2 = import_module("cv2")
    except ModuleNotFoundError as exc:
        raise RenderAdapterExecutionError(
            "Video assembly requires opencv-python-headless."
        ) from exc

    first_frame = Image.open(frame_paths[0]).convert("RGB")
    width, height = first_frame.size
    writer = cv2.VideoWriter(
        str(clip_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        float(fps),
        (width, height),
    )
    if not writer.isOpened():
        raise RenderAdapterExecutionError(f"Could not open video writer for {clip_path}.")

    try:
        for frame_path in frame_paths:
            frame = Image.open(frame_path).convert("RGB")
            frame_array = np.asarray(frame, dtype=np.uint8)
            writer.write(cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR))
    finally:
        writer.release()

    if not clip_path.exists() or clip_path.stat().st_size <= 0:
        raise RenderAdapterExecutionError(f"Rendered clip was not written: {clip_path}")


__all__ = [
    "AdapterCapabilities",
    "BaseRenderAdapter",
    "LocalCinematicAdapter",
    "PromptBundle",
    "ProviderAdapter",
    "RenderIntent",
    "RenderManager",
    "RenderManagerError",
    "RenderRequest",
    "RenderResult",
    "RuntimeCapabilities",
    "StoryboardAdapter",
    "intent_to_prompt",
]
