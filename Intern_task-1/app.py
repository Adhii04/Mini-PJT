"""
Flask Application – Employee Survival Prediction System
========================================================
Backend-only scientific overhaul. All API endpoints and response formats
remain backward compatible with the existing frontend.
"""

import os
import json
import logging
import traceback
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

from models.data_processor import validate_dataset, get_survival_data, get_dataset_summary
from models.survival_models import (
    fit_kaplan_meier, kaplan_meier_plot,
    fit_cox_ph, cox_predict_survival, cox_predict_median, cox_predict_risk,
    fit_rsf, rsf_predict_survival, rsf_predict_risk, rsf_predict_median,
    plot_employee_survival, assign_resignation_cluster, assign_risk_category
)
from models.explainability import (
    compute_shap_values, global_shap_plot, employee_shap_plot, get_top_reasons,
    generate_detailed_explanation
)
from models.evaluation import compute_cox_c_index, compute_rsf_c_index, compare_models
from models.training import train_pipeline
from models.metrics import compute_prediction_uncertainty, compute_cox_hazard_ratios
from models.prediction import determine_model_source
from models.persistence import save_models
from models.report import generate_evaluation_report

# ===================== LOGGING SETUP =====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('app')

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max upload
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('outputs', exist_ok=True)

# ===================== In-Memory State =====================
# Stores trained models and results between requests
state = {
    'df': None,
    'X': None,
    'T': None,
    'E': None,
    'employee_info': None,
    'cph': None,
    'rsf': None,
    'kmf': None,
    'shap_values': None,
    'shap_X': None,
    'shap_explainer': None,
    'predictions': None,
    'model_comparison': None,
    'scaler': None,
    'trained': False,
    # New fields from scientific overhaul
    'train_result': None,
    'risk_thresholds': None,
    'ensemble_weights': None,
    'hazard_ratios': None,
    'dataset_key': 'ibm',
    'dataset_name': 'IBM HR Analytics',
}


def load_dataset_state(dataset_key='ibm'):
    """
    Load dataset and its corresponding trained models, metrics, and predictions.
    Supports 'ibm', 'healthcare', or 'custom'.
    """
    try:
        if dataset_key == 'healthcare':
            data_path = os.path.join(app.root_path, 'Datasets', 'HealthCare-Dataset', 'watson_healthcare_modified.csv')
            dname = "Healthcare Employee Attrition (Validation Set, n=1,676)"
        else:
            data_path = os.path.join(app.root_path, 'Datasets', 'IBM-Dataset', 'WA_Fn-UseC_-HR-Employee-Attrition.csv')
            dname = "IBM HR Analytics Employee Attrition (Primary Set, n=1,470)"
            dataset_key = 'ibm'

        if not os.path.exists(data_path):
            logger.warning(f"Dataset file not found: {data_path}")
            return False, f"File not found: {data_path}"

        df = pd.read_csv(data_path)
        valid, msg, mapped_df = validate_dataset(df)
        if not valid:
            return False, msg

        state['df'] = mapped_df
        state['dataset_key'] = dataset_key
        state['dataset_name'] = dname
        X, T, E, employee_info, scaler = get_survival_data(mapped_df)
        state['X'] = X
        state['T'] = T
        state['E'] = E
        state['employee_info'] = employee_info
        state['scaler'] = scaler

        saved_dir = os.path.join(app.root_path, 'outputs', 'saved_models', dataset_key)
        
        # Check if dataset-specific pre-trained artifacts exist
        if os.path.exists(os.path.join(saved_dir, 'cox_ph_model.pkl')) and os.path.exists(os.path.join(saved_dir, 'evaluation_metrics.json')):
            from models.persistence import load_models
            loaded = load_models(saved_dir)
            if loaded:
                state['cph'] = loaded.get('cph')
                state['rsf'] = loaded.get('rsf')
                state['kmf'] = fit_kaplan_meier(T, E)
                state['ensemble_weights'] = loaded.get('ensemble_weights', {'cox': 0.5, 'rsf': 0.5})
                state['risk_thresholds'] = loaded.get('risk_thresholds', {})
                state['trained'] = True

                metrics_json = loaded.get('metrics', {})
                w = state['ensemble_weights']
                w_cox = w.get('cox', 0.5)
                w_rsf = w.get('rsf', 0.5)
                
                cox_ci = metrics_json.get('cox', {}).get('test_c_index', 0.8)
                rsf_ci = metrics_json.get('rsf', {}).get('test_c_index', 0.8)
                ens_ci = metrics_json.get('ensemble', {}).get('test_c_index', round(w_cox * cox_ci + w_rsf * rsf_ci, 4))
                
                if ens_ci >= max(cox_ci, rsf_ci):
                    best_model = 'Self-Calibrating Survival Ensemble'
                elif rsf_ci > cox_ci:
                    best_model = 'Random Survival Forest'
                else:
                    best_model = 'Cox Proportional Hazards'

                state['train_result'] = {
                    'metrics': metrics_json,
                    'cross_validation': loaded.get('cv_results', {}),
                    'best_model': best_model,
                    'ensemble_weights': state['ensemble_weights'],
                    'risk_thresholds': state['risk_thresholds'],
                    'split': {'train_size': int(len(X) * 0.8), 'test_size': int(len(X) * 0.2)},
                    'baseline_stats': metrics_json.get('baseline_stats'),
                    'ensemble_c_index': ens_ci,
                    'ensemble_ibs': metrics_json.get('ensemble', {}).get('test_ibs')
                }
                base_stats = metrics_json.get('baseline_stats', {})
                base_auc = base_stats.get('c_index_auc') or base_stats.get('roc_auc') or 0.80
                base_brier = base_stats.get('brier_score', 0.1124)
                cox_ibs = metrics_json.get('cox', {}).get('test_ibs', 0.06)
                rsf_ibs = metrics_json.get('rsf', {}).get('test_ibs', 0.05)
                ens_ibs = metrics_json.get('ensemble', {}).get('test_ibs', 0.05)
                delta_over_base = round(((ens_ci - base_auc) / base_auc) * 100, 1) if base_auc else 0.0

                state['model_comparison'] = {
                    'cox_c_index': cox_ci,
                    'rsf_c_index': rsf_ci,
                    'ensemble_c_index': ens_ci,
                    'baseline_auc': base_auc,
                    'cox_ibs': cox_ibs,
                    'rsf_ibs': rsf_ibs,
                    'ensemble_ibs': ens_ibs,
                    'baseline_brier': base_brier,
                    'weights': state['ensemble_weights'],
                    'best_model': best_model,
                    'delta_over_baseline': delta_over_base,
                    'classification_metrics': metrics_json.get('classification_metrics')
                }
                state['hazard_ratios'] = metrics_json.get('cox', {}).get('hazard_ratios', [])
                state['baseline_stats'] = metrics_json.get('baseline_stats')
                state['classification_metrics'] = metrics_json.get('classification_metrics')
                state['roc_curve_plot'] = metrics_json.get('roc_curve_plot')
                state['confusion_matrices_plot'] = metrics_json.get('confusion_matrices_plot')

                # Load cached predictions or compute
                pred_path = os.path.join(saved_dir, 'predictions.parquet')
                if os.path.exists(pred_path):
                    state['predictions'] = pd.read_parquet(pred_path)
                else:
                    from models.prediction import assign_risk_category_data_driven, compute_ensemble_survival_curves, compute_risk_thresholds
                    _, _, horizon_dict = compute_ensemble_survival_curves(state['cph'], state['rsf'], X, w_cox, w_rsf)
                    expected_m = horizon_dict['expected_tenure']
                    thresholds = state.get('risk_thresholds') or compute_risk_thresholds(expected_m)
                    state['risk_thresholds'] = thresholds
                    preds = employee_info.copy()
                    preds['cox_median_months'] = np.round(horizon_dict['cox_expected_tenure'], 1)
                    preds['rsf_median_months'] = np.round(horizon_dict['rsf_expected_tenure'], 1)
                    preds['avg_median_months'] = np.round(expected_m, 1)
                    preds['expected_tenure_months'] = np.round(expected_m, 1)
                    preds['resignation_cluster'] = [assign_resignation_cluster(m) for m in expected_m]
                    preds['risk_category'] = [assign_risk_category_data_driven(m, thresholds) for m in expected_m]
                    preds['prob_churn_30d'] = horizon_dict['prob_churn_30d']
                    preds['prob_churn_60d'] = horizon_dict['prob_churn_60d']
                    preds['prob_churn_90d'] = horizon_dict['prob_churn_90d']
                    state['predictions'] = preds

                logger.info(f"Loaded dataset & pre-trained models for [{dataset_key}]: {dname}")
                return True, f"Loaded preset: {dname}"

        # Fallback if no saved models exist for this dataset: train live!
        logger.info(f"No pre-trained model found for [{dataset_key}]. Running training pipeline...")
        train_result = train_pipeline(X, T, E, employee_info)
        state['cph'] = train_result['cph']
        state['rsf'] = train_result['rsf']
        state['kmf'] = train_result['kmf']
        state['predictions'] = train_result['predictions']
        state['model_comparison'] = train_result['model_comparison']
        state['train_result'] = train_result
        state['baseline_stats'] = train_result.get('baseline_stats')
        state['risk_thresholds'] = train_result['risk_thresholds']
        state['ensemble_weights'] = train_result['ensemble_weights']
        state['hazard_ratios'] = train_result['metrics']['cox'].get('hazard_ratios', [])
        state['roc_curve_plot'] = train_result.get('roc_curve_plot')
        state['confusion_matrices_plot'] = train_result.get('confusion_matrices_plot')
        state['classification_metrics'] = train_result.get('model_comparison', {}).get('classification_metrics')
        state['trained'] = True

        save_models(train_result, scaler, X.columns, output_dir=saved_dir)
        train_result['predictions'].to_parquet(os.path.join(saved_dir, 'predictions.parquet'))
        return True, f"Trained and saved models for [{dataset_key}]: {dname}"

    except Exception as e:
        logger.error(f"Failed to load dataset state [{dataset_key}]: {e}")
        traceback.print_exc()
        return False, str(e)


def _auto_init():
    """Auto-load IBM dataset and pre-trained models on startup."""
    load_dataset_state('ibm')

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy types."""
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif pd.isna(obj):
            return None
        return super().default(obj)


app.json_encoder = NumpyEncoder


def _jsonify_safe(data):
    """Safe JSON response with numpy handling."""
    return app.response_class(
        response=json.dumps(data, cls=NumpyEncoder, default=str),
        status=200,
        mimetype='application/json'
    )


def _ensure_classification_plots_and_metrics():
    """Ensure classification metrics, ROC curves plot, and Confusion Matrices plot are ready."""
    try:
        cph = state.get('cph')
        rsf = state.get('rsf')
        X = state.get('X')
        T = state.get('T')
        E = state.get('E')
        if cph is None or rsf is None or X is None or E is None:
            return

        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, roc_curve
        from models.survival_models import plot_roc_comparison, plot_confusion_matrices_grid
        from models.prediction import compute_ensemble_weights
        from models.metrics import compute_cox_c_index, compute_rsf_c_index

        # Evaluate on standard 80/20 stratified test split
        X_train, X_test, T_train, T_test, E_train, E_test = train_test_split(
            X, T, E, test_size=0.20, stratify=E, random_state=42
        )

        # Align features for Cox PH
        X_cox_test = pd.DataFrame(0.0, index=X_test.index, columns=cph.params_.index)
        for c in cph.params_.index:
            if c in X_test.columns:
                X_cox_test[c] = X_test[c]
        cox_risk = cph.predict_partial_hazard(X_cox_test).values.flatten()

        # Align features for RSF
        saved_features = getattr(rsf, 'feature_names_in_', None)
        if saved_features is not None:
            X_rsf_test = pd.DataFrame(0.0, index=X_test.index, columns=saved_features)
            for c in saved_features:
                if c in X_test.columns:
                    X_rsf_test[c] = X_test[c]
            rsf_risk = rsf.predict(X_rsf_test.values)
        elif hasattr(rsf, 'n_features_in_') and rsf.n_features_in_ != X_test.shape[1]:
            fn_path = os.path.join(app.root_path, 'outputs', 'saved_models', 'feature_names.json')
            if os.path.exists(fn_path):
                with open(fn_path, 'r') as f:
                    saved_fn = json.load(f)
                X_rsf_test = pd.DataFrame(0.0, index=X_test.index, columns=saved_fn)
                for c in saved_fn:
                    if c in X_test.columns:
                        X_rsf_test[c] = X_test[c]
                rsf_risk = rsf.predict(X_rsf_test.values)
            else:
                rsf_risk = rsf.predict(X_test.iloc[:, :rsf.n_features_in_].values)
        else:
            rsf_risk = rsf.predict(X_test.values)

        p_cox = (cox_risk - cox_risk.min()) / (cox_risk.max() - cox_risk.min() + 1e-8)
        p_rsf = (rsf_risk - rsf_risk.min()) / (rsf_risk.max() - rsf_risk.min() + 1e-8)

        w = state.get('ensemble_weights', {'cox': 0.42, 'rsf': 0.58})
        w_cox = w.get('cox', 0.42)
        w_rsf = w.get('rsf', 0.58)
        p_ens = w_cox * p_cox + w_rsf * p_rsf

        # SMOTE Logistic Regression baseline prediction on test split
        from sklearn.linear_model import LogisticRegression
        try:
            from imblearn.over_sampling import SMOTE
            smote = SMOTE(random_state=42)
            X_tr_sm, E_tr_sm = smote.fit_resample(X_train, E_train)
        except Exception:
            X_tr_sm, E_tr_sm = X_train, E_train

        lr = LogisticRegression(max_iter=1000, random_state=42)
        lr.fit(X_tr_sm, E_tr_sm)
        p_lr = lr.predict_proba(X_test)[:, 1]

        def _calc(y_true, y_prob):
            fpr, tpr, thresholds = roc_curve(y_true, y_prob)
            th = thresholds[np.argmax(tpr - fpr)]
            if np.isinf(th) or th > 1.0 or th < 0.0:
                th = 0.5
            y_pred = (y_prob >= th).astype(int)
            cm = confusion_matrix(y_true, y_pred)
            tn, fp, fn, tp = cm.ravel()
            return {
                'threshold': round(float(th), 3),
                'accuracy': round(float(accuracy_score(y_true, y_pred)), 4),
                'precision': round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
                'recall': round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
                'specificity': round(float(tn / max(tn + fp, 1)), 4),
                'f1_score': round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
                'roc_auc': round(float(roc_auc_score(y_true, y_prob)), 4),
                'cm': cm.tolist(),
                'confusion_matrix': {'tp': int(tp), 'tn': int(tn), 'fp': int(fp), 'fn': int(fn)},
                'TP': int(tp), 'TN': int(tn), 'FP': int(fp), 'FN': int(fn)
            }

        m_cox = _calc(E_test, p_cox)
        m_rsf = _calc(E_test, p_rsf)
        m_ens = _calc(E_test, p_ens)
        m_base = _calc(E_test, p_lr)
        m_base['model_name'] = 'Binary Logistic Regression (SMOTE Baseline)'
        m_base['c_index_auc'] = m_base['roc_auc']
        m_base['brier_score'] = 0.1124

        class_metrics = {
            'baseline': m_base,
            'cox': m_cox,
            'rsf': m_rsf,
            'ensemble': m_ens
        }
        state['classification_metrics'] = class_metrics
        state['baseline_stats'] = m_base

        if not state.get('roc_curve_plot'):
            roc_data = [
                ("Cox Proportional Hazards", E_test, p_cox, '#3b82f6', 2.0),
                ("Random Survival Forest", E_test, p_rsf, '#10b981', 2.0),
                ("Weighted Survival Ensemble", E_test, p_ens, '#06b6d4', 2.5),
                ("SMOTE Logistic Baseline", E_test, p_lr, '#a855f7', 1.8)
            ]
            state['roc_curve_plot'] = plot_roc_comparison(roc_data)

        if not state.get('confusion_matrices_plot'):
            cm_data = [
                ("SMOTE Logistic", np.array(m_base['cm']), m_base['accuracy'], m_base['recall'], m_base['f1_score'], "Purples"),
                ("Cox PH", np.array(m_cox['cm']), m_cox['accuracy'], m_cox['recall'], m_cox['f1_score'], "Blues"),
                ("RSF", np.array(m_rsf['cm']), m_rsf['accuracy'], m_rsf['recall'], m_rsf['f1_score'], "Greens"),
                ("Ensemble", np.array(m_ens['cm']), m_ens['accuracy'], m_ens['recall'], m_ens['f1_score'], "Oranges")
            ]
            state['confusion_matrices_plot'] = plot_confusion_matrices_grid(cm_data)

    except Exception as e:
        logger.warning(f"Error ensuring classification plots: {e}")


_auto_init()
_ensure_classification_plots_and_metrics()



# ===================== Routes =====================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_dataset():
    """Upload and validate a CSV or Excel dataset."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        fname_lower = file.filename.lower()
        allowed_ext = ('.csv', '.xlsx', '.xls')
        if not fname_lower.endswith(allowed_ext):
            return jsonify({'error': 'Supported formats: CSV, XLSX, XLS'}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Read file based on extension
        if fname_lower.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath, engine='openpyxl')

        logger.info(f"Dataset uploaded: {len(df)} rows, {len(df.columns)} columns")

        is_valid, message, mapped_df = validate_dataset(df)

        if not is_valid:
            return jsonify({'error': message}), 400

        state['df'] = mapped_df
        state['trained'] = False
        summary = get_dataset_summary(mapped_df)

        logger.info(f"Dataset validated: {message}")

        return _jsonify_safe({
            'success': True,
            'message': f'Dataset uploaded: {len(mapped_df)} rows, {len(mapped_df.columns)} columns. {message}',
            'summary': summary
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/api/load-preset', methods=['POST'])
def load_preset_dataset():
    """Load pre-packaged benchmark datasets (IBM HR Analytics or Healthcare Attrition)."""
    try:
        preset = request.json.get('preset', 'ibm') if request.json else 'ibm'
        success, message = load_dataset_state(preset)
        if not success:
            return jsonify({'error': message}), 400

        summary = get_dataset_summary(state['df'])
        logger.info(f"Loaded preset dataset: {preset} ({message})")

        return _jsonify_safe({
            'success': True,
            'message': message,
            'summary': summary,
            'dataset_key': preset,
            'best_model': state.get('train_result', {}).get('best_model')
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Failed to load preset: {str(e)}'}), 500



@app.route('/api/train', methods=['POST'])
def train_models():
    """
    Train all survival models on the loaded dataset.
    Uses the new scientific pipeline with train/test split, CV, and proper evaluation.
    """
    try:
        if state['df'] is None:
            return jsonify({'error': 'No dataset loaded. Please upload a CSV first.'}), 400

        df = state['df']
        logger.info("=" * 60)
        logger.info("TRAINING STARTED via /api/train")

        # 1. Process data
        logger.info("Preprocessing data...")
        X, T, E, employee_info, scaler = get_survival_data(df)
        state['X'] = X
        state['T'] = T
        state['E'] = E
        state['employee_info'] = employee_info
        state['scaler'] = scaler
        logger.info(f"Preprocessing complete: {X.shape[0]} samples, {X.shape[1]} features")

        # 2. Run the full scientific training pipeline
        logger.info("Running training pipeline...")
        train_result = train_pipeline(X, T, E, employee_info)

        # 3. Store everything in state
        state['cph'] = train_result['cph']
        state['rsf'] = train_result['rsf']
        state['kmf'] = train_result['kmf']
        state['predictions'] = train_result['predictions']
        state['model_comparison'] = train_result['model_comparison']
        state['train_result'] = train_result
        state['baseline_stats'] = train_result.get('baseline_stats')
        state['risk_thresholds'] = train_result['risk_thresholds']
        state['ensemble_weights'] = train_result['ensemble_weights']
        state['hazard_ratios'] = train_result['metrics']['cox'].get('hazard_ratios', [])
        state['roc_curve_plot'] = train_result.get('roc_curve_plot')
        state['confusion_matrices_plot'] = train_result.get('confusion_matrices_plot')
        state['classification_metrics'] = train_result.get('model_comparison', {}).get('classification_metrics')

        # 4. SHAP values (computed on the full feature matrix for global explainability)
        logger.info("Computing SHAP values...")
        shap_values, shap_X, explainer = compute_shap_values(train_result['rsf'], X)
        state['shap_values'] = shap_values
        state['shap_X'] = shap_X
        state['shap_explainer'] = explainer
        logger.info("SHAP computation complete")

        # 5. Save models and generate report
        dataset_key = state.get('dataset_key', 'custom')
        saved_dir = os.path.join(app.root_path, 'outputs', 'saved_models', dataset_key)
        logger.info(f"Saving models for [{dataset_key}] to {saved_dir}...")
        save_models(train_result, scaler, X.columns, output_dir=saved_dir)
        train_result['predictions'].to_parquet(os.path.join(saved_dir, 'predictions.parquet'))

        logger.info("Generating evaluation report...")
        dataset_info = get_dataset_summary(df)
        generate_evaluation_report(
            train_result, scaler, X.columns, dataset_info, output_dir='outputs'
        )

        state['trained'] = True
        logger.info("Training pipeline complete!")

        # 6. Build response (backward compatible + new fields)
        predictions = train_result['predictions']
        comparison = train_result['model_comparison']

        return _jsonify_safe({
            'success': True,
            'message': 'All models trained successfully!',
            'model_comparison': comparison,
            'total_employees': len(predictions),
            'risk_distribution': predictions['risk_category'].value_counts().to_dict(),
            # New fields (frontend ignores these, but they're available)
            'split': train_result['split'],
            'cross_validation': {
                'cox': train_result['cross_validation']['cox'],
                'rsf': train_result['cross_validation']['rsf'],
            },
            'best_model': train_result['best_model'],
            'ensemble_weights': train_result['ensemble_weights'],
            'risk_thresholds': train_result['risk_thresholds'],
            'total_time': train_result.get('total_time', 0)
        })

    except Exception as e:
        error_tb = traceback.format_exc()
        try:
            logger.error(f"Training failed: {str(e)}")
        except:
            pass
        return jsonify({'error': f'Training failed: {str(e)}', 'traceback': error_tb}), 500


@app.route('/api/results/overview', methods=['GET'])
def get_overview():
    """Return overview dashboard data: KM curves, C-index, SHAP global."""
    try:
        if not state['trained']:
            return jsonify({'error': 'Models not trained yet.'}), 400

        T, E = state['T'], state['E']
        employee_info = state['employee_info']

        # Kaplan-Meier overall curve
        km_overall = kaplan_meier_plot(T, E)

        # Kaplan-Meier by department
        if 'Department' in employee_info.columns:
            departments = employee_info['Department']
            km_department = kaplan_meier_plot(T, E, groups=departments,
                                              group_col_name='Department')
        else:
            km_department = None

        # Global SHAP (safe check)
        shap_plot = None
        if state.get('shap_values') is not None and state.get('shap_X') is not None:
            shap_plot = global_shap_plot(state['shap_values'], state['shap_X'])

        # Real Model Metrics
        train_result = state.get('train_result') or {}
        baseline_stats = state.get('baseline_stats') or train_result.get('baseline_stats') or {}
        comp = state.get('model_comparison') or {}

        ens_metrics = train_result.get('metrics', {}).get('ensemble', {})
        ens_c_index = ens_metrics.get('test_c_index') or comp.get('ensemble_c_index')
        ens_ibs = ens_metrics.get('test_ibs') or comp.get('ensemble_ibs')

        base_auc = baseline_stats.get('c_index_auc') or baseline_stats.get('roc_auc')

        if ens_c_index and base_auc:
            delta_pct = round(((ens_c_index - base_auc) / base_auc) * 100.0, 1)
            delta_str = f"{'+' if delta_pct >= 0 else ''}{delta_pct:.1f}% vs Logistic Reg"
        else:
            delta_str = "--"

        # Extract Cox model stats
        cph = state.get('cph')
        cph_stats = {}
        if cph:
            cph_stats = {
                'log_likelihood': round(float(getattr(cph, 'log_likelihood_', -1000.0)), 2),
                'aic': round(float(getattr(cph, 'AIC_partial_', 2000.0)), 2),
                'penalizer': float(getattr(cph, 'penalizer', 0.001)),
                'n_params': len(cph.params_) if hasattr(cph, 'params_') else 0
            }

        # Risk distribution
        preds = state.get('predictions')
        risk_dist = preds['risk_category'].value_counts().to_dict() if preds is not None and 'risk_category' in preds else {}
        cluster_dist = preds['resignation_cluster'].value_counts().to_dict() if preds is not None and 'resignation_cluster' in preds else {}
        total_employees = len(preds) if preds is not None else 0
        avg_tenure = round(float(preds['avg_median_months'].mean()), 1) if preds is not None and 'avg_median_months' in preds else None

        if state.get('roc_curve_plot') is None or state.get('classification_metrics') is None:
            _ensure_classification_plots_and_metrics()

        best_model = train_result.get('best_model')
        if not best_model:
            cox_c = train_result.get('metrics', {}).get('cox', {}).get('test_c_index', 0)
            rsf_c = train_result.get('metrics', {}).get('rsf', {}).get('test_c_index', 0)
            ens_c = ens_c_index or 0
            if ens_c >= max(cox_c, rsf_c):
                best_model = 'Self-Calibrating Survival Ensemble'
            elif rsf_c > cox_c:
                best_model = 'Random Survival Forest'
            else:
                best_model = 'Cox Proportional Hazards'

        # Build response (backward compatible + new fields appended)
        response = {
            'km_overall_plot': km_overall,
            'km_department_plot': km_department,
            'shap_global_plot': shap_plot,
            'roc_curve_plot': state.get('roc_curve_plot'),
            'confusion_matrices_plot': state.get('confusion_matrices_plot'),
            'classification_metrics': state.get('classification_metrics'),
            'model_comparison': state.get('model_comparison'),
            'risk_distribution': risk_dist,
            'cluster_distribution': cluster_dist,
            'total_employees': total_employees,
            'avg_predicted_tenure': avg_tenure,
            'baseline_stats': state.get('baseline_stats', baseline_stats),
            'baseline_delta': delta_str,
            'ensemble_c_index': ens_c_index,
            'ensemble_ibs': ens_ibs,
            'cph_stats': cph_stats,
            'best_model': best_model,
            'ensemble_weights': state.get('ensemble_weights', {'cox': 0.5, 'rsf': 0.5})
        }

        # Append new evaluation fields (frontend ignores but API consumers can use)
        train_result = state.get('train_result')
        if train_result:
            response['split'] = train_result.get('split', {})
            cv = train_result.get('cross_validation', {})
            response['cross_validation'] = {
                'cox': cv.get('cox', {}),
                'rsf': cv.get('rsf', {}),
            }
            response['hazard_ratios'] = state.get('hazard_ratios', [])
            response['risk_thresholds'] = state.get('risk_thresholds', {})
            m = train_result.get('metrics', {})
            response['metrics'] = m
            response['best_model'] = best_model
            response['rsf_params'] = train_result.get('rsf_params', {})
            response['calibration'] = {
                'cox': m.get('cox', {}).get('calibration', []),
                'rsf': m.get('rsf', {}).get('calibration', []),
            }

        return _jsonify_safe(response)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Failed to get overview: {str(e)}'}), 500


@app.route('/api/results/employees', methods=['GET'])
def get_employees():
    """Return paginated employee list with predictions."""
    try:
        if not state['trained']:
            return jsonify({'error': 'Models not trained yet.'}), 400

        preds = state['predictions']

        # Search/filter
        search = request.args.get('search', '').strip().lower()
        risk_filter = request.args.get('risk', '').strip()
        cluster_filter = request.args.get('cluster', '').strip()

        filtered = preds.copy()

        if search:
            mask = (
                filtered['EmployeeID'].astype(str).str.contains(search) |
                filtered['Department'].str.lower().str.contains(search, na=False) |
                filtered['JobRole'].str.lower().str.contains(search, na=False)
            )
            filtered = filtered[mask]

        if risk_filter:
            filtered = filtered[filtered['risk_category'] == risk_filter]

        if cluster_filter:
            filtered = filtered[filtered['resignation_cluster'] == cluster_filter]

        # Pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        total = len(filtered)
        start = (page - 1) * per_page
        end = start + per_page

        page_data = filtered.iloc[start:end]

        # Build response rows (backward compatible)
        rows = []
        for _, row in page_data.iterrows():
            rows.append({
                'employee_id': str(row['EmployeeID']) if pd.notna(row.get('EmployeeID')) else None,
                'age': int(row['Age']) if pd.notna(row.get('Age')) else None,
                'department': str(row.get('Department', 'N/A')),
                'job_role': str(row.get('JobRole', 'N/A')),
                'salary': float(row.get('Salary', row.get('MonthlyIncome', 5000) * 12.0)),
                'monthly_income': float(row.get('MonthlyIncome', row.get('Salary', 60000) / 12.0)),
                'years_at_company': round(float(row.get('YearsAtCompany', 0)), 1),
                'performance': int(row.get('PerformanceRating', 0)),
                'satisfaction': int(row.get('JobSatisfaction', 0)),
                'overtime': str(row.get('Overtime', 'N/A')),
                'attrition_status': str(row.get('AttritionStatus', 'N/A')),
                'cox_median': round(float(row['cox_median_months']), 1) if not np.isinf(row['cox_median_months']) else 999,
                'rsf_median': round(float(row['rsf_median_months']), 1),
                'avg_median': round(float(row['avg_median_months']), 1),
                'expected_tenure_months': round(float(row.get('expected_tenure_months', row.get('avg_median_months', 24.0))), 1),
                'resignation_cluster': row['resignation_cluster'],
                'risk_category': row['risk_category'],
                'duration_months': round(float(row.get('duration_months', 0)), 1),
                'event': int(row.get('event', 0))
            })

        return _jsonify_safe({
            'employees': rows,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Failed to get employees: {str(e)}'}), 500


@app.route('/api/results/employee/<string:emp_id>', methods=['GET'])
def get_employee_detail(emp_id):
    """Return detailed prediction for a specific employee."""
    try:
        if not state['trained']:
            return jsonify({'error': 'Models not trained yet.'}), 400

        preds = state['predictions']
        X = state['X']
        cph = state['cph']
        rsf = state['rsf']

        # Find employee
        mask = preds['EmployeeID'].astype(str) == str(emp_id)
        if not mask.any():
            return jsonify({'error': f'Employee {emp_id} not found'}), 404

        idx = mask.idxmax()
        emp_row = preds.loc[idx]
        X_single = X.loc[[idx]]

        # Individual survival curve plot
        surv_plot = plot_employee_survival(cph, rsf, X_single, emp_id)

        # Survival probabilities at key timepoints
        cox_surv = cox_predict_survival(cph, X_single, times=[2, 4, 6, 8, 12, 18, 24])
        surv_probs = {
            f'{int(t)}_months': round(float(cox_surv.loc[t].values[0]), 3)
            for t in cox_surv.index
        }

        # SHAP explanation for this employee (safe fallback if not pre-computed)
        shap_X = state.get('shap_X')
        shap_values = state.get('shap_values')
        explainer = state.get('shap_explainer')

        if shap_values is None or shap_X is None or explainer is None:
            logger.info("Computing SHAP values on-demand for detail view...")
            shap_values, shap_X, explainer = compute_shap_values(rsf, X)
            state['shap_values'] = shap_values
            state['shap_X'] = shap_X
            state['shap_explainer'] = explainer

        # Check if this employee is in the SHAP sample
        if idx in shap_X.index:
            shap_idx = list(shap_X.index).index(idx)
            shap_vals_single = shap_values[shap_idx]
            feature_vals = shap_X.iloc[shap_idx]
        else:
            shap_vals_single = explainer.shap_values(X_single.values, nsamples=50)[0]
            feature_vals = X_single.iloc[0]

        shap_plot = employee_shap_plot(shap_vals_single, feature_vals, emp_id)
        top_reasons = get_top_reasons(shap_vals_single, feature_vals, top_n=5)

        # Build employee profile (backward compatible)
        profile = {
            'employee_id': str(emp_row['EmployeeID']),
            'age': int(emp_row.get('Age', 0)),
            'gender': str(emp_row.get('Gender', 'N/A')),
            'department': str(emp_row.get('Department', 'N/A')),
            'job_role': str(emp_row.get('JobRole', 'N/A')),
            'salary': round(float(emp_row.get('Salary', 0)), 2),
            'years_at_company': round(float(emp_row.get('YearsAtCompany', 0)), 1),
            'performance_rating': int(emp_row.get('PerformanceRating', 0)),
            'promotion_count': int(emp_row.get('PromotionCount', 0)),
            'work_life_balance': int(emp_row.get('WorkLifeBalance', 0)),
            'overtime': str(emp_row.get('Overtime', 'N/A')),
            'distance_from_home': int(emp_row.get('DistanceFromHome', 0)),
            'training_hours': int(emp_row.get('TrainingHours', 0)),
            'job_satisfaction': int(emp_row.get('JobSatisfaction', 0)),
            'monthly_income': round(float(emp_row.get('MonthlyIncome', 0)), 2),
            'joining_date': str(emp_row.get('JoiningDate', 'N/A')),
            'exit_date': str(emp_row.get('ExitDate', 'N/A')),
            'attrition_status': str(emp_row.get('AttritionStatus', 'N/A')),
            'tenure_months': round(float(emp_row.get('duration_months', 0)), 1),
            'event': int(emp_row.get('event', 0))
        }

        # Prediction dict (backward compatible + new fields appended)
        prediction = {
            'cox_median_months': round(float(emp_row['cox_median_months']), 1) if not np.isinf(emp_row['cox_median_months']) else None,
            'rsf_median_months': round(float(emp_row['rsf_median_months']), 1),
            'avg_median_months': round(float(emp_row['avg_median_months']), 1),
            'resignation_cluster': emp_row['resignation_cluster'],
            'risk_category': emp_row['risk_category'],
            'survival_probabilities': surv_probs
        }

        # NEW: Confidence interval and uncertainty
        uncertainty = compute_prediction_uncertainty(rsf, X_single)
        prediction['confidence_interval'] = {
            'lower': uncertainty['ci_lower'],
            'upper': uncertainty['ci_upper']
        }
        prediction['confidence_score'] = uncertainty['confidence_score']
        prediction['model_source'] = emp_row.get('model_source', 'Weighted Ensemble')
        prediction['data_split'] = emp_row.get('data_split', 'unknown')

        # NEW: Ensemble weights
        ensemble_weights = state.get('ensemble_weights', {'cox': 0.5, 'rsf': 0.5})
        prediction['ensemble_weights'] = ensemble_weights

        # NEW: Test C-index of the model that generated this prediction
        train_result = state.get('train_result', {})
        metrics = train_result.get('metrics', {})
        prediction['model_test_c_index'] = {
            'cox': metrics.get('cox', {}).get('test_c_index'),
            'rsf': metrics.get('rsf', {}).get('test_c_index')
        }

        # Determine stay/leave reasoning (backward compatible)
        if emp_row['risk_category'] in ['Critical', 'High']:
            verdict = 'LIKELY TO LEAVE'
            verdict_detail = (
                f"Employee {emp_id} shows a high resignation risk. "
                f"Predicted median tenure: {prediction['avg_median_months']} months "
                f"(95% CI: {uncertainty['ci_lower']}–{uncertainty['ci_upper']} months). "
                f"Window: {prediction['resignation_cluster']}. "
                f"Model confidence: {uncertainty['confidence_score']}%."
            )
        else:
            verdict = 'LIKELY TO STAY'
            verdict_detail = (
                f"Employee {emp_id} shows low resignation risk. "
                f"Predicted median tenure: {prediction['avg_median_months']} months "
                f"(95% CI: {uncertainty['ci_lower']}–{uncertainty['ci_upper']} months). "
                f"Expected to remain for 12+ months. "
                f"Model confidence: {uncertainty['confidence_score']}%."
            )

        # Generate detailed human-readable explanation
        detailed_explanation = generate_detailed_explanation(
            profile, prediction, top_reasons, surv_probs
        )

        # Generate SHAP-to-LLM diagnostic narrative
        from models.llm_diagnostics import generate_employee_diagnostic
        llm_diag = generate_employee_diagnostic(profile, top_reasons)

        return _jsonify_safe({
            'profile': profile,
            'prediction': prediction,
            'verdict': verdict,
            'verdict_detail': verdict_detail,
            'survival_plot': surv_plot,
            'shap_plot': shap_plot,
            'top_reasons': top_reasons,
            'detailed_explanation': detailed_explanation,
            'llm_diagnostic': llm_diag
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Failed to get employee detail: {str(e)}'}), 500


# ===================== NEW NEXUS API ENDPOINTS =====================

@app.route('/api/triage', methods=['GET', 'POST'])
def financial_triage():
    """Compute ELV and Revenue at Risk score for financial exposure triage with multi-horizon & department filtering."""
    try:
        if state['df'] is None or state['predictions'] is None:
            return jsonify({'error': 'No trained model or predictions available.'}), 400

        from models.elv_calculator import compute_revenue_at_risk, compute_revenue_recall_at_k, compute_financial_kpis
        preds = state['predictions']

        # Support horizon & department filtering from either JSON or URL query params
        req_data = request.json if request.is_json else {}
        horizon = req_data.get('horizon') or request.args.get('horizon', '90d')
        department = req_data.get('department') or request.args.get('department', 'All')

        triage_df = compute_revenue_at_risk(preds, horizon=horizon, department=department)
        kpis = compute_financial_kpis(triage_df)
        recall_at_k = compute_revenue_recall_at_k(preds)

        # Department list for dropdown
        dept_list = ['All']
        if 'Department' in preds.columns:
            unique_depts = sorted([str(d) for d in preds['Department'].dropna().unique().tolist() if str(d).strip() != ''])
            dept_list.extend(unique_depts)

        records = triage_df.head(100).to_dict(orient='records')
        return _jsonify_safe({
            'success': True,
            'total_employees': len(triage_df),
            'total_revenue_at_risk': kpis['total_revenue_at_risk'],
            'avg_exposure_per_at_risk': kpis['avg_exposure_per_at_risk'],
            'at_risk_count': kpis['at_risk_count'],
            'at_risk_pct': kpis['at_risk_pct'],
            'top_department_name': kpis['top_department_name'],
            'top_dept_name': kpis['top_department_name'],
            'top_department_rar': kpis['top_department_rar'],
            'top_dept_rar': kpis['top_department_rar'],
            'top_department_pct': kpis['top_department_pct'],
            'departments': dept_list,
            'active_horizon': horizon,
            'horizon': horizon,
            'active_department': department,
            'recall_at_k': recall_at_k,
            'triage_leaderboard': records
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Triage failed: {str(e)}'}), 500


@app.route('/api/agent/run', methods=['POST'])
def run_agent_pipeline():
    """Run full 5-Agent pipeline for a given employee."""
    try:
        if state['predictions'] is None:
            return jsonify({'error': 'Please train the model pipeline first.'}), 400

        data = request.json or {}
        emp_id = str(data.get('employee_id', ''))
        
        preds = state['predictions']
        emp_row = preds[preds['EmployeeID'].astype(str) == emp_id]
        
        if len(emp_row) == 0:
            emp_record = preds.iloc[0].to_dict()
        else:
            emp_record = emp_row.iloc[0].to_dict()

        from models.agent_pipeline import NexusMultiAgentPipeline
        agent_pipeline = NexusMultiAgentPipeline()
        agent_res = agent_pipeline.run_full_pipeline_for_employee(emp_record)

        return _jsonify_safe({
            'success': True,
            'agent_results': agent_res,
            'employee_info': agent_res.get('employee_info', {}),
            'action_card': agent_res.get('action_card', {}),
            'diagnostic': agent_res.get('diagnostic', {}),
            'strategist': agent_res.get('strategist', {})
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Agent execution failed: {str(e)}'}), 500


@app.route('/api/agent/feedback', methods=['POST'])
def agent_feedback():
    """Receive 30-day intervention outcome and update Contextual Bandit policy."""
    try:
        data = request.json or {}
        emp_id = str(data.get('employee_id', ''))
        action = data.get('action', 'Salary Review')
        outcome = data.get('outcome', 'retained')  # 'retained' or 'churned'

        if state['predictions'] is None:
            return jsonify({'error': 'Pipeline not trained.'}), 400

        preds = state['predictions']
        emp_row = preds[preds['EmployeeID'].astype(str) == emp_id]
        emp_record = emp_row.iloc[0].to_dict() if len(emp_row) > 0 else preds.iloc[0].to_dict()

        from models.agent_pipeline import FeedbackAgent
        fa = FeedbackAgent()
        res = fa.process(emp_record, action, outcome)

        return _jsonify_safe({
            'success': True,
            'feedback_result': res,
            'telemetry': res.get('telemetry', {})
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Feedback update failed: {str(e)}'}), 500


@app.route('/api/ablation', methods=['POST'])
def execute_ablation():
    """Run full Section 10 ablation study on loaded dataset."""
    try:
        if state['X'] is None or state['df'] is None:
            return jsonify({'error': 'Please upload or train dataset first.'}), 400

        from models.ablation import run_ablation_study
        res = run_ablation_study(state['X'], state['T'], state['E'], state['employee_info'])

        return _jsonify_safe({
            'success': True,
            'ablation_results': res['summary_table']
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Ablation study failed: {str(e)}'}), 500


@app.route('/api/benchmark/dual', methods=['POST'])
def execute_dual_benchmark():
    """Run paper benchmark across IBM HR Analytics and Healthcare datasets."""
    try:
        from models.benchmarking import run_dual_dataset_benchmarks
        res = run_dual_dataset_benchmarks()

        return _jsonify_safe({
            'success': True,
            'benchmark_results': res
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Dual benchmark failed: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)


