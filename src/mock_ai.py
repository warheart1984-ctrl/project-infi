"""Lightweight mock AI services for local development."""


class MockMultiModalAI:
    """Cheap local fallback that mimics the model API."""

    def __init__(self):
        self.device = "mock"
        self.text_model = None
        self.text_tokenizer = None
        self.last_generation_metadata = {}

    def generate_text(self, prompt, max_length=512, temperature=0.7):
        snippet = prompt.strip().replace("\n", " ")[:140]
        self.last_generation_metadata = {
            "stop_reason": "mock_complete",
            "finish_reason": "stop",
            "input_tokens": 0,
            "output_tokens": max(1, len(snippet) // 4),
            "output_token_budget": int(max_length or 0),
        }
        return (
            "Mock response from AAIS local mode.\n\n"
            f"Prompt: {snippet}\n"
            f"Temperature: {temperature}\n"
            f"Max length: {max_length}\n\n"
            "Switch AAIS_MODEL_MODE=real after installing the full model stack."
        )

    def generate_chat(
        self,
        messages,
        max_length=512,
        temperature=0.7,
        response_mode=None,
        routing_profile=None,
    ):
        del response_mode, routing_profile
        latest_user = next(
            (
                message.get("content", "")
                for message in reversed(messages or [])
                if message.get("role") == "user"
            ),
            "",
        )
        system_hints = [
            message.get("content", "")
            for message in messages or []
            if message.get("role") == "system"
        ]
        planning_pass = any("Jarvis planning notes for this turn" in hint for hint in system_hints)

        if planning_pass:
            self.last_generation_metadata = {
                "stop_reason": "mock_complete",
                "finish_reason": "stop",
                "input_tokens": 0,
                "output_tokens": 24,
                "output_token_budget": int(max_length or 0),
            }
            return (
                f"Focus: answer {latest_user[:72]}.\n"
                "Evidence: use any attached workspace or research context.\n"
                "Answer Shape: keep the next answer practical and grounded."
            )

        return self.generate_text(latest_user or "Jarvis mock chat", max_length, temperature)

    def analyze_image(self, image):
        width, height = image.size
        return {
            "description": (
                "Mock image analysis from local mode. "
                f"The uploaded image is {width}x{height}px."
            ),
            "image_features_shape": [1, 512],
        }

    def generate_image(self, prompt, num_inference_steps=50):
        from PIL import Image, ImageDraw

        width, height = 1024, 768
        image = Image.new("RGB", (width, height), "#101826")
        draw = ImageDraw.Draw(image)

        for row in range(height):
            mix = row / max(height - 1, 1)
            red = int(16 + 90 * mix)
            green = int(24 + 120 * mix)
            blue = int(38 + 150 * mix)
            draw.line((0, row, width, row), fill=(red, green, blue))

        accent_radius = 140
        center_x, center_y = 760, 220
        for ring in range(accent_radius, 0, -8):
            alpha_mix = ring / accent_radius
            color = (
                int(246 * alpha_mix + 34 * (1 - alpha_mix)),
                int(195 * alpha_mix + 92 * (1 - alpha_mix)),
                int(84 * alpha_mix + 166 * (1 - alpha_mix)),
            )
            draw.ellipse(
                (
                    center_x - ring,
                    center_y - ring,
                    center_x + ring,
                    center_y + ring,
                ),
                outline=color,
                width=6,
            )

        prompt_lines = _wrap_text(prompt.strip() or "Generated preview", 42)
        draw.rounded_rectangle((72, 86, 640, 370), radius=28, fill="#0b1220")
        draw.text((102, 116), "AAIS MOCK IMAGE", fill="#f8fafc")
        draw.text((102, 158), f"Steps: {num_inference_steps}", fill="#94a3b8")
        y = 210
        for line in prompt_lines[:5]:
            draw.text((102, y), line, fill="#e2e8f0")
            y += 34

        return image

    def multimodal_query(self, text_prompt, image=None):
        if image is None:
            return {
                "response": self.generate_text(text_prompt, max_length=256, temperature=0.5),
                "mode": "mock",
            }

        analysis = self.analyze_image(image)
        return {
            "response": (
                "Mock multimodal response.\n\n"
                f"Prompt: {text_prompt[:120]}\n"
                f"Image: {analysis['description']}"
            ),
            "image_analysis": analysis,
            "mode": "mock",
        }


class MockStreamingTextGenerator:
    """Simple word-by-word streaming fallback."""

    def generate_stream(
        self,
        prompt,
        max_new_tokens=512,
        temperature=0.7,
        top_p=0.95,
        routing_profile=None,
        do_sample=None,
        input_max_length=None,
        **kwargs,
    ):
        base_text = (
            "Mock streaming response from AAIS local mode. "
            f"Prompt preview: {prompt.strip()[:120]}"
        )
        words = base_text.split()
        collected = []
        token_budget = max(1, min(max_new_tokens, len(words)))

        for word in words[:token_budget]:
            token = f"{word} "
            collected.append(token)
            yield {
                "token": token,
                "text_so_far": "".join(collected),
                "finished": False,
            }

        yield {
            "token": "",
            "text_so_far": "".join(collected).strip(),
            "finished": True,
            "stop_reason": "mock_complete",
            "finish_reason": "stop",
            "output_tokens_used": int(len(collected)),
            "output_token_budget": int(max_new_tokens or 0),
        }


def _wrap_text(text, max_chars):
    words = text.split()
    lines = []
    current = []
    current_len = 0

    for word in words:
        projected = current_len + len(word) + (1 if current else 0)
        if projected > max_chars and current:
            lines.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len = projected

    if current:
        lines.append(" ".join(current))

    return lines or ["Generated preview"]
