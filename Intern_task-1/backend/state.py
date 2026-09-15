"""
Backend State Management Module
===============================
Provides thread-safe in-memory session state storage and JSON sanitization utilities.
"""

import os
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

# Upload storage directory
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Centralized In-Memory Runtime State
state: Dict[str, Any] = {
    'df': None,
    'X': None,
    'T': None,
    'E': None,
    'employee_info': None,
    'scaler': None,
    'train_result': None,
    'predictions': None,
    'ensemble_weights': None,
    'ablation_results': None,
}


def reset_state():
    """Resets all runtime state variables."""
    for k in state:
        state[k] = None


def json_safe(obj: Any) -> Any:
    """
    Recursively converts numpy, pandas, NaN, and Inf types into JSON-compliant primitives.
    """
    if isinstance(obj, dict):
        return {str(k): json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [json_safe(item) for item in obj]
    elif isinstance(obj, (pd.DataFrame, pd.Series)):
        return json_safe(obj.to_dict(orient='records') if isinstance(obj, pd.DataFrame) else obj.to_dict())
    elif isinstance(obj, (np.integer, int)):
        return int(obj)
    elif isinstance(obj, (np.floating, float)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return [json_safe(x) for x in obj.tolist()]
    elif obj is None:
        return None
    return obj
