"""
Backend Pydantic Data Schemas
=============================
Defines strict type models for incoming API request payloads.
"""

from typing import Optional
from pydantic import BaseModel, Field


class PresetRequest(BaseModel):
    preset: str = Field(default="ibm", description="Preset dataset identifier: 'ibm' or 'healthcare'")


class GenerateSampleRequest(BaseModel):
    n_employees: int = Field(default=500, ge=50, le=10000, description="Number of synthetic employee records to generate")


class AgentRunRequest(BaseModel):
    employee_id: str = Field(..., description="Target Employee ID to execute the 5-agent pipeline for")


class AgentFeedbackRequest(BaseModel):
    employee_id: str = Field(..., description="Target Employee ID")
    action: str = Field(..., description="Retention intervention arm that was applied")
    outcome: str = Field(..., description="'retained' (+1.0 reward) or 'churned' (-1.0 reward)")
