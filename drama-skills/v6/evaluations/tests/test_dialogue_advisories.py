from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from v6.engine.advisories.dialogue import resolve_advisory_patterns


ROOT = Path(__file__).resolve().parents[3]


def load_pack(name: str) -> dict:
    return yaml.safe_load((ROOT / "v6" / "advisories" / name).read_text(encoding="utf-8"))


class DialogueAdvisoryTests(unittest.TestCase):
    def test_voice_tag_is_first_and_profile_is_only_a_suggestion(self):
        result = resolve_advisory_patterns(
            {"character.voice_tag": "avoids direct refusal", "profession": "student"},
            [load_pack("dialogue-voice.yaml")],
        )
        self.assertEqual(result["precedence"][0], "character.voice_tag")
        self.assertIn("avoids direct refusal", result["suggestions"][0])
        self.assertIn("advisory.dialogue-voice#student", result["applied_patterns"])
        self.assertEqual(result["blocking_errors"], [])

    def test_emotion_pattern_requires_matching_context(self):
        pack = load_pack("dialogue-emotion-rhythm.yaml")
        angry = resolve_advisory_patterns({"emotion_state": "anger"}, [pack])
        neutral = resolve_advisory_patterns({"emotion_state": "neutral"}, [pack])
        self.assertIn("advisory.dialogue-emotion-rhythm#anger", angry["applied_patterns"])
        self.assertEqual(neutral["applied_patterns"], [])

    def test_ai_tone_terms_match_by_cluster_context_and_never_block(self):
        pack = load_pack("ai-tone.yaml")
        single_unrelated_term = resolve_advisory_patterns({"candidate_terms": ["hello"]}, [pack])
        single_candidate_term = resolve_advisory_patterns({"candidate_terms": ["因此"]}, [pack])
        clustered_term = resolve_advisory_patterns({"candidate_terms": ["因此", "然而"]}, [pack])
        self.assertEqual(single_unrelated_term["applied_patterns"], [])
        self.assertEqual(single_candidate_term["applied_patterns"], [])
        self.assertIn("advisory.ai-tone#formal-connector-cluster", clustered_term["applied_patterns"])
        self.assertEqual(clustered_term["blocking_errors"], [])


if __name__ == "__main__":
    unittest.main()
