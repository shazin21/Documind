"""
DocuMind AI — Multi-Step Pipeline Evaluation CLI
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Import main CLI implementation from root scripts
root_script = Path(__file__).resolve().parent.parent.parent / "scripts" / "evaluate_pipeline_steps.py"
if root_script.exists():
    with open(root_script, "r", encoding="utf-8") as f:
        code = f.read()
    exec(code)
else:
    from app.services.evaluation_service import evaluation_service
    print("Execute via root scripts/evaluate_pipeline_steps.py")
