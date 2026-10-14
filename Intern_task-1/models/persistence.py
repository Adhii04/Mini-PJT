"""
Model Persistence Module
========================
Save and load trained models, scalers, feature names, and evaluation results.
Uses joblib for efficient serialization.
"""

import logging
import os
import json
import joblib
import numpy as np

logger = logging.getLogger(__name__)


def save_models(train_result, scaler, feature_names, output_dir='outputs/saved_models'):
    """
    Save all trained model artifacts to disk.

    Saves:
    - Cox PH model (via joblib)
    - RSF model (via joblib)
    - Scaler (via joblib)
    - Feature names (JSON)
    - Evaluation metrics (JSON)
    - Risk thresholds (JSON)
    - Ensemble weights (JSON)
    - Cross-validation results (JSON)
    """
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Save models
        joblib.dump(train_result['cph'], os.path.join(output_dir, 'cox_ph_model.pkl'))
        logger.info("  Saved Cox PH model")

        joblib.dump(train_result['rsf'], os.path.join(output_dir, 'rsf_model.pkl'))
        logger.info("  Saved RSF model")

        # Save scaler
        joblib.dump(scaler, os.path.join(output_dir, 'scaler.pkl'))
        logger.info("  Saved scaler")

        # Save feature names
        with open(os.path.join(output_dir, 'feature_names.json'), 'w') as f:
            json.dump(list(feature_names), f, indent=2)
        logger.info("  Saved feature names")

        # Save metrics (serializable subset)
        metrics_dict = dict(train_result['metrics'])
        if 'baseline_stats' in train_result:
            metrics_dict['baseline_stats'] = train_result['baseline_stats']
        if 'model_comparison' in train_result and 'classification_metrics' in train_result['model_comparison']:
            metrics_dict['classification_metrics'] = train_result['model_comparison']['classification_metrics']
        if 'roc_curve_plot' in train_result and train_result['roc_curve_plot']:
            metrics_dict['roc_curve_plot'] = train_result['roc_curve_plot']
        if 'confusion_matrices_plot' in train_result and train_result['confusion_matrices_plot']:
            metrics_dict['confusion_matrices_plot'] = train_result['confusion_matrices_plot']
        metrics_serializable = _make_serializable(metrics_dict)
        with open(os.path.join(output_dir, 'evaluation_metrics.json'), 'w') as f:
            json.dump(metrics_serializable, f, indent=2, default=str)
        logger.info("  Saved evaluation metrics")

        # Save risk thresholds
        with open(os.path.join(output_dir, 'risk_thresholds.json'), 'w') as f:
            json.dump(train_result['risk_thresholds'], f, indent=2)
        logger.info("  Saved risk thresholds")

        # Save ensemble weights
        with open(os.path.join(output_dir, 'ensemble_weights.json'), 'w') as f:
            json.dump(train_result['ensemble_weights'], f, indent=2)
        logger.info("  Saved ensemble weights")

        # Save cross-validation results
        cv_data = _make_serializable(train_result['cross_validation'])
        with open(os.path.join(output_dir, 'cv_results.json'), 'w') as f:
            json.dump(cv_data, f, indent=2, default=str)
        logger.info("  Saved cross-validation results")

        # Save RSF best params
        with open(os.path.join(output_dir, 'rsf_best_params.json'), 'w') as f:
            json.dump(train_result['rsf_params'], f, indent=2, default=str)
        logger.info("  Saved RSF best params")

        logger.info(f"All models saved to {output_dir}")
        return True

    except Exception as e:
        logger.error(f"Failed to save models: {e}")
        return False


def load_models(output_dir='outputs/saved_models'):
    """
    Load all trained model artifacts from disk.
    Returns dict with loaded artifacts or None if loading fails.
    """
    try:
        if not os.path.exists(output_dir):
            logger.warning(f"Model directory not found: {output_dir}")
            return None

        result = {}

        result['cph'] = joblib.load(os.path.join(output_dir, 'cox_ph_model.pkl'))
        result['rsf'] = joblib.load(os.path.join(output_dir, 'rsf_model.pkl'))
        result['scaler'] = joblib.load(os.path.join(output_dir, 'scaler.pkl'))

        with open(os.path.join(output_dir, 'feature_names.json'), 'r') as f:
            result['feature_names'] = json.load(f)

        with open(os.path.join(output_dir, 'evaluation_metrics.json'), 'r') as f:
            result['metrics'] = json.load(f)

        with open(os.path.join(output_dir, 'risk_thresholds.json'), 'r') as f:
            result['risk_thresholds'] = json.load(f)

        with open(os.path.join(output_dir, 'ensemble_weights.json'), 'r') as f:
            result['ensemble_weights'] = json.load(f)

        with open(os.path.join(output_dir, 'cv_results.json'), 'r') as f:
            result['cv_results'] = json.load(f)

        logger.info(f"All models loaded from {output_dir}")
        return result

    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        return None


def _make_serializable(obj):
    """Recursively convert numpy types to Python native types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_make_serializable(item) for item in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    else:
        return obj
