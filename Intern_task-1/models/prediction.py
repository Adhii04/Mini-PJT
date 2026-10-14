"""
Prediction Module
=================
Handles per-employee predictions with:
- Weighted ensemble (based on validation C-index)
- Confidence intervals
- Data-driven risk categories
- Model source attribution
"""

import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def compute_ensemble_weights(cox_test_ci, rsf_test_ci):
    """
    Compute ensemble weights proportional to test C-index.
    Better performing model gets higher weight.

    Returns (w_cox, w_rsf) normalized to sum to 1.
    """
    # Ensure minimum weight of 0.1 so neither model is fully ignored
    cox_w = max(cox_test_ci - 0.5, 0.01)  # Subtract 0.5 (random baseline)
    rsf_w = max(rsf_test_ci - 0.5, 0.01)

    total = cox_w + rsf_w
    w_cox = round(cox_w / total, 4)
    w_rsf = round(rsf_w / total, 4)

    logger.info(f"Ensemble weights: Cox={w_cox:.4f}, RSF={w_rsf:.4f} "
                f"(based on test C-index: Cox={cox_test_ci}, RSF={rsf_test_ci})")

    return w_cox, w_rsf


def compute_weighted_ensemble_medians(cox_medians, rsf_medians, w_cox, w_rsf):
    """
    Compute weighted ensemble median predictions.
    Handles inf values from Cox PH gracefully.
    """
    # Replace inf in Cox medians with RSF value
    cox_clean = np.where(np.isinf(cox_medians), rsf_medians, cox_medians)

    ensemble = w_cox * cox_clean + w_rsf * rsf_medians

    # Final inf/nan cleanup
    ensemble = np.where(np.isinf(ensemble) | np.isnan(ensemble), rsf_medians, ensemble)
    ensemble = np.where(np.isinf(ensemble) | np.isnan(ensemble), 60, ensemble)

    return ensemble


def compute_risk_thresholds(predicted_medians):
    """
    Compute data-driven risk category thresholds using percentiles
    of the predicted median survival distribution.

    Returns dict with threshold values and method documentation.
    """
    # Use quartiles of the prediction distribution
    p25 = float(np.percentile(predicted_medians, 25))
    p50 = float(np.percentile(predicted_medians, 50))
    p75 = float(np.percentile(predicted_medians, 75))

    thresholds = {
        'critical_upper': round(p25, 1),
        'high_upper': round(p50, 1),
        'medium_upper': round(p75, 1),
        'method': 'percentile_based',
        'description': (
            f"Risk categories derived from quartiles of predicted median survival: "
            f"Critical ≤ P25 ({p25:.1f} mo), "
            f"High = P25–P50 ({p25:.1f}–{p50:.1f} mo), "
            f"Medium = P50–P75 ({p50:.1f}–{p75:.1f} mo), "
            f"Low > P75 ({p75:.1f} mo)"
        ),
        'percentiles': {
            'p25': round(p25, 1),
            'p50': round(p50, 1),
            'p75': round(p75, 1)
        }
    }

    logger.info(f"Data-driven risk thresholds: Critical≤{p25:.1f}, "
                f"High≤{p50:.1f}, Medium≤{p75:.1f}, Low>{p75:.1f}")

    return thresholds


def assign_risk_category_data_driven(median_months, thresholds):
    """Assign risk category using data-driven percentile thresholds."""
    if median_months <= thresholds['critical_upper']:
        return 'Critical'
    elif median_months <= thresholds['high_upper']:
        return 'High'
    elif median_months <= thresholds['medium_upper']:
        return 'Medium'
    else:
        return 'Low'


def assign_resignation_cluster(median_months):
    """Assign resignation window cluster based on predicted median survival."""
    if median_months <= 2:
        return '0–2 months'
    elif median_months <= 4:
        return '2–4 months'
    elif median_months <= 6:
        return '4–6 months'
    elif median_months <= 8:
        return '6–8 months'
    elif median_months <= 12:
        return '8–12 months'
    else:
        return '12+ months'


def determine_model_source(cox_median, rsf_median, w_cox, w_rsf):
    """
    Determine which model primarily drove the prediction.
    Returns 'Cox PH', 'Random Survival Forest', or 'Weighted Ensemble'.
    """
    if np.isinf(cox_median):
        return 'Random Survival Forest'
    elif w_cox > 0.65:
        return 'Cox PH (primary)'
    elif w_rsf > 0.65:
        return 'Random Survival Forest (primary)'
    else:
        return 'Weighted Ensemble'


def compute_ensemble_survival_curves(cph, rsf, X, w_cox, w_rsf, times=[1, 2, 3, 6, 12, 18, 24, 36, 48, 60]):
    """
    Compute multi-horizon ensemble survival probabilities S_ens(t) and churn probabilities P_churn(t) = 1 - S_ens(t).
    Also computes continuous Restricted Mean Survival Time (RMST) for expected remaining tenure.
    
    Returns:
    - surv_df: DataFrame (employees x times) containing survival probabilities
    - churn_df: DataFrame (employees x times) containing churn probabilities
    - horizon_dict: Dict of key horizon probabilities per employee (e.g. 30d, 60d, 90d) and expected tenure
    """
    # 1. Cox PH survival predictions
    try:
        X_cox = pd.DataFrame(0.0, index=X.index, columns=cph.params_.index)
        for c in cph.params_.index:
            if c in X.columns:
                X_cox[c] = X[c]
        cox_surv = cph.predict_survival_function(X_cox, times=times).T  # Transpose to shape (n_samples, n_times)
        cox_surv.columns = times
    except Exception as e:
        logger.warning(f"Cox PH survival prediction warning: {e}")
        cox_surv = pd.DataFrame(1.0, index=X.index, columns=times)

    # 2. RSF survival predictions
    try:
        rsf_surv_fn = rsf.predict_survival_function(X.values)
        rsf_surv_list = []
        for fn in rsf_surv_fn:
            # Interpolate or evaluate at requested times
            s_vals = [float(fn(t)) for t in times]
            rsf_surv_list.append(s_vals)
        rsf_surv = pd.DataFrame(rsf_surv_list, index=X.index, columns=times)
    except Exception as e:
        logger.warning(f"RSF survival prediction warning: {e}")
        rsf_surv = pd.DataFrame(1.0, index=X.index, columns=times)

    # 3. Weighted ensemble survival curves: S_ens = w_cox * S_cox + w_rsf * S_rsf
    surv_df = w_cox * cox_surv + w_rsf * rsf_surv
    surv_df = surv_df.clip(lower=0.0, upper=1.0)

    # 4. Cumulative churn probabilities: P(churn | t) = 1 - S(t)
    churn_df = 1.0 - surv_df

    # Extract specific 30d (1 mo), 60d (2 mo), and 90d (3 mo) horizon probabilities
    prob_30d = churn_df[1].values if 1 in churn_df.columns else churn_df.iloc[:, 0].values
    prob_60d = churn_df[2].values if 2 in churn_df.columns else churn_df.iloc[:, 1].values
    prob_90d = churn_df[3].values if 3 in churn_df.columns else churn_df.iloc[:, 2].values

    # Continuous Expected Remaining Tenure: Area under survival curve up to 60 months
    t_points = np.array([0.0] + list(times))
    expected_tenure_list = []
    cox_expected_list = []
    rsf_expected_list = []

    # Helper for trapezoidal integration across numpy 1.x and 2.0+
    def _safe_trapezoid(y_vals, x_vals):
        if hasattr(np, 'trapezoid'):
            return np.trapezoid(y_vals, x_vals)
        elif hasattr(np, 'trapz'):
            return np.trapz(y_vals, x_vals)
        else:
            try:
                from scipy.integrate import trapezoid
                return trapezoid(y_vals, x_vals)
            except ImportError:
                # Basic manual trapezoidal rule fallback
                dx = np.diff(x_vals)
                return np.sum(dx * (y_vals[:-1] + y_vals[1:]) / 2.0)

    for i in range(len(surv_df)):
        s_ens = np.array([1.0] + list(surv_df.iloc[i].values))
        s_cox = np.array([1.0] + list(cox_surv.iloc[i].values))
        s_rsf = np.array([1.0] + list(rsf_surv.iloc[i].values))
        
        expected_tenure_list.append(round(float(_safe_trapezoid(s_ens, t_points)), 1))
        cox_expected_list.append(round(float(_safe_trapezoid(s_cox, t_points)), 1))
        rsf_expected_list.append(round(float(_safe_trapezoid(s_rsf, t_points)), 1))

    horizon_dict = {
        'prob_churn_30d': np.round(prob_30d, 4),
        'prob_churn_60d': np.round(prob_60d, 4),
        'prob_churn_90d': np.round(prob_90d, 4),
        'expected_tenure': np.array(expected_tenure_list),
        'cox_expected_tenure': np.array(cox_expected_list),
        'rsf_expected_tenure': np.array(rsf_expected_list)
    }

    return surv_df, churn_df, horizon_dict

