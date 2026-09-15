"""
Analyst Agent (Agent 2)
=======================
Calculates Employee Lifetime Value (ELV) and confidence-weighted Revenue at Risk.
Performs financial prioritization, risk tier assignment, and urgency scoring.
"""

import logging
import pandas as pd
from typing import List, Dict, Any
from models.elv_calculator import compute_revenue_at_risk

logger = logging.getLogger(__name__)


class AnalystAgent:
    """
    Agent 2: Financial Triage & Economic Impact Analyst.
    Transforms raw survival probabilities into monetary exposure metrics.
    """
    def __init__(self, name: str = "Analyst"):
        self.name = name

    def process(self, employee_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Executes financial triage and returns records sorted by urgency score.
        """
        df = pd.DataFrame(employee_records)
        df_triage = compute_revenue_at_risk(df)
        logger.info(f"[{self.name} Agent] Computed ELV & Revenue at Risk for {len(df_triage)} employee(s).")
        return df_triage.to_dict(orient='records')
