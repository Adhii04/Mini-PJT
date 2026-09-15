"""
Validation Module
=================
Implements cross-validation for survival analysis models.
- Stratified K-Fold CV for Cox PH and RSF
- Returns per-fold scores, mean, std
"""

import logging
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from lifelines import CoxPHFitter
from sksurv.ensemble import RandomSurvivalForest
from lifelines.utils import concordance_index as lifelines_c_index
from sksurv.metrics import concordance_index_censored

logger = logging.getLogger(__name__)


def cross_validate_cox(X, T, E, n_folds=5, penalizer=0.001):
    """
    Perform K-Fold cross-validation for Cox PH model.

    Parameters
    ----------
    X : pd.DataFrame — standardized feature matrix
    T : np.ndarray — durations
    E : np.ndarray — event indicators
    n_folds : int — number of CV folds
    penalizer : float — Cox PH regularization

    Returns
    -------
    dict with 'fold_scores', 'mean', 'std'
    """
    logger.info(f"Starting {n_folds}-fold CV for Cox PH...")

    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
    fold_scores = []

    for fold_idx, (train_idx, val_idx) in enumerate(skf.split(X, E)):
        try:
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            T_train, T_val = T[train_idx], T[val_idx]
            E_train, E_val = E[train_idx], E[val_idx]

            # Build Cox dataframe
            df_cox = X_train.copy()
            for col in list(df_cox.columns):
                if df_cox[col].nunique() <= 1:
                    df_cox = df_cox.drop(columns=[col])
                    X_val_filtered = X_val.drop(columns=[col], errors='ignore')
                else:
                    X_val_filtered = X_val

            df_cox['duration'] = T_train
            df_cox['event'] = E_train
            df_cox = df_cox[df_cox['duration'] > 0]

            cph = CoxPHFitter(penalizer=penalizer)
            cph.fit(df_cox, duration_col='duration', event_col='event')

            # Evaluate on validation fold
            common_cols = [c for c in cph.params_.index if c in X_val.columns]
            X_val_cox = X_val[common_cols]
            risk_scores = cph.predict_partial_hazard(X_val_cox).values.flatten()
            c_idx = lifelines_c_index(T_val, -risk_scores, E_val)
            fold_scores.append(round(c_idx, 4))

            logger.info(f"  Cox PH Fold {fold_idx + 1}: C-index = {c_idx:.4f}")

        except Exception as e:
            logger.warning(f"  Cox PH Fold {fold_idx + 1} failed: {e}")
            fold_scores.append(None)

    valid_scores = [s for s in fold_scores if s is not None]
    mean_score = round(float(np.mean(valid_scores)), 4) if valid_scores else 0.5
    std_score = round(float(np.std(valid_scores)), 4) if valid_scores else 0.0

    logger.info(f"Cox PH CV complete: {mean_score:.4f} ± {std_score:.4f}")

    return {
        'fold_scores': fold_scores,
        'mean': mean_score,
        'std': std_score,
        'n_folds': n_folds
    }


def cross_validate_rsf(X, T, E, n_folds=5, rsf_params=None):
    """
    Perform K-Fold cross-validation for Random Survival Forest.

    Parameters
    ----------
    X : pd.DataFrame — standardized feature matrix
    T : np.ndarray — durations
    E : np.ndarray — event indicators
    n_folds : int — number of CV folds
    rsf_params : dict — RSF hyperparameters

    Returns
    -------
    dict with 'fold_scores', 'mean', 'std'
    """
    logger.info(f"Starting {n_folds}-fold CV for RSF...")

    if rsf_params is None:
        rsf_params = {
            'n_estimators': 200,
            'min_samples_split': 6,
            'min_samples_leaf': 3,
            'max_features': 'sqrt',
            'max_depth': None,
            'n_jobs': -1,
            'random_state': 42
        }

    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
    fold_scores = []

    for fold_idx, (train_idx, val_idx) in enumerate(skf.split(X, E)):
        try:
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            T_train, T_val = T[train_idx], T[val_idx]
            E_train, E_val = E[train_idx], E[val_idx]

            # Create structured array
            y_train = np.array([(bool(e), t) for e, t in zip(E_train, T_train)],
                               dtype=[('event', bool), ('duration', float)])

            rsf = RandomSurvivalForest(**rsf_params)
            rsf.fit(X_train.values, y_train)

            # Evaluate on validation fold
            risk_scores = rsf.predict(X_val.values)
            event_indicator = E_val.astype(bool)
            c_idx, _, _, _, _ = concordance_index_censored(event_indicator, T_val, risk_scores)
            fold_scores.append(round(c_idx, 4))

            logger.info(f"  RSF Fold {fold_idx + 1}: C-index = {c_idx:.4f}")

        except Exception as e:
            logger.warning(f"  RSF Fold {fold_idx + 1} failed: {e}")
            fold_scores.append(None)

    valid_scores = [s for s in fold_scores if s is not None]
    mean_score = round(float(np.mean(valid_scores)), 4) if valid_scores else 0.5
    std_score = round(float(np.std(valid_scores)), 4) if valid_scores else 0.0

    logger.info(f"RSF CV complete: {mean_score:.4f} ± {std_score:.4f}")

    return {
        'fold_scores': fold_scores,
        'mean': mean_score,
        'std': std_score,
        'n_folds': n_folds
    }
