"""
Ablation & Benchmarks Route Controller
======================================
Executes Section 10 Scientific Ablation matrix and dual-dataset comparisons.
"""

import logging
from fastapi import APIRouter, HTTPException

from backend.state import state, json_safe
from models.ablation import run_ablation_study
from models.benchmarking import run_dual_dataset_benchmarks

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Ablation & Benchmarks"])


@router.post("/ablation")
def execute_ablation():
    """Runs the Section 10 Scientific Ablation Matrix comparing all 7 paper configurations."""
    try:
        if state['X'] is None or state['df'] is None:
            raise HTTPException(status_code=400, detail="Please train or load dataset first.")

        res = run_ablation_study(state['X'], state['T'], state['E'], state['employee_info'])
        summary_table = res.get('summary_table', [])
        state['ablation_results'] = summary_table

        return json_safe({
            "success": True,
            "ablation_results": summary_table
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ablation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/benchmark/dual")
def execute_dual_benchmark():
    """Runs comparative paper benchmark across IBM HR Analytics and Healthcare datasets."""
    try:
        res = run_dual_dataset_benchmarks()
        return json_safe({
            "success": True,
            "benchmark_results": res
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dual benchmark error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
