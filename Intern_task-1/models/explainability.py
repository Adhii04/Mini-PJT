"""
SHAP Explainability Module
Provides global and per-employee SHAP explanations for the RSF model.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import shap
import io
import base64


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
    """Apply dark theme."""
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
        'font.size': 11
    })


# Readable feature names mapping
FEATURE_LABELS = {
    'Age': 'Age',
    'Gender_enc': 'Gender (Male=1)',
    'Salary': 'Salary (Monthly)',
    'YearsAtCompany': 'Years at Company',
    'PerformanceRating': 'Performance Rating',
    'PromotionCount': 'Promotion Count',
    'WorkLifeBalance': 'Work-Life Balance',
    'Overtime_enc': 'Overtime (Yes=1)',
    'DistanceFromHome': 'Distance from Home',
    'TrainingHours': 'Training Hours',
    'JobSatisfaction': 'Job Satisfaction',
    'MonthlyIncome': 'Monthly Income',
    'DaysSinceLastPromotion': 'Days Since Last Promotion',
    'JobLevel': 'Job Level',
    'ManagerSatisfaction': 'Manager Satisfaction',
    'OvertimeDaysPerMonth': 'Overtime Days/Month',
    'MonthsSinceLastPromotion': 'Months Since Last Promotion',
    'StockOptions_enc': 'Stock Options (Yes=1)',
    'StockOptions': 'Stock Options',
}


def compute_shap_values(rsf, X, sample_size=25):
    """
    Compute SHAP values for the RSF model using a background sample.
    Returns shap_values and the explainer.
    """
    # Use a small subsample as background for speed (KernelExplainer is slow)
    if len(X) > sample_size:
        bg = X.sample(n=sample_size, random_state=42)
    else:
        bg = X.copy()

    # Wrap RSF predict to return risk scores
    def model_predict(data):
        return rsf.predict(data)

    explainer = shap.KernelExplainer(model_predict, bg.values)

    # Compute global SHAP for a very small subset to avoid 1-hour train times
    shap_sample_size = 40
    if len(X) > shap_sample_size:
        shap_X = X.sample(n=shap_sample_size, random_state=42)
    else:
        shap_X = X.copy()

    # nsamples=25 is sufficient for a rough global feature importance estimate
    import sys
    class DummyWriter:
        def write(self, x): pass
        def flush(self): pass
    
    old_stderr = sys.stderr
    sys.stderr = DummyWriter()
    try:
        shap_values = explainer.shap_values(shap_X.values, nsamples=25, silent=True)
    finally:
        sys.stderr = old_stderr

    return shap_values, shap_X, explainer


def global_shap_plot(shap_values, X_shap):
    """
    Generate global SHAP feature importance bar plot.
    Returns base64 image.
    """
    _dark_style()

    feature_names = [FEATURE_LABELS.get(c, c) for c in X_shap.columns]

    # Compute mean absolute SHAP values
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    sorted_idx = np.argsort(mean_abs_shap)[::-1]

    fig, ax = plt.subplots(figsize=(10, 7))

    colors = plt.cm.cool(np.linspace(0.2, 0.8, len(sorted_idx)))
    y_pos = range(len(sorted_idx))
    bars = ax.barh(
        y_pos,
        mean_abs_shap[sorted_idx][::-1],
        color=colors[::-1],
        edgecolor='none',
        height=0.7
    )

    ax.set_yticks(y_pos)
    ax.set_yticklabels([feature_names[i] for i in sorted_idx[::-1]], fontsize=10)
    ax.set_xlabel('Mean |SHAP Value| (Impact on Risk Score)', fontsize=12)
    ax.set_title('Global Feature Importance (SHAP)', fontsize=14, fontweight='bold', pad=15)
    ax.grid(axis='x', alpha=0.3)

    return _fig_to_base64(fig)


def employee_shap_plot(shap_values_single, feature_values, employee_id):
    """
    Generate per-employee SHAP waterfall-style horizontal bar plot.
    Returns base64 image.
    """
    _dark_style()

    feature_names = [FEATURE_LABELS.get(c, c) for c in feature_values.index]

    fig, ax = plt.subplots(figsize=(10, 7))

    sorted_idx = np.argsort(np.abs(shap_values_single))[::-1]

    vals = shap_values_single[sorted_idx]
    names = [feature_names[i] for i in sorted_idx]
    feat_vals = [feature_values.iloc[i] for i in sorted_idx]

    # Show top 10
    vals = vals[:10]
    names = names[:10]
    feat_vals = feat_vals[:10]

    # Reverse for horizontal bar
    vals = vals[::-1]
    names = names[::-1]
    feat_vals = feat_vals[::-1]

    colors = ['#ff4d6d' if v > 0 else '#00d4ff' for v in vals]

    y_pos = range(len(vals))
    ax.barh(y_pos, vals, color=colors, edgecolor='none', height=0.6)

    labels = [f'{n} = {v:.1f}' if isinstance(v, (int, float, np.floating, np.integer))
              else f'{n} = {v}' for n, v in zip(names, feat_vals)]
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel('SHAP Value (→ Higher Risk | ← Lower Risk)', fontsize=11)
    ax.set_title(f'SHAP Explanation – Employee {employee_id}',
                 fontsize=14, fontweight='bold', pad=15)
    ax.axvline(x=0, color='#555', linewidth=1, linestyle='-')
    ax.grid(axis='x', alpha=0.3)

    return _fig_to_base64(fig)


def get_top_reasons(shap_values_single, feature_values, top_n=3):
    """
    Return the top N reasons driving the prediction for an employee.
    Returns list of dicts with feature, value, impact, direction.
    """
    feature_names = list(feature_values.index)
    readable_names = [FEATURE_LABELS.get(c, c) for c in feature_names]

    sorted_idx = np.argsort(np.abs(shap_values_single))[::-1]

    reasons = []
    for i in sorted_idx[:top_n]:
        val = feature_values.iloc[i]
        shap_val = shap_values_single[i]
        direction = 'increases' if shap_val > 0 else 'decreases'

        if isinstance(val, (int, float, np.floating, np.integer)):
            val_str = f'{val:.1f}'
        else:
            val_str = str(val)

        reasons.append({
            'feature': readable_names[i],
            'value': val_str,
            'shap_value': round(float(shap_val), 4),
            'direction': direction,
            'explanation': f"{readable_names[i]} = {val_str} {direction} resignation risk"
        })

    return reasons


def generate_detailed_explanation(profile, prediction, top_reasons, surv_probs):
    """
    Generate a detailed, human-readable multi-paragraph explanation
    of why the model predicts this employee will leave or stay.
    Returns a dict with 'verdict_title', 'summary', 'factor_analysis',
    'survival_narrative', and 'recommendation'.
    """
    risk = prediction['risk_category']
    avg_median = prediction['avg_median_months']
    cluster = prediction['resignation_cluster']
    is_leaving = risk in ['Critical', 'High']

    emp_id = profile.get('employee_id', 'N/A')
    dept = profile.get('department', 'N/A')
    role = profile.get('job_role', 'N/A')
    salary = profile.get('salary', 0)
    tenure = profile.get('years_at_company', 0)
    satisfaction = profile.get('job_satisfaction', 0)
    performance = profile.get('performance_rating', 0)
    wlb = profile.get('work_life_balance', 0)
    overtime = profile.get('overtime', 'N/A')
    distance = profile.get('distance_from_home', 0)
    promotions = profile.get('promotion_count', 0)

    # ---- 1. Verdict Title ----
    if risk == 'Critical':
        verdict_title = "⚠️ CRITICAL FLIGHT RISK — Immediate Intervention Recommended"
    elif risk == 'High':
        verdict_title = "🔴 HIGH RISK — This Employee Is Likely to Resign Soon"
    elif risk == 'Medium':
        verdict_title = "🟡 MODERATE RISK — Monitor This Employee Closely"
    else:
        verdict_title = "🟢 LOW RISK — This Employee Is Likely to Stay Long-Term"

    model_source = prediction.get('model_source', 'Weighted Ensemble')
    ci = prediction.get('confidence_interval', {})
    ci_str = f" (95% CI: {ci.get('lower', avg_median)}–{ci.get('upper', avg_median)} months)" if ci else ""
    conf_score = prediction.get('confidence_score', 0)
    conf_str = f" with {conf_score}% model confidence" if conf_score else ""

    # ---- 2. Summary Paragraph ----
    if is_leaving:
        summary = (
            f"Based on the analysis by the {model_source}, Employee #{emp_id} in the "
            f"{dept} department ({role}) is predicted to resign within approximately "
            f"{avg_median:.1f} months{ci_str}{conf_str}. The resignation window is "
            f"classified as {cluster}. "
            f"The survival models categorize this employee under the "
            f"'{risk}' risk level, indicating a strong probability of attrition "
            f"in the near future. The model arrived at this conclusion by analyzing "
            f"the employee's profile across multiple behavioral, financial, and "
            f"organizational factors."
        )
    else:
        summary = (
            f"Based on the analysis by the {model_source}, Employee #{emp_id} in the "
            f"{dept} department ({role}) is predicted to remain with the organization "
            f"for at least {avg_median:.1f} months{ci_str}{conf_str}. "
            f"The survival models classify this employee under the "
            f"'{risk}' risk category, suggesting stable retention. The model "
            f"considered the employee's overall satisfaction, compensation, career "
            f"growth trajectory, and work conditions to arrive at this conclusion."
        )

    # ---- 3. Factor-by-Factor Analysis ----
    factor_paragraphs = []

    for reason in top_reasons:
        feature = reason['feature']
        value = reason['value']
        direction = reason['direction']
        shap_val = reason['shap_value']

        if direction == 'increases':
            impact_word = "pushes the employee towards resignation"
            strength = "significantly" if abs(shap_val) > 0.5 else "moderately" if abs(shap_val) > 0.1 else "slightly"
        else:
            impact_word = "acts as a retention factor"
            strength = "strongly" if abs(shap_val) > 0.5 else "moderately" if abs(shap_val) > 0.1 else "slightly"

        paragraph = (
            f"• {feature} (current value: {value}): This factor {strength} "
            f"{impact_word}. "
        )

        # Add contextual explanation based on the feature
        feature_lower = feature.lower()
        if 'satisfaction' in feature_lower:
            if direction == 'increases':
                paragraph += (
                    "Low satisfaction levels are one of the strongest predictors of employee "
                    "turnover. Employees who feel dissatisfied with their role or manager "
                    "are statistically far more likely to seek opportunities elsewhere."
                )
            else:
                paragraph += (
                    "A healthy satisfaction score indicates the employee feels valued and "
                    "engaged. This is one of the most powerful retention signals in the data."
                )
        elif 'salary' in feature_lower or 'income' in feature_lower:
            if direction == 'increases':
                paragraph += (
                    "The employee's compensation appears below the threshold where "
                    "retention risk increases. Salary dissatisfaction is a leading "
                    "driver of voluntary turnover across industries."
                )
            else:
                paragraph += (
                    "Competitive compensation serves as a strong anchor keeping "
                    "this employee connected to the organization."
                )
        elif 'overtime' in feature_lower:
            if direction == 'increases':
                paragraph += (
                    "Excessive overtime leads to burnout and work-life imbalance, "
                    "which are well-documented causes of attrition. This employee's "
                    "overtime pattern is contributing to their elevated risk."
                )
            else:
                paragraph += (
                    "A manageable workload helps maintain work-life balance, "
                    "reducing the likelihood of burnout-driven resignation."
                )
        elif 'promotion' in feature_lower:
            if direction == 'increases':
                paragraph += (
                    "A prolonged period without career advancement signals stagnation. "
                    "Employees who feel their growth has plateaued are significantly "
                    "more likely to explore external opportunities."
                )
            else:
                paragraph += (
                    "Recent or adequate promotions signal career growth, which is "
                    "a key factor in keeping employees motivated and retained."
                )
        elif 'distance' in feature_lower or 'commute' in feature_lower:
            if direction == 'increases':
                paragraph += (
                    "A long daily commute adds physical and mental fatigue, which "
                    "compounds with other workplace stressors and increases the "
                    "desire to find a closer workplace."
                )
            else:
                paragraph += (
                    "A short commute reduces daily stress and is associated with "
                    "higher overall job satisfaction."
                )
        elif 'balance' in feature_lower:
            if direction == 'increases':
                paragraph += (
                    "Poor work-life balance is a critical warning sign. Employees "
                    "struggling to maintain personal boundaries are at elevated "
                    "risk of burnout and eventual departure."
                )
            else:
                paragraph += (
                    "Good work-life balance contributes to long-term employee "
                    "well-being and is strongly correlated with retention."
                )
        elif 'performance' in feature_lower:
            if direction == 'increases':
                paragraph += (
                    "Interestingly, both very high and very low performers show "
                    "elevated attrition. Top performers may leave for better offers, "
                    "while low performers may be managed out."
                )
            else:
                paragraph += (
                    "The employee's performance level aligns with stable retention "
                    "patterns observed across the organization."
                )
        elif 'age' in feature_lower:
            if direction == 'increases':
                paragraph += (
                    "The employee's age group is associated with higher mobility "
                    "in the workforce, which may reflect career exploration or "
                    "a desire for new challenges."
                )
            else:
                paragraph += (
                    "The employee's age group is associated with greater stability "
                    "and lower voluntary turnover rates."
                )
        elif 'training' in feature_lower:
            if direction == 'increases':
                paragraph += (
                    "Insufficient training hours may indicate the employee lacks "
                    "development opportunities, which can lead to disengagement."
                )
            else:
                paragraph += (
                    "Adequate training investment shows the organization is investing "
                    "in this employee's growth, which strengthens loyalty."
                )
        elif 'stock' in feature_lower:
            if direction == 'increases':
                paragraph += (
                    "The absence of stock options or equity reduces the financial "
                    "incentive to stay long-term with the organization."
                )
            else:
                paragraph += (
                    "Stock options create a vesting-based retention lock, "
                    "giving the employee a financial reason to stay."
                )
        elif 'years' in feature_lower or 'tenure' in feature_lower:
            if direction == 'increases':
                paragraph += (
                    "The employee's tenure duration is associated with a transition "
                    "period where attrition rates tend to be higher."
                )
            else:
                paragraph += (
                    "Established tenure suggests institutional commitment and "
                    "integration that makes departure less likely."
                )
        elif 'level' in feature_lower:
            if direction == 'increases':
                paragraph += (
                    "The employee's job level may be contributing to feelings of "
                    "limited growth or being undervalued in the organization."
                )
            else:
                paragraph += (
                    "The employee's seniority level is associated with greater "
                    "organizational commitment and stability."
                )
        else:
            paragraph += (
                f"The model identified this factor as having a measurable impact "
                f"on the prediction for this specific employee."
            )

        factor_paragraphs.append(paragraph)

    factor_analysis = "\n\n".join(factor_paragraphs)

    # ---- 4. Survival Narrative ----
    prob_entries = []
    for key, val in surv_probs.items():
        months = key.replace('_months', '')
        pct = round(val * 100, 1)
        prob_entries.append((int(months), pct))

    prob_entries.sort(key=lambda x: x[0])

    if is_leaving:
        # Find the month where probability drops below 50%
        drop_month = None
        for m, p in prob_entries:
            if p < 50:
                drop_month = m
                break

        if drop_month:
            survival_narrative = (
                f"The survival curve shows that this employee's probability of staying "
                f"drops below 50% by month {drop_month}. "
            )
        else:
            survival_narrative = (
                f"Although classified as high risk, the survival curve shows the "
                f"probability declining gradually. "
            )

        survival_narrative += (
            f"Specifically, the model estimates a "
            f"{prob_entries[0][1]}% chance of staying past {prob_entries[0][0]} months, "
            f"declining to {prob_entries[-1][1]}% by month {prob_entries[-1][0]}. "
            f"This declining trajectory confirms the model's assessment that "
            f"resignation is probable within the {cluster} timeframe."
        )
    else:
        survival_narrative = (
            f"The survival curve for this employee remains strong over time. "
            f"The model estimates a {prob_entries[0][1]}% chance of staying past "
            f"{prob_entries[0][0]} months, and still {prob_entries[-1][1]}% by month "
            f"{prob_entries[-1][0]}. This flat, high survival curve is characteristic "
            f"of employees with strong organizational attachment who are unlikely "
            f"to resign in the foreseeable future."
        )

    # ---- 5. Recommendation ----
    if risk == 'Critical':
        recommendation = (
            "URGENT ACTION REQUIRED: This employee should be prioritized for an "
            "immediate one-on-one retention conversation with their direct manager "
            "or HR Business Partner. Consider an emergency compensation review, "
            "role enrichment, flexible work arrangements, or a fast-tracked promotion "
            "to address the root causes identified above. Delay in intervention "
            "significantly reduces the chances of retention."
        )
    elif risk == 'High':
        recommendation = (
            "ACTION RECOMMENDED: Schedule a career development discussion within "
            "the next 2 weeks. Review the employee's compensation against market rates, "
            "assess whether their current role aligns with their career aspirations, "
            "and address any workload or management concerns. Proactive engagement "
            "at this stage can meaningfully reduce attrition probability."
        )
    elif risk == 'Medium':
        recommendation = (
            "MONITOR CLOSELY: While not at immediate risk, this employee shows some "
            "warning signs. Include them in the next engagement survey follow-up, "
            "ensure regular check-ins with their manager, and watch for any negative "
            "changes in the factors identified above. Early attention can prevent "
            "escalation to high-risk status."
        )
    else:
        recommendation = (
            "MAINTAIN ENGAGEMENT: This employee appears well-retained. Continue "
            "providing growth opportunities, recognize their contributions, and "
            "maintain the positive conditions that keep them engaged. Periodic "
            "check-ins (quarterly) are sufficient to ensure continued satisfaction. "
            "This employee could also serve as a mentor or culture champion."
        )

    return {
        'verdict_title': verdict_title,
        'summary': summary,
        'factor_analysis': factor_analysis,
        'factor_paragraphs': factor_paragraphs,
        'survival_narrative': survival_narrative,
        'recommendation': recommendation
    }
