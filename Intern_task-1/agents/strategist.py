"""
Strategist Agent (Agent 4)
==========================
Implements a LinUCB (Linear Upper Confidence Bound) Contextual Multi-Armed Bandit
that selects optimal retention actions tailored to each employee's context vector.
"""

import logging
import numpy as np
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)

# Standard candidate retention action arms
RETENTION_ACTIONS = [
    "Salary Review",
    "L&D Offer",
    "Managerial 1:1",
    "Flexible Work",
    "Retention Bonus"
]


class ContextualBanditStrategist:
    """
    LinUCB Contextual Bandit Model.
    Selects action arm maximizing:
    UCB score = theta_a^T x_i + alpha * sqrt(x_i^T A_a^{-1} x_i)
    """
    def __init__(self, n_features: int = 10, alpha: float = 1.0, actions: List[str] = None):
        self.n_features = n_features
        self.alpha = alpha
        self.actions = actions or RETENTION_ACTIONS

        # LinUCB state matrices for each arm
        self.A = {a: np.identity(n_features) for a in self.actions}
        self.b = {a: np.zeros((n_features, 1)) for a in self.actions}

    def _extract_context_vector(self, employee_dict: Dict[str, Any]) -> np.ndarray:
        """Extracts normalized 10-dimensional numeric context vector x_i."""
        v = np.zeros(self.n_features)

        # Feature 0: Normalized Salary / Monthly Income
        sal = float(employee_dict.get('MonthlyIncome', employee_dict.get('Salary', 5000)))
        v[0] = min(sal / 20000.0, 1.0)

        # Feature 1: Normalized Tenure
        tenure = float(employee_dict.get('YearsAtCompany', employee_dict.get('duration_months', 24) / 12.0))
        v[1] = min(tenure / 20.0, 1.0)

        # Feature 2: Overtime Flag
        ot = str(employee_dict.get('OverTime', employee_dict.get('Overtime', 'No'))).lower()
        v[2] = 1.0 if ot in ['yes', '1', 'true'] else 0.0

        # Feature 3: Job Satisfaction (1 to 4 normalized)
        sat = float(employee_dict.get('JobSatisfaction', 3))
        v[3] = (sat - 1.0) / 3.0

        # Feature 4: Work-Life Balance (1 to 4 normalized)
        wlb = float(employee_dict.get('WorkLifeBalance', 3))
        v[4] = (wlb - 1.0) / 3.0

        # Feature 5: Promotions count
        prom = float(employee_dict.get('PromotionCount', employee_dict.get('YearsSinceLastPromotion', 0)))
        v[5] = min(prom / 5.0, 1.0)

        # Feature 6: Distance from home
        dist = float(employee_dict.get('DistanceFromHome', 10))
        v[6] = min(dist / 50.0, 1.0)

        # Feature 7: 90-day churn probability
        v[7] = float(employee_dict.get('prob_churn_90d', 0.2))

        # Feature 8: Revenue at Risk (normalized)
        rar = float(employee_dict.get('revenue_at_risk', 10000))
        v[8] = min(rar / 100000.0, 1.0)

        # Feature 9: Constant bias
        v[9] = 1.0

        return v.reshape(-1, 1)

    def select_action(self, employee_dict: Dict[str, Any]) -> Tuple[str, Dict[str, float]]:
        """
        Selects the highest-scoring retention intervention arm using LinUCB.
        """
        x = self._extract_context_vector(employee_dict)
        ucb_scores = {}

        for a in self.actions:
            A_inv = np.linalg.inv(self.A[a])
            theta_a = A_inv @ self.b[a]

            expected_r = float((theta_a.T @ x).item())
            var_r = float((x.T @ A_inv @ x).item())
            ucb = expected_r + self.alpha * np.sqrt(max(0.0, var_r))
            ucb_scores[a] = round(ucb, 4)

        best_action = max(ucb_scores, key=ucb_scores.get)
        return best_action, ucb_scores

    def update_policy(self, employee_dict: Dict[str, Any], action: str, reward: float):
        """
        Updates LinUCB parameters with observed intervention outcome reward (+1.0 retained / -1.0 churned).
        """
        if action not in self.actions:
            logger.warning(f"Action '{action}' is not in known action set.")
            return

        x = self._extract_context_vector(employee_dict)
        self.A[action] += x @ x.T
        self.b[action] += reward * x
        logger.info(f"Bandit policy updated for arm '{action}' with reward={reward:+.1f}")


# Singleton default strategist bandit
default_bandit = ContextualBanditStrategist()


class StrategistAgent:
    """
    Agent 4: Contextual Bandit Retention Policy Strategist.
    Selects mathematically optimal retention interventions based on employee context.
    """
    def __init__(self, bandit: ContextualBanditStrategist = None, name: str = "Strategist"):
        self.bandit = bandit or default_bandit
        self.name = name

    def process(self, employee_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Selects the optimal intervention action and returns all arm scores.
        """
        action, ucb_scores = self.bandit.select_action(employee_record)
        emp_id = employee_record.get('EmployeeID', 'N/A')
        logger.info(f"[{self.name} Agent] Selected '{action}' for Employee #{emp_id} (Score: {ucb_scores[action]}).")
        return {
            'selected_action': action,
            'ucb_scores': ucb_scores
        }
