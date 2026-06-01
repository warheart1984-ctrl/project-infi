from external.ai.beatbox.adapter import BeatboxAdapter, SimpleBeatboxFallback


class RecordingProvider:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def generate(self, input_data):
        self.calls.append(input_data)
        return self.result


class RaisingProvider:
    def __init__(self):
        self.calls = []

    def generate(self, input_data):
        self.calls.append(input_data)
        raise RuntimeError("boom")


def valid_input():
    return {
        "narrative_state": "storm breaking over the city",
        "emotion": "urgent",
        "pacing": "fast",
    }


def test_beatbox_adapter_returns_primary_output_for_normal_input():
    primary = RecordingProvider(
        {
            "audio_file": "storm_loop.wav",
            "duration": 3.2,
            "metadata": {"quality": "high"},
            "status": "ok",
        }
    )
    adapter = BeatboxAdapter(primary=primary)

    result = adapter.generate(valid_input())

    assert result["audio_file"] == "storm_loop.wav"
    assert result["output"] == "storm_loop.wav"
    assert result["status"] == "ok"
    assert result["metadata"]["quality"] == "high"
    assert primary.calls == [valid_input()]


def test_beatbox_adapter_returns_no_provider_failure_when_unwired():
    adapter = BeatboxAdapter()

    result = adapter.generate(valid_input())

    assert result["status"] == "failed"
    assert result["reason"] == "no_provider"
    assert result["audio_file"] is None


def test_beatbox_adapter_rejects_bad_input_before_provider_call():
    primary = RecordingProvider(
        {
            "audio_file": "should_not_run.wav",
            "duration": 2.0,
            "metadata": {},
            "status": "ok",
        }
    )
    adapter = BeatboxAdapter(primary=primary)

    result = adapter.generate({"emotion": "calm"})

    assert result["status"] == "failed"
    assert result["reason"] == "invalid_input"
    assert result["metadata"]["details"]["missing_fields"] == [
        "narrative_state",
        "pacing",
    ]
    assert primary.calls == []


def test_beatbox_adapter_uses_fallback_after_primary_failure():
    primary = RaisingProvider()
    fallback = SimpleBeatboxFallback()
    adapter = BeatboxAdapter(primary=primary, fallback=fallback)

    result = adapter.generate(valid_input())

    assert result["status"] == "fallback"
    assert result["audio_file"] == "basic_tone.wav"
    assert result["metadata"]["provider"] == "simple_fallback"
    assert primary.calls == [valid_input()]
