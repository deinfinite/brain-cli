"""Tests for brain.depth module."""

import pytest
from brain.depth import DEPTH_CONFIGS, VALID_DEPTHS, get_depth_config, merge_depth_into_params


class TestDepthConfigs:
    """Depth presets must cover article's implied depth levels."""

    def test_all_depths_exist(self):
        assert set(VALID_DEPTHS) == {"quick", "normal", "deep", "exhaustive"}

    def test_quick_is_light(self):
        cfg = get_depth_config("quick")
        assert cfg["max_output_tokens"] == 2048
        assert cfg["reasoning_effort"] == "low"

    def test_deep_is_heavy(self):
        cfg = get_depth_config("deep")
        assert cfg["max_output_tokens"] == 16384
        assert cfg["reasoning_effort"] == "high"

    def test_exhaustive_is_max(self):
        cfg = get_depth_config("exhaustive")
        assert cfg["max_output_tokens"] == 32768

    def test_invalid_depth_raises(self):
        with pytest.raises(ValueError, match="Unknown depth"):
            get_depth_config("super_deep")


class TestMergeDepthIntoParams:
    """Merging depth config into API params."""

    def test_merge_adds_tokens_and_temp(self):
        params = {"model": "test", "messages": []}
        merged = merge_depth_into_params(params, "deep")
        assert "max_tokens" in merged
        assert "temperature" in merged

    def test_explicit_overrides_win(self):
        params = {"model": "test", "messages": []}
        merged = merge_depth_into_params(params, "deep", max_tokens_override=999, temperature_override=0.9)
        assert merged["max_tokens"] == 999
        assert merged["temperature"] == 0.9

    def test_reasoning_effort_included(self):
        params = {"model": "test", "messages": []}
        merged = merge_depth_into_params(params, "deep")
        assert merged.get("reasoning_effort") == "high"
