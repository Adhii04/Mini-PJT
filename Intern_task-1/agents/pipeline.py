"""
Nexus Multi-Agent Retention Pipeline
====================================
Orchestrates the complete 6-stage closed-loop multi-agent system:
  Observer -> Analyst -> Diagnostic -> Strategist -> Executor -> Feedback
"""

import logging
from typing import Dict, List, Any, Optional

from agents.observer import ObserverAgent
from agents.analyst import AnalystAgent
from agents.diagnostic import DiagnosticAgent
from agents.strategist import StrategistAgent, ContextualBanditStrategist, default_bandit
from agents.executor import ExecutorAgent
from agents.feedback import FeedbackAgent

logger = logging.getLogger(__name__)


class NexusMultiAgentPipeline:
    """
    Unified Multi-Agent Orchestrator.
    Coordinates all autonomous retention agents into a seamless pipeline.
    """
    def __init__(self, bandit: Optional[ContextualBanditStrategist] = None):
        self.bandit = bandit or default_bandit
        self.observer = ObserverAgent()
        self.analyst = AnalystAgent()
        self.diagnostic = DiagnosticAgent()
        self.strategist = StrategistAgent(bandit=self.bandit)
        self.executor = ExecutorAgent()
        self.feedback = FeedbackAgent(bandit=self.bandit)

    def run_full_pipeline_for_employee(self, employee_record: Dict[str, Any], top_reasons: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Executes the entire agent chain for an individual employee record.
        """
        # 1. Observer: Ingest & validate
        observed = self.observer.process([employee_record])[0]

        # 2. Analyst: Compute ELV & Revenue at Risk
        analyzed = self.analyst.process([observed])[0]

        # 3. Diagnostic: Synthesize SHAP-LLM narrative
        diag_res = self.diagnostic.process(analyzed, top_reasons)

        # 4. Strategist: Select optimal intervention arm via Contextual Bandit
        strat_res = self.strategist.process(analyzed)

        # 5. Executor: Build Manager Action Card
        card = self.executor.process(analyzed, diag_res, strat_res)

        return {
            'employee_info': analyzed,
            'diagnostic': diag_res,
            'strategist': strat_res,
            'action_card': card
        }

    def process_intervention_feedback(self, employee_record: Dict[str, Any], action: str, outcome_status: str) -> Dict[str, Any]:
        """
        Processes 30-day intervention feedback and updates policy weights.
        """
        return self.feedback.process(employee_record, action, outcome_status)
