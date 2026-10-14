"""
Standalone script to display and evaluate all model metrics directly from the command line.
Usage:
    python evaluate_metrics.py
"""

import os
import sys
import json
import pandas as pd


PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def main():
    metrics_path = os.path.join(PROJECT_ROOT, "outputs", "saved_models", "evaluation_metrics.json")
    cv_path = os.path.join(PROJECT_ROOT, "outputs", "saved_models", "cv_results.json")

    print("\n" + "=" * 70)
    print("NEXUS AI — MODEL EVALUATION & PERFORMANCE METRICS")
    print("=" * 70)

    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            metrics = json.load(f)

        summary_data = [
            ["Concordance Index (Train C-Index)", f"{metrics['cox']['train_c_index']:.4f}", f"{metrics['rsf']['train_c_index']:.4f}"],
            ["Concordance Index (Test C-Index)", f"{metrics['cox']['test_c_index']:.4f}", f"{metrics['rsf']['test_c_index']:.4f}"],
            ["Integrated Brier Score (Train IBS)", f"{metrics['cox']['train_ibs']:.4f}", f"{metrics['rsf']['train_ibs']:.4f}"],
            ["Integrated Brier Score (Test IBS)", f"{metrics['cox']['test_ibs']:.4f}", f"{metrics['rsf']['test_ibs']:.4f}"],
            ["Training Time (seconds)", f"{metrics['cox']['train_time']:.2f}s", f"{metrics['rsf']['train_time']:.2f}s"],
        ]

        print("\n[1] Overall Model Metrics Comparison:")
        print(pd.DataFrame(summary_data, columns=["Evaluation Metric", "Cox Proportional Hazards", "Random Survival Forest"]).to_string(index=False))

    if os.path.exists(cv_path):
        with open(cv_path, "r") as f:
            cv = json.load(f)

        cv_data = [
            ["Cox PH", f"{cv['cox']['mean']:.4f}", f"{cv['cox']['std']:.4f}", str(cv['cox']['fold_scores'])],
            ["Random Survival Forest", f"{cv['rsf']['mean']:.4f}", f"{cv['rsf']['std']:.4f}", str(cv['rsf']['fold_scores'])],
        ]
        print("\n[2] 5-Fold Stratified Cross-Validation (C-Index):")
        print(pd.DataFrame(cv_data, columns=["Model", "CV Mean", "CV Std", "Individual Fold Scores"]).to_string(index=False))

    if os.path.exists(metrics_path):
        hrs = metrics.get('cox', {}).get('hazard_ratios', [])
        if hrs:
            print("\n[3] Top 8 Statistically Significant Risk Factors (Cox PH Hazard Ratios):")
            top_hrs = []
            for h in hrs[:8]:
                top_hrs.append([
                    h['feature'],
                    f"{h['hazard_ratio']:.4f}",
                    f"{h['coefficient']:.4f}",
                    f"{h['p_value']:.4e}",
                    h['significance'],
                    h['interpretation'][:60] + "..."
                ])
            hr_df = pd.DataFrame(top_hrs, columns=["Feature", "Hazard Ratio", "Coeff", "P-value", "Significance", "Interpretation"])
            print(hr_df.to_string(index=False))

    print("\n" + "=" * 70)
    print("Pre-computed files located in: outputs/saved_models/")
    print("Interactive Jupyter Notebook available at: model_evaluation.ipynb")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
