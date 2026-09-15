"""
Data Processor
Handles CSV/Excel loading, smart column mapping, feature engineering for survival analysis.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import re
from sklearn.preprocessing import StandardScaler


# ===================== SMART COLUMN MAPPING =====================
# Maps our internal column name -> list of possible aliases (lowercase, stripped)
COLUMN_ALIASES = {
    'EmployeeID': [
        'employeeid', 'employee_id', 'emp_id', 'empid', 'id', 'emp id',
        'employee id', 'employee number', 'employeenumber', 'emp_no', 'empno',
        'worker_id', 'workerid', 'staff_id', 'staffid', 'sr no', 'srno',
        'sr_no', 'serial', 'serial no', 'serialno', 's.no', 'sno'
    ],
    'Age': [
        'age', 'employee_age', 'employeeage', 'emp_age', 'empage'
    ],
    'Gender': [
        'gender', 'sex', 'employee_gender', 'employeegender'
    ],
    'Department': [
        'department', 'dept', 'department_name', 'departmentname',
        'dept_name', 'deptname', 'division', 'business_unit', 'businessunit'
    ],
    'JobRole': [
        'jobrole', 'job_role', 'job role', 'role', 'job_title', 'jobtitle',
        'job title', 'position', 'designation', 'title', 'job_name', 'jobname'
    ],
    'Salary': [
        'salary', 'annual_salary', 'annualsalary', 'annual salary',
        'yearly_salary', 'yearlysalary', 'pay', 'compensation',
        'total_compensation', 'totalcompensation', 'ctc', 'annual_income',
        'annualincome'
    ],
    'YearsAtCompany': [
        'yearsatcompany', 'years_at_company', 'years at company', 'tenure',
        'tenureyears', 'tenure_years', 'tenure years',
        'years_in_company', 'yearsincompany', 'experience', 'years_of_service',
        'yearsofservice', 'service_years', 'serviceyears', 'company_tenure',
        'companytenure', 'total_working_years', 'totalworkingyears',
        'years_experience', 'yearsexperience'
    ],
    'PerformanceRating': [
        'performancerating', 'performance_rating', 'performance rating',
        'performance', 'perf_rating', 'perfrating', 'rating',
        'performance_score', 'performancescore', 'perf_score', 'perfscore',
        'last_performance_rating', 'lastperformancerating'
    ],
    'PromotionCount': [
        'promotioncount', 'promotion_count', 'promotion count', 'promotions',
        'num_promotions', 'numpromotions', 'total_promotions',
        'totalpromotions', 'number_of_promotions', 'numberofpromotions',
        'promotionslast5years', 'promotions_last_5_years', 'promotions last 5 years'
    ],
    'WorkLifeBalance': [
        'worklifebalance', 'work_life_balance', 'work life balance',
        'wlb', 'work_balance', 'workbalance', 'life_balance', 'lifebalance'
    ],
    'Overtime': [
        'overtime', 'over_time', 'over time', 'ot', 'works_overtime',
        'worksovertime', 'overwork', 'extra_hours', 'extrahours'
    ],
    'DistanceFromHome': [
        'distancefromhome', 'distance_from_home', 'distance from home',
        'distance', 'commute_distance', 'commutedistance', 'commute',
        'travel_distance', 'traveldistance', 'home_distance', 'homedistance',
        'commutedistancekm', 'commute_distance_km', 'commute distance km'
    ],
    'TrainingHours': [
        'traininghours', 'training_hours', 'training hours', 'training',
        'training_time', 'trainingtime', 'trainingtimeslastyear',
        'training_times_last_year', 'trainingtimes', 'training_count',
        'trainingcount', 'traininghoursperyear', 'training_hours_per_year',
        'training hours per year'
    ],
    'JobSatisfaction': [
        'jobsatisfaction', 'job_satisfaction', 'job satisfaction',
        'satisfaction', 'satisfaction_level', 'satisfactionlevel',
        'job_sat', 'jobsat', 'employee_satisfaction', 'employeesatisfaction'
    ],
    'MonthlyIncome': [
        'monthlyincome', 'monthly_income', 'monthly income', 'monthly_pay',
        'monthlypay', 'monthly_salary', 'monthlysalary', 'month_income',
        'monthincome', 'income'
    ],
    'JoiningDate': [
        'joiningdate', 'joining_date', 'joining date', 'join_date',
        'joindate', 'hire_date', 'hiredate', 'hired_date', 'hireddate',
        'start_date', 'startdate', 'date_of_joining', 'dateofjoining',
        'doj', 'employment_date', 'employmentdate', 'onboarding_date',
        'onboardingdate', 'date_hired', 'datehired'
    ],
    'ExitDate': [
        'exitdate', 'exit_date', 'exit date', 'leaving_date', 'leavingdate',
        'resignation_date', 'resignationdate', 'termination_date',
        'terminationdate', 'end_date', 'enddate', 'last_working_day',
        'lastworkingday', 'departure_date', 'departuredate',
        'date_of_exit', 'dateofexit', 'separation_date', 'separationdate',
        'left_date', 'leftdate', 'relieving_date', 'relievingdate'
    ],
    'AttritionStatus': [
        'attritionstatus', 'attrition_status', 'attrition status',
        'attrition', 'left', 'resigned', 'terminated',
        'employee_status', 'employeestatus', 'is_active', 'isactive',
        'churned', 'churn', 'turnover', 'left_company',
        'leftcompany', 'still_employed', 'stillemployed', 'attrition_flag',
        'attritionflag', 'leaveornot', 'leave_or_not'
    ],
    'LastPromotionDate': [
        'lastpromotiondate', 'last_promotion_date', 'last promotion date',
        'promotion_date', 'promotiondate', 'last_promoted',
        'lastpromoted', 'lastpromotion'
    ],
    'MonthsSinceLastPromotion': [
        'monthssincelastpromotion', 'months_since_last_promotion',
        'months since last promotion'
    ],
    'OvertimeDaysPerMonth': [
        'overtimedayspermonth', 'overtime_days_per_month', 'overtime days'
    ],
    'MaritalStatus': ['maritalstatus', 'marital_status', 'marital status'],
    'JobLevel': ['joblevel', 'job_level', 'job level'],
    'ManagerSatisfaction': [
        'managersatisfaction', 'manager_satisfaction', 'manager satisfaction'
    ],
    'StockOptions': ['stockoptions', 'stock_options', 'stock options'],
    'WorkArrangement': [
        'workarrangement', 'work_arrangement', 'work arrangement'
    ],
}

# Minimum required columns (the system MUST have these to function)
ESSENTIAL_COLUMNS = ['EmployeeID', 'AttritionStatus']

# Columns needed for survival duration (at least one date needed)
DATE_COLUMNS = ['JoiningDate']

# Feature columns used by models (built from available mapped columns)
ALL_FEATURE_SOURCES = [
    'Age', 'Gender', 'Salary', 'YearsAtCompany', 'PerformanceRating',
    'PromotionCount', 'WorkLifeBalance', 'Overtime', 'DistanceFromHome',
    'TrainingHours', 'JobSatisfaction', 'MonthlyIncome', 'LastPromotionDate'
]


def _normalize(name):
    """Normalize a column name for matching."""
    return re.sub(r'[^a-z0-9]', '', name.lower().strip())


def auto_map_columns(df):
    """
    Automatically map dataset columns to internal column names.
    Returns (mapped_df, mapping_report).
    """
    column_map = {}  # original_col -> internal_col
    mapped = set()
    unmapped_internal = []

    df_cols_normalized = {_normalize(c): c for c in df.columns}

    for internal_name, aliases in COLUMN_ALIASES.items():
        found = False

        # 1. Exact match (case-insensitive)
        for col in df.columns:
            if col.lower().strip() == internal_name.lower():
                if col not in column_map:
                    column_map[col] = internal_name
                    mapped.add(internal_name)
                    found = True
                    break

        if found:
            continue

        # 2. Alias match
        for alias in aliases:
            norm_alias = _normalize(alias)
            if norm_alias in df_cols_normalized:
                original_col = df_cols_normalized[norm_alias]
                if original_col not in column_map:
                    column_map[original_col] = internal_name
                    mapped.add(internal_name)
                    found = True
                    break

        if found:
            continue

        # 3. Substring/partial match as last resort
        for col in df.columns:
            if col in column_map:
                continue
            norm_col = _normalize(col)
            for alias in aliases:
                norm_alias = _normalize(alias)
                # Ensure the alias is reasonably long to avoid false positives
                if (norm_alias in norm_col or norm_col in norm_alias) and len(norm_alias) >= 4:
                    column_map[col] = internal_name
                    mapped.add(internal_name)
                    found = True
                    break
            if found:
                break

        if not found:
            unmapped_internal.append(internal_name)

    # Rename columns
    renamed_df = df.rename(columns=column_map)

    # Build report
    report = {
        'mapped': {v: k for k, v in column_map.items()},
        'unmapped': unmapped_internal,
        'total_mapped': len(column_map),
        'total_columns': len(df.columns)
    }

    return renamed_df, report


def validate_dataset(df):
    """
    Validate dataset with smart column mapping.
    Returns (is_valid, message, mapped_df).
    """
    if len(df) == 0:
        return False, "Dataset is empty.", df

    # Auto-map columns
    mapped_df, report = auto_map_columns(df)

    # Check essential columns
    missing_essential = []
    for col in ESSENTIAL_COLUMNS:
        if col not in mapped_df.columns:
            missing_essential.append(col)

    if missing_essential:
        suggestions = []
        for col in missing_essential:
            aliases = COLUMN_ALIASES.get(col, [])
            suggestions.append(f"'{col}' (expected names: {', '.join(aliases[:5])}...)")

        return False, (
            f"Cannot find essential columns: {', '.join(missing_essential)}. "
            f"Your dataset has columns: {', '.join(df.columns.tolist())}. "
            f"Expected: {'; '.join(suggestions)}"
        ), df

    # Check for at least some date column or YearsAtCompany
    has_joining = 'JoiningDate' in mapped_df.columns
    has_tenure = 'YearsAtCompany' in mapped_df.columns

    if not has_joining and not has_tenure:
        return False, (
            "Need at least 'JoiningDate' or 'YearsAtCompany' to compute tenure. "
            f"Your columns: {', '.join(df.columns.tolist())}"
        ), df

    # Generate auto EmployeeID if missing
    if 'EmployeeID' not in mapped_df.columns:
        mapped_df['EmployeeID'] = range(1001, 1001 + len(mapped_df))

    # Build success message
    mapped_names = [f"{v} → {k}" for k, v in report['mapped'].items()]
    unmapped_msg = ""
    if report['unmapped']:
        unmapped_msg = f" | Not found (will use defaults): {', '.join(report['unmapped'])}"

    message = (
        f"Dataset mapped successfully! "
        f"{report['total_mapped']}/{report['total_columns']} columns matched.{unmapped_msg}"
    )

    return True, message, mapped_df


def engineer_features(df):
    """
    Compute survival analysis features with flexible column handling.
    Missing columns get sensible defaults.
    IMPORTANT: This does NOT scale any numeric values. Original values are preserved.
    """
    df = df.copy()
    original_columns = set(df.columns)  # Track what the user actually provided
    current_date = pd.Timestamp(datetime.now())

    # ---- Handle duration computation ----
    if 'JoiningDate' in df.columns:
        df['JoiningDate'] = pd.to_datetime(df['JoiningDate'], errors='coerce')

        if 'ExitDate' in df.columns:
            df['ExitDate'] = pd.to_datetime(df['ExitDate'], errors='coerce')
        else:
            df['ExitDate'] = pd.NaT

        end_dates = df['ExitDate'].fillna(current_date)
        df['duration_months'] = ((end_dates - df['JoiningDate']).dt.days / 30.44).clip(lower=0.5)

    elif 'YearsAtCompany' in df.columns:
        # Approximate duration from tenure
        df['YearsAtCompany'] = pd.to_numeric(df['YearsAtCompany'], errors='coerce').fillna(1)
        df['duration_months'] = (df['YearsAtCompany'] * 12).clip(lower=0.5)
        if 'JoiningDate' not in df.columns:
            df['JoiningDate'] = current_date - pd.to_timedelta(df['duration_months'] * 30.44, unit='D')
        if 'ExitDate' not in df.columns:
            df['ExitDate'] = pd.NaT
        end_dates = df['ExitDate'].fillna(current_date)
    else:
        # Fallback: uniform duration
        df['duration_months'] = 12.0
        df['ExitDate'] = pd.NaT
        end_dates = pd.Series([current_date] * len(df), index=df.index)

    # ---- Event indicator ----
    if 'AttritionStatus' in df.columns:
        attrition_col = df['AttritionStatus'].astype(str).str.strip().str.lower()
        # Handle various encodings: Yes/No, 1/0, True/False, Left/Active, etc.
        df['event'] = attrition_col.isin(['yes', '1', '1.0', 'true', 'left', 'resigned',
                                           'terminated', 'voluntary', 'involuntary',
                                           'attrited', 'churned']).astype(int)
    else:
        df['event'] = 0

    # ---- Encode Gender (with flexible detection) ----
    if 'Gender' in df.columns:
        gender_lower = df['Gender'].astype(str).str.strip().str.lower()
        df['Gender_enc'] = gender_lower.isin(['male', 'm', '1', 'man']).astype(int)
    else:
        df['Gender_enc'] = 0

    # ---- Encode Overtime (for Yes/No style columns) ----
    if 'Overtime' in df.columns:
        ot_lower = df['Overtime'].astype(str).str.strip().str.lower()
        df['Overtime_enc'] = ot_lower.isin(['yes', '1', 'true', 'y']).astype(int)
    else:
        df['Overtime_enc'] = 0

    # ---- Encode StockOptions ----
    if 'StockOptions' in df.columns:
        so_lower = df['StockOptions'].astype(str).str.strip().str.lower()
        # Could be Yes/No or numeric
        if so_lower.isin(['yes', 'no', 'y', 'n', 'true', 'false']).any():
            df['StockOptions_enc'] = so_lower.isin(['yes', '1', 'true', 'y']).astype(int)
        else:
            df['StockOptions_enc'] = pd.to_numeric(df['StockOptions'], errors='coerce').fillna(0).astype(int)
    else:
        df['StockOptions_enc'] = 0

    # ---- Days since last promotion ----
    if 'LastPromotionDate' in df.columns:
        df['LastPromotionDate'] = pd.to_datetime(df['LastPromotionDate'], errors='coerce')
        ref_dates = df['ExitDate'].fillna(current_date) if 'ExitDate' in df.columns else current_date
        df['DaysSinceLastPromotion'] = (ref_dates - df['LastPromotionDate']).dt.days.fillna(
            df['duration_months'] * 30.44
        ).clip(lower=0)
    elif 'MonthsSinceLastPromotion' in df.columns:
        df['MonthsSinceLastPromotion'] = pd.to_numeric(df['MonthsSinceLastPromotion'], errors='coerce').fillna(0)
        df['DaysSinceLastPromotion'] = (df['MonthsSinceLastPromotion'] * 30.44).clip(lower=0)
    else:
        df['DaysSinceLastPromotion'] = (df['duration_months'] * 15).clip(lower=0)

    # ---- Fill / create missing numeric columns with defaults ----
    numeric_defaults = {
        'Age': 30,
        'Salary': 50000,
        'YearsAtCompany': 3,
        'PerformanceRating': 3,
        'PromotionCount': 0,
        'WorkLifeBalance': 3,
        'DistanceFromHome': 10,
        'TrainingHours': 20,
        'JobSatisfaction': 3,
        'MonthlyIncome': 4000,
        'JobLevel': 2,
        'ManagerSatisfaction': 3,
        'OvertimeDaysPerMonth': 0,
        'MonthsSinceLastPromotion': 12,
    }

    for col, default in numeric_defaults.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].fillna(df[col].median() if df[col].notna().any() else default)
        else:
            df[col] = default

    # ---- If MonthlyIncome was not in the original data, derive it from Salary ----
    # (The user's "Salary" column is the monthly salary)
    if 'MonthlyIncome' not in original_columns and 'Salary' in original_columns:
        df['MonthlyIncome'] = df['Salary']

    # ---- NO SCALING HERE — preserve original values for display ----

    # ---- Fill missing categorical columns ----
    if 'Department' not in df.columns:
        df['Department'] = 'Unknown'
    else:
        df['Department'] = df['Department'].fillna('Unknown')

    if 'JobRole' not in df.columns:
        df['JobRole'] = 'Unknown'
    else:
        df['JobRole'] = df['JobRole'].fillna('Unknown')

    if 'Gender' not in df.columns:
        df['Gender'] = 'Unknown'

    if 'Overtime' not in df.columns:
        df['Overtime'] = 'No'

    if 'AttritionStatus' not in df.columns:
        df['AttritionStatus'] = 'No'

    return df


def get_survival_data(df):
    """
    Returns feature matrix X (standardized), duration T, event E for survival models.
    Also returns the scaler for inverse transforms if needed.
    """
    df = engineer_features(df)

    T = df['duration_months'].values
    E = df['event'].values

    # ---- Build feature matrix from all available numeric + encoded columns ----
    # These are columns that should NOT be used as features
    exclude_cols = [
        'EmployeeID', 'JoiningDate', 'ExitDate', 'AttritionStatus',
        'duration_months', 'event',
        # Raw categoricals (we use their encoded versions instead)
        'Department', 'JobRole', 'Gender', 'Overtime', 'StockOptions',
        # Avoid redundant/duplicate columns
        'LastPromotionDate',
        'MonthlyIncome',  # Same as Salary in this dataset — avoid collinearity
    ]

    X_raw = df.drop(columns=[c for c in exclude_cols if c in df.columns], errors='ignore')

    # One-hot encode any remaining categorical/object columns
    cat_cols = X_raw.select_dtypes(include=['object', 'category']).columns.tolist()
    if cat_cols:
        X_raw = pd.get_dummies(X_raw, columns=cat_cols, drop_first=True, dtype=int)

    # Ensure everything is numeric
    for col in X_raw.columns:
        X_raw[col] = pd.to_numeric(X_raw[col], errors='coerce').fillna(0)

    # ---- Standardize features for model training (zero mean, unit variance) ----
    # This prevents large-scale features like Salary from dominating Cox PH
    scaler = StandardScaler()
    X_scaled_values = scaler.fit_transform(X_raw)
    X = pd.DataFrame(X_scaled_values, columns=X_raw.columns, index=X_raw.index)

    # Store employee info for display (with ORIGINAL unscaled values)
    info_cols = ['EmployeeID', 'Age', 'Gender', 'Department', 'JobRole', 'Salary',
                 'YearsAtCompany', 'PerformanceRating', 'PromotionCount',
                 'WorkLifeBalance', 'Overtime', 'DistanceFromHome', 'TrainingHours',
                 'JobSatisfaction', 'MonthlyIncome', 'JoiningDate', 'ExitDate',
                 'AttritionStatus', 'duration_months', 'event',
                 'JobLevel', 'ManagerSatisfaction', 'OvertimeDaysPerMonth',
                 'MonthsSinceLastPromotion', 'StockOptions']
    available_info_cols = [c for c in info_cols if c in df.columns]
    employee_info = df[available_info_cols].copy()

    return X, T, E, employee_info, scaler


def get_dataset_summary(df):
    """Return a summary dict of the uploaded dataset."""
    df_eng = engineer_features(df)
    total = len(df_eng)
    attrited = int(df_eng['event'].sum())
    active = total - attrited

    summary = {
        'total_employees': total,
        'attrited': attrited,
        'active': active,
        'attrition_rate': round(attrited / total * 100, 1) if total > 0 else 0,
        'avg_tenure_months': round(df_eng['duration_months'].mean(), 1),
        'departments': df_eng['Department'].nunique() if 'Department' in df_eng.columns else 0,
        'columns': list(df.columns),
        'sample_rows': df.head(5).to_dict(orient='records')
    }
    return summary
