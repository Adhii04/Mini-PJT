"""
Executor Agent (Agent 5)
========================
Synthesizes the diagnostic narrative and strategist intervention into a
complete, dispatch-ready Manager Action Card with concrete action steps.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ExecutorAgent:
    """
    Agent 5: Retention Action Card Builder & Dispatcher.
    Generates personalized execution plans for people managers.
    """
    def __init__(self, name: str = "Executor"):
        self.name = name

    def process(self, employee_record: Dict[str, Any], diagnostic_result: Dict[str, Any], strategist_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds a comprehensive, personalized Manager Action Card for execution.
        """
        emp_id = str(employee_record.get('EmployeeID', 'N/A'))
        role = str(employee_record.get('JobRole', 'Team Member'))
        dept = str(employee_record.get('Department', 'General'))
        action = str(strategist_result.get('selected_action', 'Managerial 1:1'))
        narrative = str(diagnostic_result.get('narrative', ''))
        
        income = float(employee_record.get('MonthlyIncome', employee_record.get('Salary', 5000.0)))
        overtime = str(employee_record.get('Overtime', 'No'))
        satisfaction = int(employee_record.get('JobSatisfaction', 3))
        wlb = int(employee_record.get('WorkLifeBalance', 3))
        tenure_rem = float(employee_record.get('avg_median_months', 24.0))
        rar = float(employee_record.get('revenue_at_risk', 0.0))

        # Action-specific customized steps and strategy narrative
        if action == "Salary Review":
            target_adj = round(income * 0.10, 0)
            strategy = (
                f"Proactively counter market pull by adjusting compensation toward the 75th percentile. "
                f"Employee #{emp_id} earns ${income:,.0f}/mo; an estimated +${target_adj:,.0f}/mo adjustment "
                f"protects ${rar:,.0f} in exposure over a {tenure_rem:.1f}-month horizon."
            )
            action_steps = [
                f"1. Initiate HR compensation benchmark audit for {role} (Current base: ${income:,.0f}/mo).",
                f"2. Submit formal adjustment proposal of approx +${target_adj:,.0f}/mo to Department Lead.",
                "3. Deliver formal revised compensation letter within 7 business days and log outcome in Nexus."
            ]
        elif action == "Retention Bonus":
            bonus_amt = max(2500.0, round(rar * 0.12, 0))
            strategy = (
                f"Execute immediate financial ring-fencing. Recommend a structured retention bonus of "
                f"${bonus_amt:,.0f} with a 12-month clawback vesting schedule to stabilize key role continuity."
            )
            action_steps = [
                f"1. Request approval for retention bonus of ${bonus_amt:,.0f} tied to key department deliverables.",
                "2. Conduct executive conversation highlighting organizational value and leadership roadmap.",
                "3. Execute sign-off agreement and register feedback outcome in the 30-day simulator."
            ]
        elif action == "Flexible Work":
            strategy = (
                f"Mitigate burnout and work-life friction (Current OverTime: {overtime}, WLB: {wlb}/4). "
                f"Introduce structured hybrid flexibility to restore engagement before formal departure."
            )
            action_steps = [
                f"1. Schedule workload restructuring meeting with {role} within 3 business days.",
                "2. Agree on 2-day remote flexibility and set a strict 5-hour/week cap on overtime.",
                "3. Rebalance active sprint workload and conduct a 14-day welfare check-in."
            ]
        elif action == "L&D Offer":
            strategy = (
                f"Re-energize career trajectory and internal mobility. Pair employee with advanced technical "
                f"or leadership credentials to overcome career stagnation risks."
            )
            action_steps = [
                f"1. Present tailored Executive / Technical development roadmap aligned to {dept} priorities.",
                "2. Grant dedicated $3,000 professional learning budget and assign senior mentor.",
                "3. Establish clear review criteria for advancement within the next 6-month cycle."
            ]
        else:  # Managerial 1:1
            strategy = (
                f"Conduct an urgent, confidential stay-interview. Deep-dive into satisfaction drivers "
                f"({satisfaction}/4 rating) and address organizational headwinds directly."
            )
            action_steps = [
                f"1. Schedule private 45-minute stay-interview with {role} within 48 hours.",
                "2. Probe core dissatisfaction triggers and align on team-level working improvements.",
                "3. Synthesize agreed commitments into written 30-day roadmap with weekly touchpoints."
            ]

        action_card = {
            'title': f"Nexus Retention Action Card — Employee #{emp_id}",
            'employee_id': emp_id,
            'job_role': role,
            'department': dept,
            'monthly_income': income,
            'revenue_at_risk': f"${rar:,.2f}",
            'revenue_at_risk_raw': rar,
            'rar': rar,
            'expected_tenure': f"{tenure_rem:.1f} Mo",
            'tenure_months': round(tenure_rem, 1),
            'recommended_intervention': action,
            'recommended_action': action,
            'intervention_cost': 5000 if 'Salary' in action or 'Compensation' in action else (3000 if 'L&D' in action else (1500 if 'Workload' in action else 500)),
            'prescribed_strategy': strategy,
            'strategy': strategy,
            'diagnostic_narrative': narrative,
            'action_steps': action_steps,
            'status': 'Action Plan Ready for Execution'
        }
        logger.info(f"[{self.name} Agent] Generated personalized Manager Action Card for Employee #{emp_id}.")
        return action_card
