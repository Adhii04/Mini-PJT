"""
Training Pipeline Route Controller
==================================
Handles end-to-end model training, hyperparameter tuning, evaluation,
and auto-execution of Section 10 ablation benchmarking.
"""

import logging
import traceback
from fastapi import APIRouter, HTTPException

from backend.state import state, json_safe
from core.data_processor import get_survival_data
from models.training import train_pipeline
from models.elv_calculator import compute_revenue_at_risk, compute_revenue_recall_at_k
from models.ablation import run_ablation_study

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Model Training"])


@router.post("/train")
def train_model_pipeline():
    """
    Trains the Cox PH + Random Survival Forest weighted ensemble,
    computes multi-horizon survival curves, evaluates metrics, and
    pre-calculates Section 10 ablation benchmark results.
    """
    try:
        if state['df'] is None:
            raise HTTPException(status_code=400, detail="No dataset loaded. Please load or upload a dataset first.")

        df = state['df']
        X, T, E, info, scaler = get_survival_data(df)

        state['X'] = X
        state['T'] = T
        state['E'] = E
        state['employee_info'] = info
        state['scaler'] = scaler

        train_res = train_pipeline(X, T, E, info)
        state['train_result'] = train_res
        state['predictions'] = train_res['predictions']
        state['ensemble_weights'] = train_res['ensemble_weights']

        preds = train_res['predictions']
        triage_df = compute_revenue_at_risk(preds)
        recall_at_k = compute_revenue_recall_at_k(preds)

        # Run Section 10 ablation study automatically on training
        ablation_table = None
        try:
            ablation_res = run_ablation_study(X, T, E, info)
            ablation_table = ablation_res.get('summary_table', [])
            state['ablation_results'] = ablation_table
        except Exception as e_ab:
            logger.warning(f"Auto ablation calculation warning: {e_ab}")

        return json_safe({
            "success": True,
            "total_employees": len(preds),
            "metrics": train_res['metrics'],
            "cross_validation": train_res.get('cross_validation'),
            "ensemble_weights": train_res['ensemble_weights'],
            "best_model": train_res['best_model'],
            "total_revenue_at_risk": float(triage_df['revenue_at_risk'].sum()),
            "recall_at_k": recall_at_k,
            "ablation_results": ablation_table,
            "sample_predictions": preds.head(10).to_dict(orient='records')
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Training pipeline error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
