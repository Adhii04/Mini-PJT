"""
Multi-Agent Execution Route Controller
======================================
Coordinates execution of the 5-Agent Autonomous Retention Pipeline and
ingests 30-day intervention feedback.
"""

import logging
from fastapi import APIRouter, HTTPException

from backend.state import state, json_safe
from backend.schemas import AgentRunRequest, AgentFeedbackRequest
from agents.pipeline import NexusMultiAgentPipeline
from agents.feedback import FeedbackAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agent", tags=["Autonomous Multi-Agent System"])


@router.post("/run")
def run_agent_pipeline(req: AgentRunRequest):
    """Executes the full 5-Agent Autonomous Retention Pipeline for an individual employee."""
    try:
        if state['predictions'] is None:
            raise HTTPException(status_code=400, detail="Please train the pipeline first.")

        preds = state['predictions']
        emp_row = preds[preds['EmployeeID'].astype(str) == str(req.employee_id)]
        emp_record = emp_row.iloc[0].to_dict() if len(emp_row) > 0 else preds.iloc[0].to_dict()

        pipeline = NexusMultiAgentPipeline()
        agent_res = pipeline.run_full_pipeline_for_employee(emp_record)

        return json_safe({
            "success": True,
            "agent_results": agent_res
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
def log_agent_feedback(req: AgentFeedbackRequest):
    """Logs 30-day intervention outcome and updates LinUCB Contextual Bandit policy parameters."""
    try:
        if state['predictions'] is None:
            raise HTTPException(status_code=400, detail="Pipeline not trained yet.")

        preds = state['predictions']
        emp_row = preds[preds['EmployeeID'].astype(str) == str(req.employee_id)]
        emp_record = emp_row.iloc[0].to_dict() if len(emp_row) > 0 else preds.iloc[0].to_dict()

        fa = FeedbackAgent()
        res = fa.process(emp_record, req.action, req.outcome)

        return json_safe({
            "success": True,
            "feedback_result": res
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
