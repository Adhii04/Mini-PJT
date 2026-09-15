"""
Model Evaluation
================
Computes C-index for Cox PH and RSF models and compares them.
This module is kept for backward compatibility — the actual metric
computation is now in models/metrics.py.
"""

import numpy as np
from models.metrics import (
    compute_cox_c_index,
    compute_rsf_c_index
)


def compare_models(cox_c_index, rsf_c_index):
    """
    Compare Cox PH and RSF models by C-index.
    Returns comparison dict (backward compatible with existing frontend).
    """
    if cox_c_index > rsf_c_index:
        winner = 'Cox PH'
        margin = round(cox_c_index - rsf_c_index, 4)
    elif rsf_c_index > cox_c_index:
        winner = 'Random Survival Forest'
        margin = round(rsf_c_index - cox_c_index, 4)
    else:
        winner = 'Tie'
        margin = 0.0

    return {
        'cox_ph_c_index': cox_c_index,
        'rsf_c_index': rsf_c_index,
        'winner': winner,
        'margin': margin,
        'interpretation': (
            f"{'Cox PH' if winner == 'Cox PH' else 'Random Survival Forest'} "
            f"performs better with a C-index of "
            f"{max(cox_c_index, rsf_c_index):.4f} "
            f"(margin: {margin:.4f}). "
            f"A C-index > 0.7 indicates good discrimination."
        ) if winner != 'Tie' else (
            f"Both models perform equally with a C-index of {cox_c_index:.4f}."
        )
    }
