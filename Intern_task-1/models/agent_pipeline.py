"""
Models Agent Pipeline Bridge
============================
Maintains backward compatibility by importing from the dedicated `agents` package.
"""

from agents.observer import ObserverAgent
from agents.analyst import AnalystAgent
from agents.diagnostic import DiagnosticAgent
from agents.strategist import StrategistAgent, ContextualBanditStrategist, default_bandit, RETENTION_ACTIONS
from agents.executor import ExecutorAgent
from agents.feedback import FeedbackAgent
from agents.pipeline import NexusMultiAgentPipeline

# Backward compatible alias for singleton bandit
band_strategist = default_bandit

__all__ = [
    'RETENTION_ACTIONS',
    'ContextualBanditStrategist',
    'band_strategist',
    'default_bandit',
    'ObserverAgent',
    'AnalystAgent',
    'DiagnosticAgent',
    'StrategistAgent',
    'ExecutorAgent',
    'FeedbackAgent',
    'NexusMultiAgentPipeline',
]
