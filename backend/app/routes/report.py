import os
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import sys

# Ensure backend root is in sys.path to import generate_report_pdf
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from generate_report_pdf import generate_pdf_from_payload

router = APIRouter(prefix="/reports", tags=["Report Generation"])

def remove_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"Failed to remove temp file {path}: {e}")

@router.post("/investigation")
async def generate_investigation_report(payload: Dict[str, Any], background_tasks: BackgroundTasks):
    try:
        pdf_path = generate_pdf_from_payload(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=500, detail="PDF was not generated.")

    # Schedule the generated PDF to be deleted after the response is sent
    background_tasks.add_task(remove_file, pdf_path)
    
    filename = os.path.basename(pdf_path)
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=filename
    )
