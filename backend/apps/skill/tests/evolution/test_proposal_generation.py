# -*- coding: utf-8 -*-
from unittest.mock import patch

from django.test import TestCase

from apps.skill.evolution.services import RuleEvolutionService


class RuleEvolutionProposalTests(TestCase):
    def test_generate_proposal_skips_on_llm_error(self):
        service = RuleEvolutionService()
        pattern = {
            "dimension": "hook",
            "pattern": "钩子维度持续偏低",
            "suggestion": "强化开场",
            "affected_projects": [],
        }
        with patch.object(
            service,
            "_call_llm_propose",
            return_value={"error": "llm unavailable"},
        ):
            proposal = service.generate_proposal(pattern)
        self.assertIsNone(proposal)

    def test_generate_proposal_sets_pending_approval_and_target_skill(self):
        from apps.skill.evolution.models import RuleEvolutionProposal

        service = RuleEvolutionService()
        pattern = {
            "dimension": "structure",
            "pattern": "结构维度持续偏低",
            "suggestion": "优化结构模板",
            "affected_projects": [],
        }
        with patch.object(
            service,
            "_call_llm_propose",
            return_value={"target_tier": "Tier2", "target_scope_key": "family-revenge"},
        ):
            proposal = service.generate_proposal(pattern)
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.status, RuleEvolutionProposal.STATUS_PENDING_APPROVAL)
        self.assertEqual(proposal.target_skill_id, "quality-structure")
