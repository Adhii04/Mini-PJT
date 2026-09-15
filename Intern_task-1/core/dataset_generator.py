"""
Synthetic HR Dataset Generator
Generates realistic employee data with survival-analysis-ready fields.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_dataset(n_employees=1000, seed=42):
    """Generate a synthetic HR dataset with realistic correlations."""
    np.random.seed(seed)

    departments = ['Engineering', 'Sales', 'HR', 'Marketing', 'Finance', 'Operations']
    job_roles = {
        'Engineering': ['Software Engineer', 'Data Scientist', 'DevOps Engineer', 'QA Engineer', 'Tech Lead'],
        'Sales': ['Sales Executive', 'Account Manager', 'Sales Lead', 'Business Dev Rep'],
        'HR': ['HR Specialist', 'Recruiter', 'HR Manager', 'Training Coordinator'],
        'Marketing': ['Marketing Analyst', 'Content Writer', 'SEO Specialist', 'Brand Manager'],
        'Finance': ['Financial Analyst', 'Accountant', 'Auditor', 'Finance Manager'],
        'Operations': ['Operations Analyst', 'Supply Chain Coord', 'Logistics Manager', 'Project Manager']
    }
    genders = ['Male', 'Female']

    records = []
    base_date = datetime(2020, 1, 1)
    current_date = datetime(2026, 6, 15)

    for i in range(1, n_employees + 1):
        dept = np.random.choice(departments)
        role = np.random.choice(job_roles[dept])
        gender = np.random.choice(genders)
        age = np.random.randint(22, 60)

        # Joining date: between 2015 and 2024
        join_offset = np.random.randint(0, 365 * 9)
        joining_date = datetime(2015, 1, 1) + timedelta(days=int(join_offset))

        years_at_company = (current_date - joining_date).days / 365.25

        performance = np.random.choice([1, 2, 3, 4, 5], p=[0.05, 0.10, 0.35, 0.35, 0.15])
        satisfaction = np.random.choice([1, 2, 3, 4, 5], p=[0.08, 0.12, 0.30, 0.30, 0.20])
        work_life = np.random.choice([1, 2, 3, 4, 5], p=[0.10, 0.15, 0.30, 0.25, 0.20])
        overtime = np.random.choice(['Yes', 'No'], p=[0.35, 0.65])
        distance = np.random.randint(1, 60)
        training = np.random.randint(0, 80)
        promotion_count = np.random.choice([0, 1, 2, 3, 4, 5], p=[0.30, 0.30, 0.20, 0.10, 0.07, 0.03])

        # Salary correlated with age, performance, role
        base_salary = 30000 + age * 500 + performance * 5000
        salary = base_salary + np.random.normal(0, 5000)
        monthly_income = salary / 12

        # Last promotion date
        if promotion_count > 0:
            promo_offset = np.random.randint(30, int(max(years_at_company * 365, 60)))
            last_promo = joining_date + timedelta(days=int(promo_offset))
            if last_promo > current_date:
                last_promo = current_date - timedelta(days=np.random.randint(30, 365))
        else:
            last_promo = None

        # Attrition logic: higher chance if low satisfaction, high overtime, low work-life
        attrition_score = (
            (5 - satisfaction) * 0.25 +
            (5 - work_life) * 0.15 +
            (1 if overtime == 'Yes' else 0) * 0.20 +
            (5 - performance) * 0.10 +
            (distance / 60) * 0.10 +
            (1 if promotion_count == 0 else 0) * 0.15 +
            np.random.normal(0, 0.1)
        )

        attrition = attrition_score > 0.55

        if attrition:
            # Exit date: between joining and current, biased by attrition score
            max_tenure_days = (current_date - joining_date).days
            if max_tenure_days < 60:
                tenure_days = max_tenure_days
            else:
                # Higher attrition score = shorter tenure
                mean_tenure = max(60, max_tenure_days * (1 - attrition_score * 0.6))
                tenure_days = int(np.clip(
                    np.random.exponential(mean_tenure),
                    30, max_tenure_days
                ))
            exit_date = joining_date + timedelta(days=tenure_days)
            if exit_date > current_date:
                exit_date = current_date - timedelta(days=np.random.randint(1, 30))
            attrition_status = 'Yes'
        else:
            exit_date = None
            attrition_status = 'No'

        records.append({
            'EmployeeID': 1000 + i,
            'Age': age,
            'Gender': gender,
            'Department': dept,
            'JobRole': role,
            'Salary': round(salary, 2),
            'YearsAtCompany': round(years_at_company, 2),
            'PerformanceRating': performance,
            'PromotionCount': promotion_count,
            'WorkLifeBalance': work_life,
            'Overtime': overtime,
            'DistanceFromHome': distance,
            'TrainingHours': training,
            'JobSatisfaction': satisfaction,
            'MonthlyIncome': round(monthly_income, 2),
            'LastPromotionDate': last_promo.strftime('%Y-%m-%d') if last_promo else None,
            'JoiningDate': joining_date.strftime('%Y-%m-%d'),
            'ExitDate': exit_date.strftime('%Y-%m-%d') if exit_date else None,
            'AttritionStatus': attrition_status
        })

    df = pd.DataFrame(records)
    return df


if __name__ == '__main__':
    df = generate_dataset(1000)
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, 'sample_hr_data.csv')
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} employee records -> {output_path}")
    print(f"Attrition rate: {df['AttritionStatus'].value_counts(normalize=True).get('Yes', 0):.1%}")
    print(df.head())
