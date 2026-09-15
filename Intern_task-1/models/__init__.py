"""
Models Package Initialization
=============================
Provides core machine learning, survival analysis, financial risk calculation,
explainability, and benchmarking models.
"""

from models.survival_models import (
    fit_kaplan_meier,
    fit_cox_ph,
    fit_rsf,
    cox_predict_median,
    cox_predict_risk,
    rsf_predict_median,
    rsf_predict_risk,
)
from models.training import train_pipeline
from models.prediction import (
    compute_ensemble_weights,
    compute_weighted_ensemble_medians,
    compute_ensemble_survival_curves,
    compute_risk_thresholds,
    assign_risk_category_data_driven,
    assign_resignation_cluster,
    determine_model_source,
)
from models.metrics import (
    compute_cox_c_index,
    compute_rsf_c_index,
    compute_integrated_brier_score,
    compute_calibration_data,
    compute_cox_hazard_ratios,
)
from models.validation import cross_validate_cox, cross_validate_rsf
from models.elv_calculator import (
    compute_elv,
    compute_revenue_at_risk,
    compute_revenue_recall_at_k,
)
from models.explainability import (
    compute_shap_values,
    global_shap_plot,
    employee_shap_plot,
    get_top_reasons,
    generate_detailed_explanation,
)
from models.llm_diagnostics import generate_employee_diagnostic
from models.ablation import run_ablation_study
from models.benchmarking import run_dual_dataset_benchmarks

__all__ = [
    'fit_kaplan_meier',
    'fit_cox_ph',
    'fit_rsf',
    'cox_predict_median',
    'cox_predict_risk',
    'rsf_predict_median',
    'rsf_predict_risk',
    'train_pipeline',
    'compute_ensemble_weights',
    'compute_weighted_ensemble_medians',
    'compute_ensemble_survival_curves',
    'compute_risk_thresholds',
    'assign_risk_category_data_driven',
    'assign_resignation_cluster',
    'determine_model_source',
    'compute_cox_c_index',
    'compute_rsf_c_index',
    'compute_integrated_brier_score',
    'compute_calibration_data',
    'compute_cox_hazard_ratios',
    'cross_validate_cox',
    'cross_validate_rsf',
    'compute_elv',
    'compute_revenue_at_risk',
    'compute_revenue_recall_at_k',
    'compute_shap_values',
    'global_shap_plot',
    'employee_shap_plot',
    'get_top_reasons',
    'generate_detailed_explanation',
    'generate_employee_diagnostic',
    'run_ablation_study',
    'run_dual_dataset_benchmarks',
]
