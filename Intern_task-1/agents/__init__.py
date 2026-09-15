"""
Agents Package Initialization
=============================
Exposes the 6-stage autonomous closed-loop retention multi-agent system.
"""

from agents.observer import ObserverAgent
from agents.analyst import AnalystAgent
from agents.diagnostic import DiagnosticAgent
from agents.strategist import StrategistAgent, ContextualBanditStrategist, default_bandit, RETENTION_ACTIONS
from agents.executor import ExecutorAgent
from agents.feedback import FeedbackAgent
from agents.pipeline import NexusMultiAgentPipeline

__all__ = [
    'ObserverAgent',
    'AnalystAgent',
    'DiagnosticAgent',
    'StrategistAgent',
    'ContextualBanditStrategist',
    'default_bandit',
    'RETENTION_ACTIONS',
    'ExecutorAgent',
    'FeedbackAgent',
    'NexusMultiAgentPipeline',
]
