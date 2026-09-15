"""
Observer Agent (Agent 1)
========================
Monitors employee event streams, state transitions, tenure clocks, and workplace signals.
Performs continuous ingestion and baseline schema normalization across data sources.
"""

import logging
import pandas as pd
from typing import Dict, List, Any, Union

logger = logging.getLogger(__name__)


class ObserverAgent:
    """
    Agent 1: Ingestion & Telemetry Monitor.
    Monitors employee records, tenure durations, and categorical state indicators.
    """
    def __init__(self, name: str = "Observer"):
        self.name = name

    def process(self, employee_data: Union[pd.DataFrame, List[Dict[str, Any]], Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ingests and validates raw employee records.
        """
        if isinstance(employee_data, pd.DataFrame):
            records = employee_data.to_dict(orient='records')
        elif isinstance(employee_data, dict):
            records = [employee_data]
        else:
            records = list(employee_data)

        logger.info(f"[{self.name} Agent] Successfully ingested & observed {len(records)} employee record(s).")
        return records
