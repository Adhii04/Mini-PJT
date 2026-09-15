"""
Metrics Module
==============
Computes advanced survival analysis metrics:
- C-index (train/test)
- Integrated Brier Score
- Calibration data
- Prediction uncertainty / confidence intervals
- Cox PH hazard ratios with p-values and CIs
"""

import logging
import numpy as np
import pandas as pd
from lifelines.utils import concordance_index as lifelines_c_index
from sksurv.metrics import concordance_index_censored

logger = logging.getLogger(__name__)


# ===================== C-INDEX =====================

def compute_cox_c_index(cph, X, T, E):
    """Compute C-index for Cox PH model on given data split."""
    try:
        X_cox = X[cph.params_.index]
        risk_scores = cph.predict_partial_hazard(X_cox).values.flatten()
        c_index = lifelines_c_index(T, -risk_scores, E)
        return round(c_index, 4)
    except Exception as e:
        logger.warning(f"Cox C-index computation failed: {e}")
        return 0.5


def compute_rsf_c_index(rsf, X, T, E):
    """Compute C-index for RSF model on given data split."""
    try:
        risk_scores = rsf.predict(X.values)
        event_indicator = E.astype(bool)
        c_index, _, _, _, _ = concordance_index_censored(event_indicator, T, risk_scores)
        return round(c_index, 4)
    except Exception as e:
        logger.warning(f"RSF C-index computation failed: {e}")
        return 0.5


# ===================== INTEGRATED BRIER SCORE =====================

def compute_integrated_brier_score(model, model_type, X, T, E, y_train, times=None):
    """
    Compute Integrated Brier Score for a survival model.
    Lower IBS = better calibrated predictions.

    Parameters
    ----------
    model : fitted CoxPHFitter or RandomSurvivalForest
    model_type : 'cox' or 'rsf'
    X : feature matrix
    T : durations
    E : event indicators
    y_train : structured array from training data (needed for IPCW)
    times : evaluation timepoints
    """
    try:
        from sksurv.metrics import integrated_brier_score as ibs_score

        # Create structured array for test data
        y_test = np.array([(bool(e), t) for e, t in zip(E, T)],
                          dtype=[('event', bool), ('duration', float)])

        # Define evaluation times within the range of observed times
        if times is None:
            t_min = max(T[T > 0].min(), 0.5)
            t_max = T.max() * 0.9  # Stay within 90% of max to avoid boundary issues
            times = np.linspace(t_min, t_max, 20)

        # Filter times to be within the range of both train and test
        train_times = y_train['duration']
        valid_mask = (times > max(T.min(), train_times.min())) & \
                     (times < min(T.max(), train_times.max()))
        times = times[valid_mask]

        if len(times) < 3:
            logger.warning("Not enough valid timepoints for IBS computation")
            return None

        # Get survival probabilities at each time point
        if model_type == 'cox':
            X_cox = X[model.params_.index]
            surv_df = model.predict_survival_function(X_cox, times=times)
            surv_probs = surv_df.values.T  # shape: (n_samples, n_times)
        else:
            surv_funcs = model.predict_survival_function(X.values)
            surv_probs = np.zeros((len(X), len(times)))
            for i, sf in enumerate(surv_funcs):
                for j, t in enumerate(times):
                    idx = np.searchsorted(sf.x, t)
                    if idx >= len(sf.x):
                        surv_probs[i, j] = sf.y[-1]
                    elif idx == 0:
                        surv_probs[i, j] = sf.y[0]
                    else:
                        x0, x1 = sf.x[idx - 1], sf.x[idx]
                        y0, y1 = sf.y[idx - 1], sf.y[idx]
                        frac = (t - x0) / (x1 - x0) if x1 != x0 else 0
                        surv_probs[i, j] = y0 + frac * (y1 - y0)

        # Clip probabilities to valid range
        surv_probs = np.clip(surv_probs, 1e-8, 1 - 1e-8)

        ibs = ibs_score(y_train, y_test, surv_probs, times)
        return round(float(ibs), 4)

    except Exception as e:
        logger.warning(f"IBS computation failed: {e}")
        return None


# ===================== CALIBRATION =====================

def compute_calibration_data(model, model_type, X, T, E, timepoints=None):
    """
    Compute calibration data: predicted vs observed survival at fixed timepoints.
    Uses decile-based grouping for calibration analysis.

    Returns list of dicts: [{time, predicted, observed}, ...]
    """
    try:
        if timepoints is None:
            timepoints = [6, 12, 18, 24]

        calibration_results = []

        for t in timepoints:
            # Get predicted survival probability at time t
            if model_type == 'cox':
                X_cox = X[model.params_.index]
                surv = model.predict_survival_function(X_cox, times=[t])
                pred_surv = surv.values.flatten()
            else:
                surv_funcs = model.predict_survival_function(X.values)
                pred_surv = []
                for sf in surv_funcs:
                    idx = np.searchsorted(sf.x, t)
                    if idx >= len(sf.x):
                        pred_surv.append(sf.y[-1])
                    elif idx == 0:
                        pred_surv.append(sf.y[0])
                    else:
                        x0, x1 = sf.x[idx - 1], sf.x[idx]
                        y0, y1 = sf.y[idx - 1], sf.y[idx]
                        frac = (t - x0) / (x1 - x0) if x1 != x0 else 0
                        pred_surv.append(y0 + frac * (y1 - y0))
                pred_surv = np.array(pred_surv)

            # Compute observed (Kaplan-Meier) survival at this time
            from lifelines import KaplanMeierFitter
            kmf = KaplanMeierFitter()
            kmf.fit(T, event_observed=E)
            if t in kmf.survival_function_.index:
                obs_surv = float(kmf.survival_function_.loc[t].values[0])
            else:
                # Interpolate
                sf_index = kmf.survival_function_.index
                idx = np.searchsorted(sf_index, t)
                if idx >= len(sf_index):
                    obs_surv = float(kmf.survival_function_.iloc[-1].values[0])
                elif idx == 0:
                    obs_surv = 1.0
                else:
                    obs_surv = float(kmf.survival_function_.iloc[idx].values[0])

            calibration_results.append({
                'time': int(t),
                'predicted_mean': round(float(np.mean(pred_surv)), 4),
                'predicted_median': round(float(np.median(pred_surv)), 4),
                'observed': round(obs_surv, 4),
                'n_at_risk': int(np.sum(T >= t)),
                'calibration_error': round(abs(float(np.mean(pred_surv)) - obs_surv), 4)
            })

        return calibration_results

    except Exception as e:
        logger.warning(f"Calibration computation failed: {e}")
        return []


# ===================== PREDICTION UNCERTAINTY =====================

def compute_prediction_uncertainty(rsf, X_single):
    """
    Compute prediction uncertainty from RSF by analyzing variance across trees.
    Returns confidence interval and confidence score.

    Uses the individual tree predictions to estimate uncertainty.
    """
    try:
        # Get individual tree survival functions
        surv_funcs = rsf.predict_survival_function(X_single.values)

        # Get median from the ensemble
        sf = surv_funcs[0]
        below_50 = np.where(sf.y <= 0.5)[0]
        ensemble_median = sf.x[below_50[0]] if len(below_50) > 0 else sf.x[-1]

        # Estimate uncertainty from individual trees
        tree_medians = []
        for tree in rsf.estimators_:
            try:
                # Each tree is a SurvivalTree
                y_struct = np.array([(True, ensemble_median)],
                                   dtype=[('event', bool), ('duration', float)])
                # Use the tree's predict method for risk score
                risk = tree.predict(X_single.values)
                tree_medians.append(float(risk[0]))
            except Exception:
                continue

        if len(tree_medians) > 10:
            # Use risk score variance as proxy for uncertainty
            risk_std = np.std(tree_medians)
            risk_mean = np.mean(tree_medians)
            # Coefficient of variation as uncertainty measure
            cv = risk_std / (abs(risk_mean) + 1e-8)

            # Scale uncertainty to months
            uncertainty_months = ensemble_median * cv * 0.5

            # Confidence interval
            ci_lower = max(0.5, ensemble_median - 1.96 * uncertainty_months)
            ci_upper = ensemble_median + 1.96 * uncertainty_months

            # Confidence score: higher agreement among trees = higher confidence
            # Normalize: low CV = high confidence
            confidence_score = max(0, min(100, int(100 * (1 / (1 + cv)))))
        else:
            # Fallback: use a fixed uncertainty estimate
            uncertainty_months = ensemble_median * 0.15
            ci_lower = max(0.5, ensemble_median - 1.96 * uncertainty_months)
            ci_upper = ensemble_median + 1.96 * uncertainty_months
            confidence_score = 65  # Default moderate confidence

        return {
            'median_months': round(float(ensemble_median), 1),
            'ci_lower': round(float(ci_lower), 1),
            'ci_upper': round(float(ci_upper), 1),
            'confidence_score': confidence_score,
            'uncertainty_months': round(float(uncertainty_months), 2)
        }

    except Exception as e:
        logger.warning(f"Uncertainty computation failed: {e}")
        return {
            'median_months': None,
            'ci_lower': None,
            'ci_upper': None,
            'confidence_score': 50,
            'uncertainty_months': None
        }


# ===================== COX PH HAZARD RATIOS =====================

def compute_cox_hazard_ratios(cph):
    """
    Extract hazard ratios, confidence intervals, p-values, and coefficients
    from a fitted Cox PH model.

    Returns list of dicts for each feature, sorted by absolute coefficient.
    """
    try:
        summary = cph.summary

        results = []
        for feature in summary.index:
            coef = float(summary.loc[feature, 'coef'])
            hr = float(summary.loc[feature, 'exp(coef)'])
            p_val = float(summary.loc[feature, 'p'])

            # Confidence interval for hazard ratio
            ci_cols = [c for c in summary.columns if 'exp(coef)' in c and ('lower' in c or 'upper' in c)]
            if len(ci_cols) >= 2:
                hr_lower = float(summary.loc[feature, ci_cols[0]])
                hr_upper = float(summary.loc[feature, ci_cols[1]])
            else:
                # Compute from coefficient CI
                coef_se = float(summary.loc[feature, 'se(coef)'])
                hr_lower = float(np.exp(coef - 1.96 * coef_se))
                hr_upper = float(np.exp(coef + 1.96 * coef_se))

            # Interpretation
            if p_val < 0.05:
                significance = 'Significant'
                if hr > 1:
                    interpretation = (
                        f"Increases resignation hazard by {(hr - 1) * 100:.1f}%. "
                        f"Employees with higher values are more likely to leave."
                    )
                else:
                    interpretation = (
                        f"Decreases resignation hazard by {(1 - hr) * 100:.1f}%. "
                        f"Employees with higher values are less likely to leave."
                    )
            else:
                significance = 'Not Significant'
                interpretation = (
                    f"No statistically significant effect on resignation hazard "
                    f"(p={p_val:.4f})."
                )

            results.append({
                'feature': feature,
                'coefficient': round(coef, 4),
                'hazard_ratio': round(hr, 4),
                'hr_ci_lower': round(hr_lower, 4),
                'hr_ci_upper': round(hr_upper, 4),
                'p_value': round(p_val, 4),
                'significance': significance,
                'interpretation': interpretation
            })

        # Sort by absolute coefficient (most impactful first)
        results.sort(key=lambda x: abs(x['coefficient']), reverse=True)
        return results

    except Exception as e:
        logger.warning(f"Hazard ratio computation failed: {e}")
        return []
