"""
Dataset Routes Controller
=========================
Handles dataset file uploads (CSV/Excel), preset loading (IBM/Healthcare),
and synthetic dataset generation.
"""

import os
import logging
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.state import state, UPLOAD_FOLDER, json_safe
from backend.schemas import PresetRequest, GenerateSampleRequest
from core.data_processor import validate_dataset, get_dataset_summary
from core.dataset_generator import generate_dataset as gen_data

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Dataset Operations"])


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Upload custom CSV or Excel dataset file."""
    try:
        contents = await file.read()
        filename = file.filename or "uploaded_data.csv"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        with open(filepath, "wb") as f:
            f.write(contents)

        if filename.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(filepath)
        else:
            df = pd.read_csv(filepath)

        valid, msg, mapped_df = validate_dataset(df)
        if not valid:
            raise HTTPException(status_code=400, detail=msg)

        state['df'] = mapped_df
        summary = get_dataset_summary(mapped_df)
        return json_safe({
            "success": True,
            "message": f"Dataset uploaded: {len(mapped_df)} rows, {len(mapped_df.columns)} columns. {msg}",
            "summary": summary
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/load-preset")
def load_preset(req: PresetRequest):
    """Loads pre-packaged benchmark datasets (IBM HR Analytics or Healthcare Attrition)."""
    try:
        preset_name = req.preset.lower()
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        if preset_name == "healthcare":
            filepath = os.path.join(root_dir, 'Datasets', 'HealthCare-Dataset', 'watson_healthcare_modified.csv')
            dname = "Healthcare Employee Attrition (Validation Set, n=1,676)"
        else:
            filepath = os.path.join(root_dir, 'Datasets', 'IBM-Dataset', 'WA_Fn-UseC_-HR-Employee-Attrition.csv')
            dname = "IBM HR Analytics Employee Attrition (Primary Set, n=1,470)"

        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail=f"Preset file not found: {filepath}")

        df = pd.read_csv(filepath)
        valid, msg, mapped_df = validate_dataset(df)
        if not valid:
            raise HTTPException(status_code=400, detail=msg)

        state['df'] = mapped_df
        summary = get_dataset_summary(mapped_df)
        return json_safe({
            "success": True,
            "message": f"Loaded {dname}",
            "dataset_name": dname,
            "summary": summary
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Load preset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-sample")
def generate_sample_dataset(req: GenerateSampleRequest):
    """Generates and loads a synthetic HR survival dataset."""
    try:
        df = gen_data(n=req.n_employees)
        valid, msg, mapped_df = validate_dataset(df)
        if not valid:
            raise HTTPException(status_code=400, detail=msg)

        state['df'] = mapped_df
        summary = get_dataset_summary(mapped_df)
        return json_safe({
            "success": True,
            "message": f"Generated synthetic dataset with {len(mapped_df)} employee records.",
            "summary": summary
        })
    except Exception as e:
        logger.error(f"Generate sample error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
