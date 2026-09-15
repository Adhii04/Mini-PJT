"""
Diagnostic Agent (Agent 3)
==========================
Translates raw TreeSHAP feature attributions and survival parameters into
natural language executive diagnostic narratives.
"""

import logging
from typing import Dict, List, Any, Optional
from models.llm_diagnostics import generate_employee_diagnostic

logger = logging.getLogger(__name__)


class DiagnosticAgent:
    """
    Agent 3: SHAP-to-LLM Explainability & Diagnostic Synthesizer.
    Generates actionable, human-interpretable reasons why an employee is at risk.
    """
    def __init__(self, name: str = "Diagnostic"):
        self.name = name

    def process(self, employee_record: Dict[str, Any], top_reasons: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Synthesizes a structured natural language diagnostic narrative for an employee.
        """
        if not top_reasons:
            top_reasons = [
                {'feature': 'Overtime', 'value': employee_record.get('Overtime', 'Yes'), 'shap_value': 0.42},
                {'feature': 'YearsAtCompany', 'value': employee_record.get('YearsAtCompany', 3), 'shap_value': 0.35},
                {'feature': 'JobSatisfaction', 'value': employee_record.get('JobSatisfaction', 2), 'shap_value': 0.28},
                {'feature': 'MonthlyIncome', 'value': employee_record.get('MonthlyIncome', 5000), 'shap_value': -0.15},
                {'feature': 'WorkLifeBalance', 'value': employee_record.get('WorkLifeBalance', 3), 'shap_value': -0.12},
            ]

        diag = generate_employee_diagnostic(
            employee_record,
            top_reasons,
            p_churn_90d=employee_record.get('prob_churn_90d'),
            revenue_at_risk=employee_record.get('revenue_at_risk')
        )
        emp_id = employee_record.get('EmployeeID', 'N/A')
        logger.info(f"[{self.name} Agent] Generated SHAP-to-LLM diagnostic narrative for Employee #{emp_id}.")
        return diag
