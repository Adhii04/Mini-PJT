"""
Dual Dataset Benchmarking Module
================================
Runs paper evaluation across Primary (IBM HR Analytics) and Validation (Healthcare Employee Attrition) datasets.
"""

import os
import pandas as pd
import logging
from models.data_processor import validate_dataset, get_survival_data
from models.ablation import run_ablation_study

logger = logging.getLogger(__name__)

IBM_PATH = r"Datasets/IBM-Dataset/WA_Fn-UseC_-HR-Employee-Attrition.csv"
HEALTHCARE_PATH = r"Datasets/HealthCare-Dataset/watson_healthcare_modified.csv"


def run_benchmark_on_dataset(dataset_path, dataset_name="IBM HR Analytics"):
    """Run full pipeline and ablation study on a specified dataset file."""
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    logger.info(f"Loading {dataset_name} from {dataset_path}...")
    df = pd.read_csv(dataset_path)
    valid, msg, mapped_df = validate_dataset(df)
    
    if not valid:
        raise ValueError(f"Dataset validation failed for {dataset_name}: {msg}")

    X, T, E, info, scaler = get_survival_data(mapped_df)
    logger.info(f"Loaded {dataset_name}: n={len(X)} rows, {len(X.columns)} features.")

    ablation_results = run_ablation_study(X, T, E, info)
    ablation_results['dataset_name'] = dataset_name
    return ablation_results


def run_dual_dataset_benchmarks():
    """Run ablation benchmarks across both IBM and Healthcare datasets."""
    results = {}
    
    # 1. Primary: IBM HR Analytics
    if os.path.exists(IBM_PATH):
        results['ibm'] = run_benchmark_on_dataset(IBM_PATH, "Primary Dataset (IBM HR Analytics, n=1,470)")

    # 2. Validation: Healthcare Employee Attrition
    if os.path.exists(HEALTHCARE_PATH):
        results['healthcare'] = run_benchmark_on_dataset(HEALTHCARE_PATH, "Validation Dataset (Healthcare Attrition, n=1,676)")

    return results
