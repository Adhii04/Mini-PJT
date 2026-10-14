"""
Survival Models
Implements Kaplan-Meier, Cox Proportional Hazards, and Random Survival Forest.
"""

import numpy as np
import pandas as pd
import sys
import matplotlib
if 'ipykernel' not in sys.modules:
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from lifelines import KaplanMeierFitter, CoxPHFitter
from sksurv.ensemble import RandomSurvivalForest


def _fig_to_base64(fig):
    """Convert matplotlib figure to base64 PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=130, bbox_inches='tight',
                facecolor='#0f1429', edgecolor='none')
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return b64


def _dark_style():
    """Apply dark theme to matplotlib."""
    plt.rcParams.update({
        'figure.facecolor': '#0f1429',
        'axes.facecolor': '#161b33',
        'axes.edgecolor': '#2a3055',
        'axes.labelcolor': '#c8cfe0',
        'text.color': '#c8cfe0',
        'xtick.color': '#8890a8',
        'ytick.color': '#8890a8',
        'grid.color': '#1e2545',
        'grid.alpha': 0.6,
        'font.family': 'sans-serif',
        'font.size': 11
    })


# ===================== KAPLAN-MEIER =====================

def fit_kaplan_meier(T, E):
    """Fit overall Kaplan-Meier estimator and return it."""
    kmf = KaplanMeierFitter()
    kmf.fit(T, event_observed=E, label='Overall Survival')
    return kmf


def kaplan_meier_plot(T, E, groups=None, group_col_name='Group'):
    """
    Generate Kaplan-Meier survival curve plot.
    If groups is provided, plot per-group curves.
    Returns base64 image.
    """
    _dark_style()
    fig, ax = plt.subplots(figsize=(10, 6))

    if groups is not None:
        unique_groups = sorted(groups.unique())
        colors = plt.cm.cool(np.linspace(0.1, 0.9, len(unique_groups)))
        for grp, color in zip(unique_groups, colors):
            mask = groups == grp
            kmf = KaplanMeierFitter()
            kmf.fit(T[mask], event_observed=E[mask], label=str(grp))
            kmf.plot_survival_function(ax=ax, color=color, linewidth=2)
        ax.set_title(f'Kaplan-Meier Survival Curves by {group_col_name}',
                     fontsize=14, fontweight='bold', pad=15)
    else:
        kmf = KaplanMeierFitter()
        kmf.fit(T, event_observed=E, label='Overall')
        kmf.plot_survival_function(ax=ax, color='#00d4ff', linewidth=2.5)
        ax.fill_between(kmf.survival_function_.index,
                        kmf.confidence_interval_.iloc[:, 0],
                        kmf.confidence_interval_.iloc[:, 1],
                        alpha=0.15, color='#00d4ff')
        ax.set_title('Kaplan-Meier Overall Survival Curve',
                     fontsize=14, fontweight='bold', pad=15)

    ax.set_xlabel('Time (Months)', fontsize=12)
    ax.set_ylabel('Survival Probability', fontsize=12)
    ax.legend(fontsize=9, loc='lower left', framealpha=0.3)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.05)

    return _fig_to_base64(fig)


# ===================== COX PH =====================

def fit_cox_ph(X, T, E, penalizer=0.001):
    """
    Fit Cox Proportional Hazards model.
    X should already be standardized (zero mean, unit variance).
    Returns fitted CoxPHFitter.
    """
    df_cox = X.copy()

    # Remove zero-variance columns which cause CoxPH convergence errors
    for col in list(df_cox.columns):
        if df_cox[col].nunique() <= 1:
            df_cox = df_cox.drop(columns=[col])

    df_cox['duration'] = T
    df_cox['event'] = E

    # Remove zero/negative durations
    df_cox = df_cox[df_cox['duration'] > 0]

    # With standardized features, a small penalizer is fine
    # Extremely low penalizer since we use StandardScaler, allowing maximum coefficient learning
    cph = CoxPHFitter(penalizer=penalizer)
    cph.fit(df_cox, duration_col='duration', event_col='event')
    return cph


def cox_predict_survival(cph, X, times=None):
    """
    Predict survival function for each employee using Cox PH.
    Returns DataFrame of survival probabilities at given times.
    """
    if times is None:
        times = [2, 4, 6, 8, 12, 18, 24, 36]

    X_cox = X[cph.params_.index]
    surv_funcs = cph.predict_survival_function(X_cox, times=times)
    return surv_funcs


def cox_predict_median(cph, X):
    """Predict median survival time for each employee."""
    X_cox = X[cph.params_.index]
    medians = cph.predict_median(X_cox)
    return medians


def cox_predict_risk(cph, X):
    """Predict partial hazard (risk score) for each employee."""
    X_cox = X[cph.params_.index]
    return cph.predict_partial_hazard(X_cox)


# ===================== RANDOM SURVIVAL FOREST =====================

def fit_rsf(X, T, E, n_estimators=300, min_samples_split=6,
            min_samples_leaf=3, max_features='sqrt', max_depth=None,
            n_jobs=-1, random_state=42):
    """
    Fit Random Survival Forest.
    Accepts individual hyperparameters (from tuning or defaults).
    Returns fitted RSF model.
    """
    # Create structured array for sksurv
    y = np.array([(bool(e), t) for e, t in zip(E, T)],
                 dtype=[('event', bool), ('duration', float)])

    rsf = RandomSurvivalForest(
        n_estimators=n_estimators,
        min_samples_split=min_samples_split,
        min_samples_leaf=min_samples_leaf,
        max_features=max_features,
        max_depth=max_depth,
        n_jobs=n_jobs,
        random_state=random_state
    )
    rsf.fit(X.values, y)
    return rsf


def rsf_predict_survival(rsf, X, times=None):
    """
    Predict survival function for each employee using RSF.
    Returns DataFrame of survival probabilities at given times.
    """
    if times is None:
        times = np.array([2, 4, 6, 8, 12, 18, 24, 36])

    surv_funcs = rsf.predict_survival_function(X.values)

    results = []
    for sf in surv_funcs:
        probs = []
        for t in times:
            # Find closest time point
            idx = np.searchsorted(sf.x, t)
            if idx >= len(sf.x):
                probs.append(sf.y[-1])
            elif idx == 0:
                probs.append(sf.y[0])
            else:
                # Linear interpolation
                x0, x1 = sf.x[idx - 1], sf.x[idx]
                y0, y1 = sf.y[idx - 1], sf.y[idx]
                frac = (t - x0) / (x1 - x0) if x1 != x0 else 0
                probs.append(y0 + frac * (y1 - y0))
        results.append(probs)

    return pd.DataFrame(results, columns=[f't_{t}' for t in times], index=X.index)


def rsf_predict_risk(rsf, X):
    """Predict risk scores for each employee using RSF."""
    return rsf.predict(X.values)


def rsf_predict_median(rsf, X):
    """Estimate median survival time from RSF survival functions."""
    surv_funcs = rsf.predict_survival_function(X.values)
    medians = []
    for sf in surv_funcs:
        # Find time where survival drops below 0.5
        below_50 = np.where(sf.y <= 0.5)[0]
        if len(below_50) > 0:
            medians.append(sf.x[below_50[0]])
        else:
            medians.append(sf.x[-1])  # If never drops below 0.5, use max time
    return np.array(medians)


# ===================== INDIVIDUAL SURVIVAL PLOT =====================

def plot_employee_survival(cph, rsf, X_single, employee_id):
    """
    Plot overlaid survival curves from Cox PH and RSF for a single employee.
    Returns base64 image.
    """
    _dark_style()
    fig, ax = plt.subplots(figsize=(9, 5))

    # Cox PH survival curve
    times = np.linspace(0.5, 60, 120)
    X_cox_single = X_single[cph.params_.index]
    cox_surv = cph.predict_survival_function(X_cox_single, times=times)

    ax.plot(times, cox_surv.values.flatten(), color='#00d4ff', linewidth=2.5,
            label='Cox PH', linestyle='-')

    # RSF survival curve
    rsf_surv_funcs = rsf.predict_survival_function(X_single.values)
    for sf in rsf_surv_funcs:
        ax.plot(sf.x, sf.y, color='#ff6bcb', linewidth=2.5,
                label='Random Survival Forest', linestyle='--')

    # 50% survival line
    ax.axhline(y=0.5, color='#ffd93d', linestyle=':', alpha=0.7, linewidth=1.5,
               label='50% Survival Threshold')

    ax.set_title(f'Survival Curve – Employee {employee_id}',
                 fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Time (Months)', fontsize=12)
    ax.set_ylabel('Survival Probability', fontsize=12)
    ax.legend(fontsize=10, framealpha=0.3)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.05)
    ax.set_xlim(0, 60)

    return _fig_to_base64(fig)


# ===================== RESIGNATION WINDOW CLUSTERING =====================

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


def assign_risk_category(median_months, thresholds=None):
    """
    Assign risk category based on predicted median survival time.
    If thresholds are provided, uses data-driven percentile thresholds.
    Otherwise falls back to hardcoded defaults for backward compatibility.
    """
    if thresholds:
        from models.prediction import assign_risk_category_data_driven
        return assign_risk_category_data_driven(median_months, thresholds)

    # Legacy hardcoded fallback
    if median_months <= 3:
        return 'Critical'
    elif median_months <= 6:
        return 'High'
    elif median_months <= 12:
        return 'Medium'
    else:
        return 'Low'


def plot_roc_comparison(roc_curves_data):
    """
    Generate ROC curves comparison figure matching model_evaluation.ipynb.
    roc_curves_data: list of tuples (model_name, y_true, y_prob, color, linewidth)
    """
    _dark_style()
    fig, ax = plt.subplots(figsize=(8, 5))
    
    from sklearn.metrics import roc_curve, roc_auc_score
    for name, y_true, y_prob, color, lw in roc_curves_data:
        fpr, tpr, _ = roc_curve(y_true, y_prob)
        auc = roc_auc_score(y_true, y_prob)
        ax.plot(fpr, tpr, label=f"{name} (AUC = {auc:.4f})", color=color, linewidth=lw)

    ax.plot([0, 1], [0, 1], 'k--', color='#64748b', alpha=0.6, linewidth=1.5,
            label='Random Baseline (AUC = 0.5000)')

    ax.set_title('ROC Curves Comparison: Test Split Discrimination',
                 fontsize=12, fontweight='bold', color='#ffffff', pad=12)
    ax.set_xlabel('False Positive Rate (1 - Specificity)', fontsize=9.5, color='#94a3b8')
    ax.set_ylabel('True Positive Rate (Recall)', fontsize=9.5, color='#94a3b8')
    ax.legend(fontsize=8.5, facecolor='#161b33', edgecolor='#2a3055', labelcolor='#ffffff', loc='lower right')
    ax.grid(True, alpha=0.2, color='#2a3055')
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.05)

    return _fig_to_base64(fig)


def plot_confusion_matrices_grid(cm_models_data):
    """
    Generate side-by-side Confusion Matrix heatmaps matching model_evaluation.ipynb.
    cm_models_data: list of tuples (model_name, cm, accuracy, recall, f1, cmap_name)
    """
    _dark_style()
    n_models = len(cm_models_data)
    fig, axes = plt.subplots(1, n_models, figsize=(3.8 * n_models, 3.4))
    if n_models == 1:
        axes = [axes]

    for ax, (title, cm, acc, rec, f1, cmap) in zip(axes, cm_models_data):
        sns.heatmap(
            cm, annot=True, fmt='d', cmap=cmap, cbar=False, ax=ax,
            annot_kws={"size": 11, "weight": "bold", "color": "#ffffff"},
            xticklabels=['Stayed (0)', 'Left (1)'],
            yticklabels=['Stayed (0)', 'Left (1)']
        )
        ax.set_title(f"{title}\nAcc: {acc*100:.1f}% | Rec: {rec*100:.1f}% | F1: {f1:.3f}",
                     fontsize=9, fontweight='600', color='#ffffff', pad=8)
        ax.set_xlabel('Predicted Class', fontsize=8, color='#94a3b8')
        ax.set_ylabel('Actual Class', fontsize=8, color='#94a3b8')
        ax.tick_params(colors='#94a3b8', labelsize=8)

    plt.tight_layout()
    return _fig_to_base64(fig)
