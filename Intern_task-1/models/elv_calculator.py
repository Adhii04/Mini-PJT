"""
ELV & Revenue at Risk Economic Triage Engine
============================================
Implements Novelty 2 from the Nexus paper:
1. Employee Lifetime Value (ELV) calculation
2. Per-employee Revenue at Risk score (ELV * P(churn in 90 days))
3. Financial risk ranking and triage
4. Revenue Recall@K metric calculation
"""

import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def compute_elv(monthly_income, tenure_months=None, projected_remaining_months=None):
    """
    Compute Employee Lifetime Value (ELV) per employee.
    
    Formula:
    ELV = Monthly Income * 3 * Remaining Tenure (months)
    
    Parameters
    ----------
    monthly_income : float or np.ndarray
        Monthly income/salary of employee.
    tenure_months : float or np.ndarray, optional
        Current tenure of employee in months.
    projected_remaining_months : float or np.ndarray, optional
        Projected remaining tenure (or predicted median survival time).
    """
    monthly_income = np.maximum(monthly_income, 1000.0)  # Default floor for zero/missing values
    
    if projected_remaining_months is not None:
        remaining_tenure = np.maximum(projected_remaining_months, 3.0)
    elif tenure_months is not None:
        # Standard assumption: expected 5-year (60 month) career horizon minus current tenure
        remaining_tenure = np.maximum(60.0 - tenure_months, 12.0)
    else:
        remaining_tenure = 24.0  # Default 2-year horizon

    elv = monthly_income * 3.0 * (remaining_tenure / 12.0)
    return np.round(elv, 2)


def compute_revenue_at_risk(predictions_df):
    """
    Compute per-employee Revenue at Risk score and return sorted financial triage DataFrame.
    
    Revenue at Risk = ELV * P(churn in 90 days)
    """
    df = predictions_df.copy()
    
    # 1. Obtain Monthly Income
    if 'MonthlyIncome' in df.columns:
        monthly_income = df['MonthlyIncome'].values
    elif 'Salary' in df.columns:
        # If Salary is annual, divide by 12
        monthly_income = np.where(df['Salary'] > 20000, df['Salary'] / 12.0, df['Salary'])
    else:
        monthly_income = np.full(len(df), 5000.0)

    # 2. Obtain current tenure or predicted median
    tenure_months = df['duration_months'].values if 'duration_months' in df.columns else df.get('YearsAtCompany', 2.0) * 12.0
    predicted_medians = df['avg_median_months'].values if 'avg_median_months' in df.columns else None

    # 3. Compute ELV
    elv = compute_elv(monthly_income, tenure_months, predicted_medians)
    df['elv'] = elv

    # 4. Obtain 90-day churn probability P(churn_90d)
    if 'prob_churn_90d' in df.columns:
        p_churn_90d = df['prob_churn_90d'].values
    elif 'avg_median_months' in df.columns:
        # Logistic approximation from predicted median: P(churn_90d) = 1 / (1 + exp((median - 3)/2))
        p_churn_90d = 1.0 / (1.0 + np.exp((df['avg_median_months'].values - 3.0) / 2.0))
    else:
        p_churn_90d = np.full(len(df), 0.1)

    df['prob_churn_90d'] = np.round(p_churn_90d, 4)

    # ─────────────────────────────────────────────────────────────────────────
    # 5.  CONFIDENCE-WEIGHTED REVENUE AT RISK
    # ─────────────────────────────────────────────────────────────────────────
    # The raw formula  RAR = ELV × P(churn)  is mathematically correct but
    # treats a 10% signal exactly the same way as a 90% signal — just scaled.
    # In practice, very low probabilities carry so much model uncertainty that
    # including them at face value inflates the total exposure figure.
    #
    # We address this with three confidence bands:
    #
    #   P(churn_90d) ≥ 0.80  → confidence_weight = 1.00   (near-certain departure)
    #   P(churn_90d) ≥ 0.40  → confidence_weight = 0.70   (probable but uncertain)
    #   P(churn_90d) < 0.40  → confidence_weight = 0.40   (low signal; model noise)
    #
    # Effective RAR = ELV × P(churn_90d) × confidence_weight
    #
    # This gives three behavioural properties:
    #   1. High-confidence churners (>80%) drive the leaderboard correctly.
    #   2. Mid-range (40–80%) employees still appear but at reduced exposure.
    #   3. Low-probability employees (<40%) are de-prioritised without being
    #      silently dropped — they still have a revenue_at_risk value.
    #
    # NOTE: The original unweighted RAR is retained as `rar_unweighted` so
    # the Revenue Recall@K metric (which compares ELV-triage vs prob-triage)
    # still uses the comparable, undiscounted values.

    BAND_HIGH   = 0.80   # near-certain: full weight
    BAND_MID    = 0.40   # probable:     70% weight
    W_HIGH      = 1.00
    W_MID       = 0.70
    W_LOW       = 0.40

    confidence_weight = np.where(
        p_churn_90d >= BAND_HIGH, W_HIGH,
        np.where(p_churn_90d >= BAND_MID, W_MID, W_LOW)
    )

    df['confidence_weight']  = np.round(confidence_weight, 2)
    df['rar_unweighted']     = np.round(elv * p_churn_90d, 2)          # original formula kept for recall metric
    revenue_at_risk          = elv * p_churn_90d * confidence_weight    # confidence-adjusted exposure
    df['revenue_at_risk']    = np.round(revenue_at_risk, 2)


    # 6. Assign Financial Exposure Tier using DUAL-GATE logic:
    #    Gate 1: Churn probability must exceed a meaningful threshold.
    #    Gate 2: Revenue at risk must exceed an absolute dollar threshold.
    #
    #    Pure quartile-based ranking (previous approach) is wrong: it always
    #    flags exactly 25% as "High", even if all employees have <10% churn risk.
    #
    #    Tier definitions:
    #      Critical  : churn ≥ 50%  AND  revenue_at_risk ≥ $15,000
    #      High      : churn ≥ 25%  AND  revenue_at_risk ≥ $10,000
    #      Moderate  : churn ≥ 10%  (some meaningful departure signal present)
    #      Watch     : churn ≥ 5%   (low signal, monitor)
    #      Stable    : churn < 5%   (effectively no near-term flight risk)

    CRITICAL_CHURN  = 0.50
    CRITICAL_RAR    = 15_000

    HIGH_CHURN      = 0.25
    HIGH_RAR        = 10_000

    MODERATE_CHURN  = 0.10
    WATCH_CHURN     = 0.05

    def assign_exposure(row_p, row_rar):
        p   = float(row_p)
        rar = float(row_rar)
        if p >= CRITICAL_CHURN and rar >= CRITICAL_RAR:
            return 'Critical'
        elif p >= HIGH_CHURN and rar >= HIGH_RAR:
            return 'High'
        elif p >= MODERATE_CHURN:
            return 'Moderate'
        elif p >= WATCH_CHURN:
            return 'Watch'
        else:
            return 'Stable'

    df['exposure_tier'] = [
        assign_exposure(p, r)
        for p, r in zip(p_churn_90d, revenue_at_risk)
    ]

    # Urgency score: combines churn likelihood and financial magnitude.
    # Useful for sorting; a high-earner with low churn will rank below
    # a moderate-earner who is actually likely to leave.
    #   urgency = 0.6 * prob_churn_90d + 0.4 * norm_revenue_at_risk
    max_rar = max(revenue_at_risk.max(), 1.0)
    df['urgency_score'] = np.round(
        0.6 * p_churn_90d + 0.4 * (revenue_at_risk / max_rar),
        4
    )

    # Actionable flag: employee is truly worth an immediate intervention
    df['actionable'] = (
        (p_churn_90d >= HIGH_CHURN) & (revenue_at_risk >= HIGH_RAR)
    ).astype(int)

    # Sort by urgency (churn-weighted) not raw revenue
    df_sorted = df.sort_values(by='urgency_score', ascending=False).reset_index(drop=True)
    return df_sorted



def compute_revenue_recall_at_k(df, k_percentiles=[5, 10, 15, 20, 25]):
    """
    Calculate Revenue Recall@K: how much of total financial exposure does each
    sorting strategy capture when flagging only the top K% of employees?

    Metric uses `rar_unweighted` (ELV × P(churn), no confidence discount) so
    both ELV-triage and prob-triage are compared on the same base value.
    This gives a fair comparison of prioritisation strategy, not confidence scaling.

    Revenue Recall@K = (Revenue at Risk in top-K employees) / (Total Revenue at Risk)
    """
    df_elv_sorted = compute_revenue_at_risk(df)

    # Use unweighted RAR for the recall denominator/numerator (apples-to-apples)
    rar_col = 'rar_unweighted' if 'rar_unweighted' in df_elv_sorted.columns else 'revenue_at_risk'
    total_rev_risk = df_elv_sorted[rar_col].sum()

    if total_rev_risk <= 0:
        total_rev_risk = 1.0

    n_total = len(df_elv_sorted)
    recall_results = []

    # Sort 1: ELV urgency-score triage (Nexus approach) — already sorted by urgency_score
    # Sort 2: Raw churn probability sort (legacy approach)
    df_prob_sorted = df_elv_sorted.sort_values(by='prob_churn_90d', ascending=False)

    for k_pct in k_percentiles:
        top_k_count = max(1, int(n_total * (k_pct / 100.0)))

        elv_captured  = df_elv_sorted.iloc[:top_k_count][rar_col].sum()
        elv_recall    = round((elv_captured  / total_rev_risk) * 100.0, 2)

        prob_captured = df_prob_sorted.iloc[:top_k_count][rar_col].sum()
        prob_recall   = round((prob_captured / total_rev_risk) * 100.0, 2)

        recall_results.append({
            'k_percentile':          k_pct,
            'top_k_employees':       top_k_count,
            'elv_triage_recall_pct': elv_recall,
            'prob_triage_recall_pct': prob_recall,
            'revenue_gain_pct':      round(elv_recall - prob_recall, 2)
        })

    return recall_results

