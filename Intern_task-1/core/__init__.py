"""
Core Package Initialization
===========================
Provides core dataset ingestion, validation, serialization, and report generation utilities.
"""

from core.data_processor import validate_dataset, get_survival_data, get_dataset_summary
from core.dataset_generator import generate_dataset
from core.persistence import save_models, load_models
from core.report_generator import generate_evaluation_report

__all__ = [
    'validate_dataset',
    'get_survival_data',
    'get_dataset_summary',
    'generate_dataset',
    'save_models',
    'load_models',
    'generate_evaluation_report',
]
