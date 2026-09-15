"""
Executor Agent (Agent 5)
========================
Synthesizes the diagnostic narrative and strategist intervention into a
complete, dispatch-ready Manager Action Card with concrete action steps.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ExecutorAgent:
    """
    Agent 5: Retention Action Card Builder & Dispatcher.
    Generates personalized execution plans for people managers.
    """
    def __init__(self, name: str = "Executor"):
        self.name = name

    def process(self, employee_record: Dict[str, Any], diagnostic_result: Dict[str, Any], strategist_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds a comprehensive Manager Action Card for execution.
        """
        emp_id = employee_record.get('EmployeeID', 'N/A')
        role = employee_record.get('JobRole', 'Team Member')
        dept = employee_record.get('Department', 'General')
        action = strategist_result.get('selected_action', 'Managerial 1:1')
        narrative = diagnostic_result.get('narrative', '')
        rar = float(employee_record.get('revenue_at_risk', 0.0))

        action_card = {
            'title': f"Nexus Retention Action Card — Employee #{emp_id}",
            'employee_id': emp_id,
            'job_role': role,
            'department': dept,
            'revenue_at_risk': f"${rar:,.2f}",
            'recommended_intervention': action,
            'diagnostic_narrative': narrative,
            'action_steps': [
                f"1. Schedule proactive 1:1 briefing with {role} within 5 business days.",
                f"2. Present calibrated retention initiative: '{action}'.",
                "3. Record resolution progress & outcome in the Nexus system within 30 days."
            ],
            'status': 'Action Card Prepared & Dispatched'
        }
        logger.info(f"[{self.name} Agent] Generated Manager Action Card for Employee #{emp_id}.")
        return action_card
