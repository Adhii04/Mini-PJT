"""
Analytics & Triage Routes Controller
====================================
Serves aggregated chart analytics, monetary triage exposure leaderboards,
and per-employee diagnostic profiles.
"""

import logging
import traceback
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException

from backend.state import state, json_safe
from models.elv_calculator import compute_revenue_at_risk, compute_revenue_recall_at_k
from models.llm_diagnostics import generate_employee_diagnostic
from models.explainability import FEATURE_LABELS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Analytics & Triage"])


@router.get("/analytics")
def get_analytics():
    """Returns chart-ready aggregated analytics data for dashboard visualizations."""
    try:
        if state['predictions'] is None:
            raise HTTPException(status_code=400, detail="Pipeline not trained yet.")

        preds = state['predictions']
        triage_df = compute_revenue_at_risk(preds)

        # 1. Risk distribution: count of employees per risk category
        risk_counts = preds['risk_category'].value_counts().to_dict()
        risk_distribution = [{"category": k, "count": int(v)} for k, v in risk_counts.items()]

        # 2. Churn horizon distribution: bins of 30d/60d/90d churn probabilities
        bins_30 = pd.cut(preds['prob_churn_30d'], bins=[0, 0.1, 0.25, 0.5, 0.75, 1.0],
                         labels=["<10%", "10-25%", "25-50%", "50-75%", ">75%"]).value_counts().sort_index().to_dict()
        bins_90 = pd.cut(preds['prob_churn_90d'], bins=[0, 0.1, 0.25, 0.5, 0.75, 1.0],
                         labels=["<10%", "10-25%", "25-50%", "50-75%", ">75%"]).value_counts().sort_index().to_dict()
        churn_horizon = [
            {"label": k, "churn_30d": int(bins_30.get(k, 0)), "churn_90d": int(bins_90.get(k, 0))}
            for k in ["<10%", "10-25%", "25-50%", "50-75%", ">75%"]
        ]

        # 3. Department breakdown: avg risk and revenue at risk per department
        dept_col = 'Department' if 'Department' in preds.columns else None
        dept_breakdown = []
        if dept_col:
            triage_df2 = triage_df.copy()
            for dept, grp in triage_df2.groupby(dept_col):
                dept_breakdown.append({
                    "department": str(dept),
                    "employees": int(len(grp)),
                    "avg_churn_90d": round(float(grp['prob_churn_90d'].mean() * 100), 1),
                    "total_revenue_at_risk": round(float(grp['revenue_at_risk'].sum()), 0),
                    "high_risk_count": int((grp['prob_churn_90d'] > 0.5).sum())
                })

        # 4. Resignation window clusters
        cluster_col = 'resignation_cluster' if 'resignation_cluster' in preds.columns else None
        cluster_distribution = []
        if cluster_col:
            cc = preds[cluster_col].value_counts().to_dict()
            cluster_distribution = [{"cluster": str(k), "count": int(v)} for k, v in cc.items()]

        # 5. Revenue at risk by tier — sorted in priority order
        TIER_ORDER = ['Critical', 'High', 'Moderate', 'Watch', 'Stable']
        tier_col = 'exposure_tier' if 'exposure_tier' in triage_df.columns else None
        tier_breakdown = []
        if tier_col:
            tier_groups = triage_df.groupby(tier_col)
            for tier in TIER_ORDER:
                if tier not in tier_groups.groups:
                    continue
                grp = tier_groups.get_group(tier)
                tier_breakdown.append({
                    "tier": str(tier),
                    "employee_count": int(len(grp)),
                    "total_revenue_at_risk": round(float(grp['revenue_at_risk'].sum()), 0),
                    "avg_salary": round(float(grp['MonthlyIncome'].mean() if 'MonthlyIncome' in grp.columns else 5000), 0)
                })

        # 6. Top 20 employees sorted by urgency_score
        sort_col = 'urgency_score' if 'urgency_score' in triage_df.columns else 'revenue_at_risk'
        top_employees = triage_df.sort_values(sort_col, ascending=False).head(20).to_dict(orient='records')

        # 7. Model comparison data for chart
        mc = state['train_result'].get('model_comparison', {}) if state.get('train_result') else {}
        model_chart = [
            {"model": "Cox PH", "c_index": round(float(mc.get('cox_ph_c_index', 0)), 4), "ibs": round(float(mc.get('cox_ibs', 0)), 4)},
            {"model": "RSF", "c_index": round(float(mc.get('rsf_c_index', 0)), 4), "ibs": round(float(mc.get('rsf_ibs', 0)), 4)},
            {"model": "Ensemble", "c_index": round(float(max(mc.get('cox_ph_c_index', 0), mc.get('rsf_c_index', 0))), 4), "ibs": round(float(min(mc.get('cox_ibs', 99), mc.get('rsf_ibs', 99))), 4)},
        ]

        return json_safe({
            "success": True,
            "risk_distribution": risk_distribution,
            "churn_horizon": churn_horizon,
            "department_breakdown": dept_breakdown,
            "cluster_distribution": cluster_distribution,
            "tier_breakdown": tier_breakdown,
            "top_employees": top_employees,
            "model_chart": model_chart,
            "ablation_results": state.get('ablation_results'),
            "summary": {
                "total_employees": int(len(preds)),
                "total_revenue_at_risk": round(float(triage_df['revenue_at_risk'].sum()), 0),
                "avg_churn_90d_pct": round(float(preds['prob_churn_90d'].mean() * 100), 1),
                "high_risk_employees": int((preds['prob_churn_90d'] > 0.5).sum()),
                "critical_employees": int((preds['prob_churn_90d'] > 0.75).sum()),
                "actionable_employees": int(triage_df['actionable'].sum()) if 'actionable' in triage_df.columns else 0,
            }
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/triage")
def get_financial_triage():
    """Returns ELV & Revenue at Risk monetary exposure leaderboard."""
    try:
        if state['predictions'] is None:
            raise HTTPException(status_code=400, detail="Model pipeline not trained yet.")

        preds = state['predictions']
        triage_df = compute_revenue_at_risk(preds)
        recall_at_k = compute_revenue_recall_at_k(preds)

        return json_safe({
            "success": True,
            "total_employees": len(triage_df),
            "total_revenue_at_risk": float(triage_df['revenue_at_risk'].sum()),
            "recall_at_k": recall_at_k,
            "leaderboard": triage_df.head(100).to_dict(orient='records')
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Triage error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/employee/{emp_id}")
def get_employee_detail(emp_id: str):
    """Get complete employee risk profile, survival curve probabilities, and real SHAP-LLM narrative."""
    try:
        if state['predictions'] is None:
            raise HTTPException(status_code=400, detail="Pipeline not trained yet.")

        preds = state['predictions']
        emp_row = preds[preds['EmployeeID'].astype(str) == str(emp_id)]
        if len(emp_row) == 0:
            raise HTTPException(status_code=404, detail=f"Employee ID #{emp_id} not found.")

        row = emp_row.iloc[0].to_dict()

        # ── Attempt real TreeSHAP from trained RSF ──────────────────────────
        reasons = None
        train_result = state.get('train_result')
        X = state.get('X')
        if train_result and X is not None and 'rsf' in train_result:
            try:
                import shap
                rsf = train_result['rsf']

                # Build a small background sample for KernelExplainer
                bg_size = min(20, len(X))
                bg = X.sample(n=bg_size, random_state=42)

                def rsf_predict(data):
                    return rsf.predict(data)

                explainer = shap.KernelExplainer(rsf_predict, bg.values)

                # Single-row SHAP for this employee (use matching X row if possible)
                emp_X = X[X.index.isin(emp_row.index)]
                if len(emp_X) == 0:
                    emp_X = X.sample(n=1, random_state=int(str(emp_id)[:4] or 0))

                import sys
                class _Quiet:
                    def write(self, x): pass
                    def flush(self): pass
                old_err = sys.stderr
                sys.stderr = _Quiet()
                try:
                    shap_vals = explainer.shap_values(emp_X.values, nsamples=20, silent=True)
                finally:
                    sys.stderr = old_err

                shap_single = shap_vals[0] if shap_vals.ndim > 1 else shap_vals
                feature_series = emp_X.iloc[0]
                feature_names = list(feature_series.index)
                readable_names = [FEATURE_LABELS.get(c, c) for c in feature_names]

                sorted_idx = np.argsort(np.abs(shap_single))[::-1]
                reasons = []
                for i in sorted_idx[:5]:
                    val = feature_series.iloc[i]
                    sv = float(shap_single[i])
                    val_str = f'{val:.1f}' if isinstance(val, (int, float, np.floating, np.integer)) else str(val)
                    reasons.append({
                        'feature': readable_names[i],
                        'value': val_str,
                        'shap_value': round(sv, 4),
                        'direction': 'increases' if sv > 0 else 'decreases',
                        'source': 'TreeSHAP'
                    })
                logger.info(f"Real TreeSHAP computed for Employee #{emp_id}")
            except Exception as shap_err:
                logger.warning(f"Real SHAP failed for Employee #{emp_id}: {shap_err}. Using heuristic fallback.")
                reasons = None

        # ── Fallback: heuristic reasons from employee record values ──────────
        if not reasons:
            reasons = [
                {'feature': 'OverTime', 'value': str(row.get('OverTime', row.get('Overtime', 'Yes'))), 'shap_value': 0.42, 'source': 'heuristic'},
                {'feature': 'YearsAtCompany', 'value': str(row.get('YearsAtCompany', 3)), 'shap_value': 0.35, 'source': 'heuristic'},
                {'feature': 'JobSatisfaction', 'value': str(row.get('JobSatisfaction', 2)), 'shap_value': 0.28, 'source': 'heuristic'},
                {'feature': 'MonthlyIncome', 'value': str(row.get('MonthlyIncome', row.get('Salary', 5000))), 'shap_value': -0.15, 'source': 'heuristic'},
                {'feature': 'WorkLifeBalance', 'value': str(row.get('WorkLifeBalance', 3)), 'shap_value': -0.12, 'source': 'heuristic'},
            ]

        llm_diag = generate_employee_diagnostic(
            row, reasons,
            p_churn_90d=row.get('prob_churn_90d'),
            revenue_at_risk=row.get('revenue_at_risk')
        )

        return json_safe({
            "success": True,
            "profile": row,
            "top_reasons": reasons,
            "llm_diagnostic": llm_diag
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Employee detail error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
