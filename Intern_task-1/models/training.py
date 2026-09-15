"""
Training Pipeline Module
========================
Orchestrates the entire ML training flow:
1. Train/Test split (80/20, stratified by event)
2. Model fitting (Cox PH + RSF) on training data only
3. Evaluation on held-out test set
4. Cross-validation
5. Hyperparameter tuning for RSF
6. Weighted ensemble computation
7. Full prediction generation for all employees
"""

import logging
import time
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from models.survival_models import (
    fit_kaplan_meier, fit_cox_ph, fit_rsf,
    cox_predict_median, cox_predict_risk,
    rsf_predict_median, rsf_predict_risk
)
from models.metrics import (
    compute_cox_c_index, compute_rsf_c_index,
    compute_integrated_brier_score,
    compute_calibration_data,
    compute_cox_hazard_ratios
)
from models.validation import cross_validate_cox, cross_validate_rsf
from models.prediction import (
    compute_ensemble_weights, compute_weighted_ensemble_medians,
    compute_risk_thresholds, assign_risk_category_data_driven,
    assign_resignation_cluster, determine_model_source
)

logger = logging.getLogger(__name__)


def _tune_rsf_hyperparameters(X_train, T_train, E_train):
    """
    Perform randomized hyperparameter search for RSF.
    Uses a validation split from the training data.

    Returns best_params dict.
    """
    logger.info("Starting RSF hyperparameter tuning...")

    # Parameter grid
    param_candidates = [
        {'n_estimators': 200, 'min_samples_split': 6, 'min_samples_leaf': 3, 'max_features': 'sqrt'},
        {'n_estimators': 300, 'min_samples_split': 4, 'min_samples_leaf': 2, 'max_features': 0.6},
        {'n_estimators': 300, 'min_samples_split': 6, 'min_samples_leaf': 3, 'max_features': 'sqrt'},
        {'n_estimators': 200, 'min_samples_split': 10, 'min_samples_leaf': 5, 'max_features': 0.4},
        {'n_estimators': 300, 'min_samples_split': 4, 'min_samples_leaf': 2, 'max_features': 'sqrt'},
    ]

    # Use a 75/25 split of training data for tuning
    X_t, X_v, T_t, T_v, E_t, E_v = train_test_split(
        X_train, T_train, E_train, test_size=0.25,
        stratify=E_train, random_state=42
    )

    best_score = -1
    best_params = param_candidates[0]

    for i, params in enumerate(param_candidates):
        try:
            full_params = {**params, 'max_depth': None, 'n_jobs': -1, 'random_state': 42}
            y_t = np.array([(bool(e), t) for e, t in zip(E_t, T_t)],
                           dtype=[('event', bool), ('duration', float)])

            from sksurv.ensemble import RandomSurvivalForest
            rsf = RandomSurvivalForest(**full_params)
            rsf.fit(X_t.values, y_t)

            score = compute_rsf_c_index(rsf, X_v, T_v, E_v)
            logger.info(f"  Candidate {i + 1}: C-index={score:.4f} | {params}")

            if score > best_score:
                best_score = score
                best_params = params

        except Exception as e:
            logger.warning(f"  Candidate {i + 1} failed: {e}")

    best_params.update({'max_depth': None, 'n_jobs': -1, 'random_state': 42})
    logger.info(f"Best RSF params: {best_params} (C-index={best_score:.4f})")

    return best_params, best_score


def train_pipeline(X, T, E, employee_info):
    """
    Complete training pipeline with proper evaluation methodology.

    Parameters
    ----------
    X : pd.DataFrame — standardized feature matrix (all employees)
    T : np.ndarray — durations (all employees)
    E : np.ndarray — event indicators (all employees)
    employee_info : pd.DataFrame — display info for all employees

    Returns
    -------
    dict with all trained models, evaluation results, predictions, and metadata
    """
    logger.info("=" * 60)
    logger.info("TRAINING PIPELINE STARTED")
    logger.info(f"Dataset: {len(X)} employees, {int(E.sum())} events, "
                f"{len(X) - int(E.sum())} censored")
    logger.info(f"Features: {X.shape[1]}")
    logger.info("=" * 60)

    pipeline_start = time.time()
    result = {}

    # ================================================================
    # STEP 1: Train/Test Split (80/20, stratified by event)
    # ================================================================
    logger.info("STEP 1: Train/Test split (80/20)...")

    X_train, X_test, T_train, T_test, E_train, E_test = train_test_split(
        X, T, E, test_size=0.20, stratify=E, random_state=42
    )

    # Also split the indices to track which employees are in which set
    train_indices = X_train.index.tolist()
    test_indices = X_test.index.tolist()

    logger.info(f"  Training set: {len(X_train)} ({int(E_train.sum())} events)")
    logger.info(f"  Test set: {len(X_test)} ({int(E_test.sum())} events)")

    result['split'] = {
        'train_size': len(X_train),
        'test_size': len(X_test),
        'train_events': int(E_train.sum()),
        'test_events': int(E_test.sum()),
        'train_censored': int(len(E_train) - E_train.sum()),
        'test_censored': int(len(E_test) - E_test.sum()),
        'train_indices': train_indices,
        'test_indices': test_indices
    }

    # ================================================================
    # STEP 2: Kaplan-Meier (on full data — descriptive, not predictive)
    # ================================================================
    logger.info("STEP 2: Fitting Kaplan-Meier estimator...")
    kmf = fit_kaplan_meier(T, E)
    result['kmf'] = kmf

    # ================================================================
    # STEP 3: Hyperparameter Tuning for RSF
    # ================================================================
    logger.info("STEP 3: RSF hyperparameter tuning...")
    tuning_start = time.time()
    best_rsf_params, tuning_best_score = _tune_rsf_hyperparameters(
        X_train, T_train, E_train
    )
    tuning_time = round(time.time() - tuning_start, 2)
    result['rsf_params'] = best_rsf_params
    result['tuning_time'] = tuning_time
    logger.info(f"  Tuning complete in {tuning_time}s")

    # ================================================================
    # STEP 4: Train Models on Training Data ONLY
    # ================================================================
    logger.info("STEP 4: Training models on training data...")

    # Cox PH
    cox_start = time.time()
    cph = fit_cox_ph(X_train, T_train, E_train)
    cox_train_time = round(time.time() - cox_start, 2)
    result['cph'] = cph
    logger.info(f"  Cox PH trained in {cox_train_time}s")

    # RSF
    rsf_start = time.time()
    rsf = fit_rsf(X_train, T_train, E_train, **{
        k: v for k, v in best_rsf_params.items()
        if k in ['n_estimators', 'min_samples_split', 'min_samples_leaf',
                  'max_features', 'max_depth', 'n_jobs', 'random_state']
    })
    rsf_train_time = round(time.time() - rsf_start, 2)
    result['rsf'] = rsf
    logger.info(f"  RSF trained in {rsf_train_time}s")

    # ================================================================
    # STEP 5: Evaluate on Train AND Test Sets
    # ================================================================
    logger.info("STEP 5: Computing evaluation metrics...")

    # C-index on training data
    cox_train_ci = compute_cox_c_index(cph, X_train, T_train, E_train)
    rsf_train_ci = compute_rsf_c_index(rsf, X_train, T_train, E_train)

    # C-index on test data (THE REAL METRIC)
    cox_test_ci = compute_cox_c_index(cph, X_test, T_test, E_test)
    rsf_test_ci = compute_rsf_c_index(rsf, X_test, T_test, E_test)

    logger.info(f"  Cox PH — Train C-index: {cox_train_ci}, Test C-index: {cox_test_ci}")
    logger.info(f"  RSF    — Train C-index: {rsf_train_ci}, Test C-index: {rsf_test_ci}")

    # Structured arrays for IBS
    y_train_struct = np.array([(bool(e), t) for e, t in zip(E_train, T_train)],
                              dtype=[('event', bool), ('duration', float)])

    # Integrated Brier Score
    cox_train_ibs = compute_integrated_brier_score(cph, 'cox', X_train, T_train, E_train, y_train_struct)
    cox_test_ibs = compute_integrated_brier_score(cph, 'cox', X_test, T_test, E_test, y_train_struct)
    rsf_train_ibs = compute_integrated_brier_score(rsf, 'rsf', X_train, T_train, E_train, y_train_struct)
    rsf_test_ibs = compute_integrated_brier_score(rsf, 'rsf', X_test, T_test, E_test, y_train_struct)

    logger.info(f"  Cox PH — Train IBS: {cox_train_ibs}, Test IBS: {cox_test_ibs}")
    logger.info(f"  RSF    — Train IBS: {rsf_train_ibs}, Test IBS: {rsf_test_ibs}")

    # Calibration data
    cox_calibration = compute_calibration_data(cph, 'cox', X_test, T_test, E_test)
    rsf_calibration = compute_calibration_data(rsf, 'rsf', X_test, T_test, E_test)

    # Cox hazard ratios
    hazard_ratios = compute_cox_hazard_ratios(cph)

    result['metrics'] = {
        'cox': {
            'train_c_index': cox_train_ci,
            'test_c_index': cox_test_ci,
            'train_ibs': cox_train_ibs,
            'test_ibs': cox_test_ibs,
            'train_time': cox_train_time,
            'calibration': cox_calibration,
            'hazard_ratios': hazard_ratios
        },
        'rsf': {
            'train_c_index': rsf_train_ci,
            'test_c_index': rsf_test_ci,
            'train_ibs': rsf_train_ibs,
            'test_ibs': rsf_test_ibs,
            'train_time': rsf_train_time,
            'calibration': rsf_calibration,
            'n_estimators': best_rsf_params.get('n_estimators', 300)
        }
    }

    # ================================================================
    # STEP 6: Cross-Validation
    # ================================================================
    logger.info("STEP 6: Cross-validation (5-fold)...")
    cv_start = time.time()

    cox_cv = cross_validate_cox(X_train, T_train, E_train, n_folds=5)
    rsf_cv = cross_validate_rsf(X_train, T_train, E_train, n_folds=5,
                                rsf_params=best_rsf_params)

    cv_time = round(time.time() - cv_start, 2)
    logger.info(f"  CV complete in {cv_time}s")
    logger.info(f"  Cox PH CV: {cox_cv['mean']:.4f} ± {cox_cv['std']:.4f}")
    logger.info(f"  RSF CV:    {rsf_cv['mean']:.4f} ± {rsf_cv['std']:.4f}")

    result['cross_validation'] = {
        'cox': cox_cv,
        'rsf': rsf_cv,
        'cv_time': cv_time
    }

    # ================================================================
    # STEP 7: Weighted Ensemble
    # ================================================================
    logger.info("STEP 7: Computing weighted ensemble...")

    w_cox, w_rsf = compute_ensemble_weights(cox_test_ci, rsf_test_ci)
    result['ensemble_weights'] = {'cox': w_cox, 'rsf': w_rsf}

    # Determine best model
    if cox_test_ci > rsf_test_ci:
        best_model = 'Cox PH'
    elif rsf_test_ci > cox_test_ci:
        best_model = 'Random Survival Forest'
    else:
        best_model = 'Tie'

    result['best_model'] = best_model
    logger.info(f"  Best model: {best_model}")

    # ================================================================
    # STEP 8: Generate Predictions for ALL Employees
    # ================================================================
    logger.info("STEP 8: Generating predictions for all employees...")

    # Predict on ALL employees (for display), but note which are train/test
    cox_medians = cox_predict_median(cph, X).values.flatten()
    rsf_medians = rsf_predict_median(rsf, X)

    # Weighted ensemble
    avg_medians = compute_weighted_ensemble_medians(cox_medians, rsf_medians, w_cox, w_rsf)

    # Data-driven risk thresholds (computed on TRAINING predictions only)
    train_avg_medians = compute_weighted_ensemble_medians(
        cox_predict_median(cph, X_train).values.flatten(),
        rsf_predict_median(rsf, X_train),
        w_cox, w_rsf
    )
    risk_thresholds = compute_risk_thresholds(train_avg_medians)
    result['risk_thresholds'] = risk_thresholds

    # Build predictions DataFrame
    predictions = employee_info.copy()
    predictions['cox_median_months'] = np.round(cox_medians, 1)
    predictions['rsf_median_months'] = np.round(rsf_medians, 1)
    predictions['avg_median_months'] = np.round(avg_medians, 1)
    predictions['resignation_cluster'] = [assign_resignation_cluster(m) for m in avg_medians]
    predictions['risk_category'] = [
        assign_risk_category_data_driven(m, risk_thresholds) for m in avg_medians
    ]

    # Compute continuous S_ens(t) survival curves and multi-horizon churn probabilities
    from models.prediction import compute_ensemble_survival_curves
    surv_df, churn_df, horizon_dict = compute_ensemble_survival_curves(cph, rsf, X, w_cox, w_rsf)
    predictions['prob_churn_30d'] = horizon_dict['prob_churn_30d']
    predictions['prob_churn_60d'] = horizon_dict['prob_churn_60d']
    predictions['prob_churn_90d'] = horizon_dict['prob_churn_90d']

    # Risk scores
    cox_risk = cox_predict_risk(cph, X).values.flatten()
    rsf_risk = rsf_predict_risk(rsf, X)
    predictions['cox_risk_score'] = np.round(cox_risk, 4)
    predictions['rsf_risk_score'] = np.round(rsf_risk, 4)

    # Mark train/test membership
    predictions['data_split'] = 'train'
    predictions.loc[predictions.index.isin(test_indices), 'data_split'] = 'test'

    # Model source for each prediction
    predictions['model_source'] = [
        determine_model_source(cm, rm, w_cox, w_rsf)
        for cm, rm in zip(cox_medians, rsf_medians)
    ]

    result['predictions'] = predictions
    result['survival_curves'] = surv_df
    result['churn_curves'] = churn_df


    # ================================================================
    # STEP 9: Build Model Comparison
    # ================================================================
    logger.info("STEP 9: Building model comparison...")

    model_comparison = {
        'cox_ph_c_index': cox_test_ci,  # Report TEST C-index as the main metric
        'rsf_c_index': rsf_test_ci,
        'cox_train_c_index': cox_train_ci,
        'rsf_train_c_index': rsf_train_ci,
        'cox_cv_mean': cox_cv['mean'],
        'cox_cv_std': cox_cv['std'],
        'rsf_cv_mean': rsf_cv['mean'],
        'rsf_cv_std': rsf_cv['std'],
        'cox_ibs': cox_test_ibs,
        'rsf_ibs': rsf_test_ibs,
        'cox_train_time': cox_train_time,
        'rsf_train_time': rsf_train_time,
        'winner': best_model,
        'margin': round(abs(cox_test_ci - rsf_test_ci), 4),
        'ensemble_weights': {'cox': w_cox, 'rsf': w_rsf},
        'interpretation': _build_interpretation(
            cox_test_ci, rsf_test_ci, cox_cv, rsf_cv, best_model
        )
    }
    result['model_comparison'] = model_comparison

    # ================================================================
    # DONE
    # ================================================================
    total_time = round(time.time() - pipeline_start, 2)
    result['total_time'] = total_time

    logger.info("=" * 60)
    logger.info(f"TRAINING PIPELINE COMPLETE in {total_time}s")
    logger.info(f"  Best Model: {best_model}")
    logger.info(f"  Test C-index: Cox={cox_test_ci}, RSF={rsf_test_ci}")
    logger.info(f"  CV C-index: Cox={cox_cv['mean']}±{cox_cv['std']}, "
                f"RSF={rsf_cv['mean']}±{rsf_cv['std']}")
    logger.info("=" * 60)

    return result


def _build_interpretation(cox_ci, rsf_ci, cox_cv, rsf_cv, best_model):
    """Build a human-readable interpretation of the model comparison."""
    best_ci = max(cox_ci, rsf_ci)
    parts = []

    parts.append(
        f"{best_model} achieves the best test C-index of {best_ci:.4f} "
        f"(margin: {abs(cox_ci - rsf_ci):.4f})."
    )

    if best_ci >= 0.8:
        parts.append("This indicates excellent discrimination ability.")
    elif best_ci >= 0.7:
        parts.append("This indicates good discrimination ability.")
    elif best_ci >= 0.6:
        parts.append("This indicates moderate discrimination. Consider more features.")
    else:
        parts.append("Discrimination is limited. The model may need more informative features.")

    # Check for overfitting
    cox_overfit = abs(cox_cv.get('mean', cox_ci) - cox_ci) if cox_cv else 0
    rsf_overfit = abs(rsf_cv.get('mean', rsf_ci) - rsf_ci) if rsf_cv else 0

    if cox_overfit > 0.05 or rsf_overfit > 0.05:
        parts.append(
            "Note: There is some gap between test and CV performance, "
            "suggesting mild overfitting."
        )
    else:
        parts.append("Test and CV performance are consistent, indicating stable generalization.")

    return " ".join(parts)
