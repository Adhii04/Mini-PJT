"""
Feedback Agent (Agent 6)
========================
Closes the autonomous learning loop by ingesting 30-day post-intervention outcomes
and updating Contextual Bandit policy parameters dynamically.
"""

import logging
from typing import Dict, Any
from agents.strategist import ContextualBanditStrategist, default_bandit

logger = logging.getLogger(__name__)


class FeedbackAgent:
    """
    Agent 6: Closed-Loop Outcome Ingestion & Policy Updater.
    Updates the LinUCB Contextual Bandit weights based on real-world retention success.
    """
    def __init__(self, bandit: ContextualBanditStrategist = None, name: str = "Feedback"):
        self.bandit = bandit or default_bandit
        self.name = name

    def process(self, employee_record: Dict[str, Any], action: str, outcome_status: str) -> Dict[str, Any]:
        """
        Processes feedback outcome ('retained' -> +1.0, 'churned' -> -1.0) and updates bandit policy.
        """
        is_retained = outcome_status.lower() == 'retained'
        reward = 1.0 if is_retained else -1.0

        self.bandit.update_policy(employee_record, action, reward)
        emp_id = employee_record.get('EmployeeID', 'N/A')

        logger.info(f"[{self.name} Agent] Processed outcome for Employee #{emp_id}: {outcome_status.upper()} (Reward: {reward:+.1f}).")
        return {
            'employee_id': emp_id,
            'action': action,
            'outcome': outcome_status,
            'reward': reward,
            'status': 'Policy Parameters Updated Successfully'
        }
