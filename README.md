# AI Employee Attrition Analytics Platform

A full-stack HR analytics system for predicting employee attrition risk, explaining the reasons behind predictions, managing employee records, and generating downloadable reports.

## Features

- HR admin login with signed bearer tokens
- Dashboard metrics for employee count, at-risk employees, salary, satisfaction, department mix, and attrition rate
- Employee CRUD with CSV upload/import
- Attrition prediction API with explainable reasons and retention recommendations
- Analytics endpoints for department, gender, overtime, salary, age, satisfaction, promotion, work-life balance, and tenure views
- PDF, CSV, and Excel-compatible report downloads
- React dashboard with charts and employee workflows
- Scikit-learn model training with Logistic Regression, Decision Tree, and Random Forest
- Optional SHAP/XGBoost/CatBoost/LightGBM dependency hooks through `requirements.txt`
- Docker Compose for backend, frontend, and PostgreSQL-ready deployment

## Quick Start

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m ml.train
uvicorn app.main:app --reload --port 8000
```

The backend defaults to SQLite at `backend/attrition.db`, so it runs without PostgreSQL. Use `DATABASE_URL` if you want to point it at another database later.

Default login:

- Email: `admin@hr.local`
- Password: `admin123`

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL, normally `http://localhost:5173`.

## Dataset

Place the IBM HR Analytics CSV at:

```text
backend/dataset/WA_Fn-UseC_-HR-Employee-Attrition.csv
```

If the file is missing, `python -m ml.train` creates a synthetic IBM-like dataset so the app remains runnable for demos and development.

## API

Interactive docs are available after starting the backend:

```text
http://localhost:8000/docs
```

## Project Structure

```text
backend/
  app/
    main.py
    auth.py
    database.py
    schemas.py
    services/
  dataset/
  ml/
    train.py
    predict.py
  saved_models/
  tests/
frontend/
  src/
    components/
    pages/
    services/
docker-compose.yml
```

## Notes

This project is designed as a practical internship-grade baseline. For production, add stronger password storage, role management, audit logs, hosted PostgreSQL migrations, and bias/fairness review before using attrition scores in HR decisions.
