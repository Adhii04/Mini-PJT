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


def compute_revenue_at_risk(predictions_df, horizon='90d', department=None):
    """
    Compute per-employee Revenue at Risk score and return sorted financial triage DataFrame.
    Supports multi-horizon forecasting (30-day, 60-day, 90-day) and department filtering.
    
    Revenue at Risk = ELV * P(churn in horizon) * Confidence_Weight
    """
    df = predictions_df.copy()

    # Optional department pre-filtering (case-insensitive, ignore 'all' or empty)
    if department and str(department).strip().lower() not in ['all', '', 'none'] and 'Department' in df.columns:
        dept_match = df['Department'].astype(str).str.lower() == str(department).strip().lower()
        if dept_match.any():
            df = df[dept_match].copy()
    
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

    # 4. Obtain horizon-specific churn probability
    horizon_key = str(horizon).lower().strip()
    if horizon_key in ['30d', '30', '30days'] and 'prob_churn_30d' in df.columns:
        p_churn = df['prob_churn_30d'].values
    elif horizon_key in ['60d', '60', '60days'] and 'prob_churn_60d' in df.columns:
        p_churn = df['prob_churn_60d'].values
    elif 'prob_churn_90d' in df.columns:
        p_churn = df['prob_churn_90d'].values
    elif 'avg_median_months' in df.columns:
        # Calibrated survival probability from expected tenure
        p_churn = np.clip(1.0 - (df['avg_median_months'].values / 60.0), 0.02, 0.95)
    else:
        p_churn = np.full(len(df), 0.1)

    df['prob_churn_active'] = np.round(p_churn, 4)
    df['prob_churn_90d'] = np.round(p_churn, 4)  # Retain for table display compatibility
    df['churn_prob'] = np.round(p_churn, 4)
    p_churn_eval = df['prob_churn_active'].values

    # 5. Confidence-weighted Revenue at Risk
    BAND_HIGH   = 0.80   # near-certain: full weight
    BAND_MID    = 0.40   # probable:     70% weight
    W_HIGH      = 1.00
    W_MID       = 0.70
    W_LOW       = 0.40

    confidence_weight = np.where(
        p_churn_eval >= BAND_HIGH, W_HIGH,
        np.where(p_churn_eval >= BAND_MID, W_MID, W_LOW)
    )

    df['confidence_weight']  = np.round(confidence_weight, 2)
    df['rar_unweighted']     = np.round(elv * p_churn_eval, 2)
    revenue_at_risk          = elv * p_churn_eval * confidence_weight
    df['revenue_at_risk']    = np.round(revenue_at_risk, 2)

    # 6. Assign Financial Exposure Tier using DUAL-GATE logic
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
        for p, r in zip(p_churn_eval, revenue_at_risk)
    ]

    # Urgency score: combines churn likelihood and financial magnitude
    max_rar = max(float(revenue_at_risk.max()) if len(revenue_at_risk) > 0 else 1.0, 1.0)
    df['urgency_score'] = np.round(
        0.6 * p_churn_eval + 0.4 * (revenue_at_risk / max_rar),
        4
    )

    df['actionable'] = (
        (p_churn_eval >= HIGH_CHURN) & (revenue_at_risk >= HIGH_RAR)
    ).astype(int)

    # Sort by urgency (churn-weighted) not raw revenue
    df_sorted = df.sort_values(by='urgency_score', ascending=False).reset_index(drop=True)
    return df_sorted


def compute_financial_kpis(triage_df):
    """
    Computes enterprise financial intelligence KPIs for Tab 2:
    1. Total Revenue at Risk (aggregate portfolio exposure)
    2. Average Exposure per At-Risk Employee
    3. High & Critical Flight Risk Headcount & workforce percentage
    4. Top Exposure Department name, exposure volume, and % share
    """
    if triage_df is None or len(triage_df) == 0:
        return {
            'total_revenue_at_risk': 0.0,
            'avg_exposure_per_at_risk': 0.0,
            'at_risk_count': 0,
            'at_risk_pct': 0.0,
            'top_department_name': 'N/A',
            'top_department_rar': 0.0,
            'top_department_pct': 0.0
        }

    total_rar = float(triage_df['revenue_at_risk'].sum())

    # Flight risk headcount: Critical or High
    at_risk_mask = triage_df['risk_category'].isin(['Critical', 'High']) if 'risk_category' in triage_df.columns else triage_df['exposure_tier'].isin(['Critical', 'High'])
    at_risk_df = triage_df[at_risk_mask]
    at_risk_count = int(len(at_risk_df))
    at_risk_pct = round((at_risk_count / max(len(triage_df), 1)) * 100.0, 1)

    avg_exposure = round(float(at_risk_df['revenue_at_risk'].mean()), 2) if at_risk_count > 0 else round(float(triage_df['revenue_at_risk'].mean()), 2) if len(triage_df) > 0 else 0.0

    # Top Department Analysis
    if 'Department' in triage_df.columns and len(triage_df) > 0:
        dept_grouped = triage_df.groupby('Department')['revenue_at_risk'].sum().sort_values(ascending=False)
        top_dept_name = str(dept_grouped.index[0]) if len(dept_grouped) > 0 else 'All Units'
        top_dept_rar = float(dept_grouped.iloc[0]) if len(dept_grouped) > 0 else 0.0
        top_dept_pct = round((top_dept_rar / max(total_rar, 1.0)) * 100.0, 1)
    else:
        top_dept_name = 'Enterprise Fleet'
        top_dept_rar = total_rar
        top_dept_pct = 100.0

    return {
        'total_revenue_at_risk': round(total_rar, 2),
        'avg_exposure_per_at_risk': avg_exposure,
        'at_risk_count': at_risk_count,
        'at_risk_pct': at_risk_pct,
        'top_department_name': top_dept_name,
        'top_department_rar': round(top_dept_rar, 2),
        'top_department_pct': top_dept_pct
    }



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

