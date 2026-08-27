import os
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, Query, BackgroundTasks

from evaluation.run_evaluation import run_evaluation

router = APIRouter(prefix="/api/evaluation", tags=["Evaluation"])

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
EVAL_FILE = os.path.join(BASE_DIR, "evaluation", "evaluation_results.json")


@router.get("/latest")
async def get_latest_evaluation() -> Dict[str, Any]:
    if not os.path.exists(EVAL_FILE):
        return run_evaluation(num_samples=10000, output_file=os.path.join("/tmp", "evaluation_results.json") if os.environ.get("VERCEL") else EVAL_FILE)

    try:
        with open(EVAL_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception:
        return run_evaluation(num_samples=10000, output_file=os.path.join("/tmp", "evaluation_results.json") if os.environ.get("VERCEL") else EVAL_FILE)


@router.post("/run")
async def trigger_evaluation_run(
    samples: int = Query(5000, ge=100, le=20000, description="Sample size for evaluation")
) -> Dict[str, Any]:
    results = run_evaluation(num_samples=samples, output_file=EVAL_FILE)
    return {
        "status": "success",
        "message": f"Successfully evaluated {samples:,} payment risk events against Baseline.",
        "results": results
    }
