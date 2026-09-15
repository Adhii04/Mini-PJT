"""
SHAP-to-LLM Diagnostic Pipeline Module
=======================================
Implements Novelty 3 from the Nexus paper:
Converts numerical TreeSHAP feature importances and employee metadata into
natural language, manager-facing diagnostic narratives using LLM integration
with zero-dependency local fallback.
"""

import os
import json
import logging

logger = logging.getLogger(__name__)


def generate_shap_llm_prompt(employee_info, top_reasons, p_churn_90d=None, revenue_at_risk=None):
    """
    Construct a structured diagnostic prompt combining employee profile with top-5 SHAP values.
    """
    emp_id = employee_info.get('EmployeeID', 'N/A')
    role = employee_info.get('JobRole', 'Employee')
    dept = employee_info.get('Department', 'General')
    tenure = employee_info.get('YearsAtCompany', employee_info.get('duration_months', 12) / 12.0)
    salary = employee_info.get('Salary', employee_info.get('MonthlyIncome', 5000) * 12)

    features_str = ""
    for idx, reason in enumerate(top_reasons[:5], 1):
        feat_name = reason.get('feature', reason.get('name', 'Feature'))
        shap_val = reason.get('shap_value', reason.get('impact', 0.0))
        val_str = reason.get('value', 'N/A')
        direction = "INCREASES churn risk" if shap_val > 0 else "REDUCES churn risk"
        features_str += f"  {idx}. {feat_name} (Current Value: {val_str}): SHAP={shap_val:+.4f} ({direction})\n"

    p_churn_str = f"{p_churn_90d * 100:.1f}%" if p_churn_90d is not None else "High"
    rar_str = f"${revenue_at_risk:,.2f}" if revenue_at_risk is not None else "Significant"

    prompt = f"""You are an expert HR Analyst AI operating within the Nexus Attrition Prevention Framework.
Analyze the following employee risk profile and generate a concise, actionable 2-3 sentence executive diagnostic narrative explaining WHY this employee is at risk of leaving the company.

### Employee Profile
- Employee ID: {emp_id}
- Job Role: {role}
- Department: {dept}
- Tenure: {tenure:.1f} years
- Salary: ${salary:,.2f}
- 90-Day Churn Probability: {p_churn_str}
- Revenue at Risk: {rar_str}

### Top Contributing SHAP Factors (TreeSHAP Explainer)
{features_str}

### Required Output Format:
Provide a clear, professional narrative starting with: "This employee is flagged for retention risk primarily due to..."
Explain the main underlying root causes based directly on the SHAP factors provided above. Avoid generic fluff. Keep it under 80 words.
"""
    return prompt


def _generate_local_fallback_narrative(employee_info, top_reasons):
    """
    High-quality, realistic rule-based text generator when no LLM API key is available.
    """
    risk_factors = []
    protective_factors = []

    for reason in top_reasons[:5]:
        feat = reason.get('feature', 'Factor')
        shap_val = reason.get('shap_value', 0.0)
        val = reason.get('value', '')

        if 'overtime' in feat.lower() and ('yes' in str(val).lower() or str(val) == '1'):
            risk_factors.append("consistent overtime demands")
        elif 'promotion' in feat.lower():
            risk_factors.append("extended period without career advancement")
        elif 'satisfaction' in feat.lower():
            risk_factors.append(f"low recorded satisfaction score ({val})")
        elif 'worklife' in feat.lower() or 'balance' in feat.lower():
            risk_factors.append("sub-optimal work-life balance rating")
        elif 'distance' in feat.lower() or 'commute' in feat.lower():
            risk_factors.append(f"significant commute distance ({val} km)")
        elif 'salary' in feat.lower() or 'income' in feat.lower():
            if shap_val > 0:
                risk_factors.append("below-market compensation benchmarking")
            else:
                protective_factors.append("competitive salary levels")
        elif shap_val > 0:
            risk_factors.append(f"{feat.lower()} (value: {val})")
        else:
            protective_factors.append(f"{feat.lower()}")

    if not risk_factors:
        risk_factors = ["tenure progression factors", "workplace workload distribution"]

    narrative = f"This employee is flagged for retention risk primarily due to {', '.join(risk_factors[:3])}."
    if protective_factors:
        narrative += f" However, {protective_factors[0]} serves as a mitigating factor."
    
    narrative += " Immediate HR intervention is recommended to review career alignment and workload balance."
    return narrative


def generate_employee_diagnostic(employee_info, top_reasons, p_churn_90d=None, revenue_at_risk=None, api_key=None):
    """
    Unified entry point to generate SHAP-to-LLM diagnostic narratives.
    
    Parameters
    ----------
    employee_info : dict
        Employee profile dictionary.
    top_reasons : list
        List of dicts containing feature names, SHAP values, and actual feature values.
    p_churn_90d : float, optional
        90-day churn probability.
    revenue_at_risk : float, optional
        Revenue at risk score.
    api_key : str, optional
        OpenAI/Anthropic API key. If omitted, checks environment or uses local generator.
    """
    prompt = generate_shap_llm_prompt(employee_info, top_reasons, p_churn_90d, revenue_at_risk)
    
    # 1. Check for API key
    if not api_key:
        api_key = os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY')

    # 2. Try LLM execution if key present
    if api_key:
        try:
            import requests
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 150,
                "temperature": 0.3
            }
            resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=5)
            if resp.status_code == 200:
                text = resp.json()['choices'][0]['message']['content'].strip()
                return {
                    'narrative': text,
                    'provider': 'GPT-4o-mini (Live API)',
                    'prompt': prompt
                }
        except Exception as e:
            logger.warning(f"LLM API call failed, falling back to local generator: {e}")

    # 3. Fallback to local rule-based engine
    text = _generate_local_fallback_narrative(employee_info, top_reasons)
    return {
        'narrative': text,
        'provider': 'Nexus Local Diagnostic Engine (Zero-Dependency Fallback)',
        'prompt': prompt
    }
