from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app import database
from app.auth import create_token, current_user, verify_credentials
from app.config import DATASET_DIR
from app.schemas import DashboardMetrics, Employee, EmployeeIn, LoginRequest, PredictionResponse, TokenResponse
from app.services.analytics import analytics_payload, dashboard_metrics
from app.services.reports import employees_csv, pdf_report
from ml.predict import AttritionPredictor
from ml.train import DATASET_PATH, make_synthetic_dataset
import os

app = FastAPI(title="AI Employee Attrition Analytics Platform", version="1.0.0")



FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

predictor = AttritionPredictor()


@app.on_event("startup")
def startup() -> None:
    database.init_db()
    if not DATASET_PATH.exists():
        make_synthetic_dataset(DATASET_PATH, rows=120)
    database.seed_if_empty(_load_seed_rows(DATASET_PATH))


def _load_seed_rows(path: Path) -> list[dict]:
    import csv

    rows = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            rows.append(row)
            if len(rows) >= 120:
                break
    return rows


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model_loaded": predictor.available}


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    if not verify_credentials(payload.email, payload.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=create_token(payload.email))


@app.get("/dashboard", response_model=DashboardMetrics)
def dashboard(_: dict = Depends(current_user)) -> dict:
    return dashboard_metrics(database.list_employees(), predictor)


@app.get("/employees", response_model=list[Employee])
def employees(search: str | None = None, _: dict = Depends(current_user)) -> list[dict]:
    return database.list_employees(search)


@app.post("/employees", response_model=Employee)
def add_employee(payload: EmployeeIn, _: dict = Depends(current_user)) -> dict:
    return database.create_employee(payload.model_dump())


@app.get("/employees/{employee_id}", response_model=Employee)
def employee_detail(employee_id: int, _: dict = Depends(current_user)) -> dict:
    employee = database.get_employee(employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@app.put("/employees/{employee_id}", response_model=Employee)
def edit_employee(employee_id: int, payload: EmployeeIn, _: dict = Depends(current_user)) -> dict:
    employee = database.update_employee(employee_id, payload.model_dump())
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@app.delete("/employees/{employee_id}")
def remove_employee(employee_id: int, _: dict = Depends(current_user)) -> dict:
    if not database.delete_employee(employee_id):
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"deleted": True}


@app.post("/employees/upload")
async def upload_employees(file: UploadFile = File(...), _: dict = Depends(current_user)) -> dict:
    suffix = Path(file.filename or "upload.csv").suffix or ".csv"
    with NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        temp.write(await file.read())
        temp_path = Path(temp.name)
    try:
        count = database.import_csv(temp_path)
    finally:
        temp_path.unlink(missing_ok=True)
    return {"imported": count}


@app.post("/predict", response_model=PredictionResponse)
def predict_employee(payload: EmployeeIn, _: dict = Depends(current_user)) -> dict:
    return predictor.predict(payload.model_dump())


@app.post("/predict/{employee_id}", response_model=PredictionResponse)
def predict_existing_employee(employee_id: int, _: dict = Depends(current_user)) -> dict:
    employee = database.get_employee(employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    result = predictor.predict(employee)
    result["employee_id"] = employee_id
    return result


@app.get("/analytics")
def analytics(_: dict = Depends(current_user)) -> dict:
    return analytics_payload(database.list_employees())


@app.get("/reports/csv")
def csv_download(_: dict = Depends(current_user)) -> Response:
    content = employees_csv(database.list_employees())
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=employee_attrition_report.csv"},
    )


@app.get("/reports/excel")
def excel_download(_: dict = Depends(current_user)) -> Response:
    content = employees_csv(database.list_employees())
    return Response(
        content=content,
        media_type="application/vnd.ms-excel",
        headers={"Content-Disposition": "attachment; filename=employee_attrition_report.xls"},
    )


@app.get("/reports/pdf")
def pdf_download(_: dict = Depends(current_user)) -> Response:
    employees_list = database.list_employees()
    metrics = dashboard_metrics(employees_list, predictor)
    return Response(
        content=pdf_report(metrics, employees_list),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=employee_attrition_report.pdf"},
    )
