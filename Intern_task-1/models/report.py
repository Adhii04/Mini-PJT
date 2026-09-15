"""
Report Generation Module
========================
Generates comprehensive model evaluation reports in HTML and JSON formats.
"""

import logging
import os
import json
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


def generate_evaluation_report(train_result, scaler, feature_names,
                                dataset_info, output_dir='outputs'):
    """
    Generate a complete model evaluation report.

    Produces:
    - outputs/model_report.html
    - outputs/model_metrics.json
    """
    os.makedirs(output_dir, exist_ok=True)

    metrics = train_result['metrics']
    cv = train_result['cross_validation']
    split = train_result['split']
    comparison = train_result['model_comparison']
    thresholds = train_result['risk_thresholds']

    # ================================================================
    # JSON Metrics
    # ================================================================
    metrics_json = {
        'generated_at': datetime.now().isoformat(),
        'dataset': {
            'total_employees': split['train_size'] + split['test_size'],
            'train_size': split['train_size'],
            'test_size': split['test_size'],
            'total_events': split['train_events'] + split['test_events'],
            'total_censored': split['train_censored'] + split['test_censored'],
            'feature_count': len(feature_names),
            'features': list(feature_names)
        },
        'cox_ph': {
            'train_c_index': metrics['cox']['train_c_index'],
            'test_c_index': metrics['cox']['test_c_index'],
            'train_ibs': metrics['cox']['train_ibs'],
            'test_ibs': metrics['cox']['test_ibs'],
            'train_time_seconds': metrics['cox']['train_time'],
            'cv_mean': cv['cox']['mean'],
            'cv_std': cv['cox']['std'],
            'cv_fold_scores': cv['cox']['fold_scores'],
            'penalizer': 0.001,
            'hazard_ratios': metrics['cox'].get('hazard_ratios', []),
            'calibration': metrics['cox'].get('calibration', [])
        },
        'rsf': {
            'train_c_index': metrics['rsf']['train_c_index'],
            'test_c_index': metrics['rsf']['test_c_index'],
            'train_ibs': metrics['rsf']['train_ibs'],
            'test_ibs': metrics['rsf']['test_ibs'],
            'train_time_seconds': metrics['rsf']['train_time'],
            'cv_mean': cv['rsf']['mean'],
            'cv_std': cv['rsf']['std'],
            'cv_fold_scores': cv['rsf']['fold_scores'],
            'n_estimators': metrics['rsf'].get('n_estimators', 300),
            'best_params': train_result.get('rsf_params', {}),
            'calibration': metrics['rsf'].get('calibration', [])
        },
        'ensemble': {
            'weights': train_result['ensemble_weights'],
            'method': 'weighted_average_by_test_c_index'
        },
        'best_model': train_result['best_model'],
        'risk_thresholds': thresholds,
        'total_training_time': train_result.get('total_time', 0)
    }

    json_path = os.path.join(output_dir, 'model_metrics.json')
    with open(json_path, 'w') as f:
        json.dump(metrics_json, f, indent=2, default=str)
    logger.info(f"Saved model_metrics.json → {json_path}")

    # ================================================================
    # HTML Report
    # ================================================================
    html = _build_html_report(metrics_json, comparison)

    html_path = os.path.join(output_dir, 'model_report.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    logger.info(f"Saved model_report.html → {html_path}")

    return json_path, html_path


def _build_html_report(m, comparison):
    """Build a styled HTML evaluation report."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Hazard ratio table rows
    hr_rows = ''
    for hr in m['cox_ph'].get('hazard_ratios', []):
        sig_color = '#2ee89e' if hr['significance'] == 'Significant' else '#8890a8'
        hr_rows += f"""
        <tr>
            <td>{hr['feature']}</td>
            <td>{hr['coefficient']}</td>
            <td><strong>{hr['hazard_ratio']}</strong></td>
            <td>[{hr['hr_ci_lower']}, {hr['hr_ci_upper']}]</td>
            <td>{hr['p_value']}</td>
            <td style="color:{sig_color}">{hr['significance']}</td>
            <td style="font-size:0.85em">{hr['interpretation']}</td>
        </tr>"""

    # CV fold scores
    cox_folds = ', '.join([str(s) for s in m['cox_ph']['cv_fold_scores'] if s is not None])
    rsf_folds = ', '.join([str(s) for s in m['rsf']['cv_fold_scores'] if s is not None])

    # Calibration rows
    cal_rows_cox = ''
    for c in m['cox_ph'].get('calibration', []):
        err_color = '#ff3b5c' if c['calibration_error'] > 0.1 else '#2ee89e'
        cal_rows_cox += f"""
        <tr>
            <td>{c['time']} months</td>
            <td>{c['predicted_mean']}</td>
            <td>{c['observed']}</td>
            <td style="color:{err_color}">{c['calibration_error']}</td>
            <td>{c['n_at_risk']}</td>
        </tr>"""

    cal_rows_rsf = ''
    for c in m['rsf'].get('calibration', []):
        err_color = '#ff3b5c' if c['calibration_error'] > 0.1 else '#2ee89e'
        cal_rows_rsf += f"""
        <tr>
            <td>{c['time']} months</td>
            <td>{c['predicted_mean']}</td>
            <td>{c['observed']}</td>
            <td style="color:{err_color}">{c['calibration_error']}</td>
            <td>{c['n_at_risk']}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Model Evaluation Report — Employee Survival Prediction</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: #080b1a; color: #e8ecf4; padding: 2rem;
            line-height: 1.6;
        }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        h1 {{ font-size: 1.8rem; color: #00d4ff; margin-bottom: 0.5rem; }}
        h2 {{ font-size: 1.3rem; color: #b44aff; margin: 2rem 0 1rem; border-bottom: 1px solid #2a3055; padding-bottom: 0.5rem; }}
        h3 {{ font-size: 1.05rem; color: #00d4ff; margin: 1.5rem 0 0.5rem; }}
        .meta {{ color: #8890a8; font-size: 0.85rem; margin-bottom: 2rem; }}
        .card {{
            background: rgba(15,20,45,0.75); border: 1px solid rgba(60,80,160,0.25);
            border-radius: 12px; padding: 1.25rem; margin-bottom: 1.25rem;
        }}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
        .metric {{ text-align: center; padding: 1rem; }}
        .metric-value {{ font-size: 1.8rem; font-weight: 700; }}
        .metric-label {{ font-size: 0.78rem; color: #8890a8; text-transform: uppercase; letter-spacing: 1px; }}
        .winner {{ color: #2ee89e; }}
        .good {{ color: #2ee89e; }}
        .warn {{ color: #ffd93d; }}
        .bad {{ color: #ff3b5c; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-top: 0.5rem; }}
        th {{ text-align: left; color: #00d4ff; padding: 8px 12px; border-bottom: 1px solid #2a3055; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; }}
        td {{ padding: 8px 12px; border-bottom: 1px solid rgba(60,80,160,0.1); }}
        .note {{ background: rgba(0,212,255,0.05); border-left: 3px solid #00d4ff; padding: 12px 16px; border-radius: 4px; font-size: 0.88rem; margin: 1rem 0; color: #a0b0d0; }}
        .warning {{ background: rgba(255,59,92,0.08); border-left: 3px solid #ff3b5c; padding: 12px 16px; border-radius: 4px; font-size: 0.88rem; margin: 1rem 0; }}
    </style>
</head>
<body>
<div class="container">
    <h1>📊 Model Evaluation Report</h1>
    <p class="meta">Employee Survival Prediction System | Generated: {now}</p>

    <h2>1. Dataset Summary</h2>
    <div class="card grid">
        <div class="metric">
            <div class="metric-value">{m['dataset']['total_employees']}</div>
            <div class="metric-label">Total Employees</div>
        </div>
        <div class="metric">
            <div class="metric-value">{m['dataset']['feature_count']}</div>
            <div class="metric-label">Features</div>
        </div>
        <div class="metric">
            <div class="metric-value">{m['dataset']['total_events']}</div>
            <div class="metric-label">Events (Resigned)</div>
        </div>
        <div class="metric">
            <div class="metric-value">{m['dataset']['total_censored']}</div>
            <div class="metric-label">Censored (Active)</div>
        </div>
        <div class="metric">
            <div class="metric-value">{m['dataset']['train_size']}</div>
            <div class="metric-label">Training Set</div>
        </div>
        <div class="metric">
            <div class="metric-value">{m['dataset']['test_size']}</div>
            <div class="metric-label">Test Set</div>
        </div>
    </div>

    <h2>2. Model Performance Comparison</h2>
    <div class="card">
        <table>
            <tr>
                <th>Metric</th>
                <th>Cox PH</th>
                <th>Random Survival Forest</th>
            </tr>
            <tr>
                <td>Train C-index</td>
                <td>{m['cox_ph']['train_c_index']}</td>
                <td>{m['rsf']['train_c_index']}</td>
            </tr>
            <tr>
                <td><strong>Test C-index</strong></td>
                <td><strong>{m['cox_ph']['test_c_index']}</strong></td>
                <td><strong>{m['rsf']['test_c_index']}</strong></td>
            </tr>
            <tr>
                <td>CV C-index (mean ± std)</td>
                <td>{m['cox_ph']['cv_mean']} ± {m['cox_ph']['cv_std']}</td>
                <td>{m['rsf']['cv_mean']} ± {m['rsf']['cv_std']}</td>
            </tr>
            <tr>
                <td>Integrated Brier Score (test)</td>
                <td>{m['cox_ph']['test_ibs']}</td>
                <td>{m['rsf']['test_ibs']}</td>
            </tr>
            <tr>
                <td>Training Time</td>
                <td>{m['cox_ph']['train_time_seconds']}s</td>
                <td>{m['rsf']['train_time_seconds']}s</td>
            </tr>
        </table>
        <div class="note">
            <strong>Best Model:</strong> {m['best_model']} |
            <strong>Ensemble Weights:</strong> Cox={m['ensemble']['weights']['cox']}, RSF={m['ensemble']['weights']['rsf']}
        </div>
    </div>

    <h2>3. Cross-Validation Results (5-Fold)</h2>
    <div class="card">
        <h3>Cox PH Fold Scores</h3>
        <p style="color:#a0b0d0">{cox_folds}</p>
        <p>Mean: <strong>{m['cox_ph']['cv_mean']}</strong> ± {m['cox_ph']['cv_std']}</p>

        <h3>RSF Fold Scores</h3>
        <p style="color:#a0b0d0">{rsf_folds}</p>
        <p>Mean: <strong>{m['rsf']['cv_mean']}</strong> ± {m['rsf']['cv_std']}</p>
    </div>

    <h2>4. Cox PH Hazard Ratios</h2>
    <div class="card">
        <table>
            <tr>
                <th>Feature</th><th>Coefficient</th><th>Hazard Ratio</th>
                <th>95% CI</th><th>p-value</th><th>Significance</th><th>Interpretation</th>
            </tr>
            {hr_rows}
        </table>
    </div>

    <h2>5. Calibration Analysis</h2>
    <div class="card">
        <h3>Cox PH Calibration</h3>
        <table>
            <tr><th>Time</th><th>Predicted Survival</th><th>Observed (KM)</th><th>Error</th><th>N at Risk</th></tr>
            {cal_rows_cox}
        </table>
        <h3>RSF Calibration</h3>
        <table>
            <tr><th>Time</th><th>Predicted Survival</th><th>Observed (KM)</th><th>Error</th><th>N at Risk</th></tr>
            {cal_rows_rsf}
        </table>
    </div>

    <h2>6. Risk Category Thresholds</h2>
    <div class="card">
        <p><strong>Method:</strong> {m['risk_thresholds']['method']}</p>
        <p>{m['risk_thresholds']['description']}</p>
    </div>

    <h2>7. Model Limitations</h2>
    <div class="card">
        <ul style="padding-left: 1.5rem; color: #a0b0d0;">
            <li>Survival analysis assumes non-informative censoring — employees who are still active are assumed to resign eventually.</li>
            <li>Cox PH assumes proportional hazards — the effect of each feature is constant over time. This may not hold for all features.</li>
            <li>The model was trained on historical data and may not capture future organizational changes.</li>
            <li>Predictions are probabilistic estimates, not deterministic outcomes.</li>
            <li>Small sample sizes or low event rates may reduce model reliability.</li>
            <li>SHAP explanations are approximations using KernelExplainer due to the non-standard RSF model interface.</li>
        </ul>
    </div>

    <h2>8. Business Interpretation</h2>
    <div class="card">
        <p style="color:#a0b0d0">
            The C-index measures how well the model ranks employees by resignation risk.
            A C-index of 0.5 = random guessing, 1.0 = perfect ranking.
            The Integrated Brier Score measures calibration accuracy — lower is better.
            The hazard ratios indicate the multiplicative effect of each feature on the resignation hazard.
            A hazard ratio > 1 means that feature increases risk; &lt; 1 means it decreases risk.
            Risk categories are computed from the percentile distribution of predicted resignation timelines,
            making them adaptive to the specific dataset rather than hardcoded.
        </p>
    </div>

    <p class="meta" style="margin-top: 3rem; text-align: center;">
        Total Training Time: {m['total_training_time']}s |
        Report generated by Employee Survival Prediction System
    </p>
</div>
</body>
</html>"""

    return html
