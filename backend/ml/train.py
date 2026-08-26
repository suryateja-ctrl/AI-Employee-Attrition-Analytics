import csv
import random
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

from app.config import DATASET_DIR, MODEL_DIR
from app.database import EMPLOYEE_COLUMNS, INTEGER_COLUMNS

DATASET_PATH = DATASET_DIR / "WA_Fn-UseC_-HR-Employee-Attrition.csv"
MODEL_PATH = MODEL_DIR / "attrition_model.joblib"
METRICS_PATH = MODEL_DIR / "metrics.csv"

FEATURE_COLUMNS = [column for column in EMPLOYEE_COLUMNS if column != "Attrition"]
def make_synthetic_dataset(path: Path, rows: int = 900) -> None:
    random.seed(42)
    departments = ["Research & Development", "Sales", "Human Resources"]
    roles = {
        "Research & Development": ["Research Scientist", "Laboratory Technician", "Manufacturing Director", "Healthcare Representative"],
        "Sales": ["Sales Executive", "Sales Representative", "Manager"],
        "Human Resources": ["Human Resources", "Manager"],
    }
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=EMPLOYEE_COLUMNS)
        writer.writeheader()
        for _ in range(rows):
            department = random.choices(departments, weights=[62, 31, 7])[0]
            age = random.randint(21, 60)
            years_at_company = max(0, min(age - 18, int(random.expovariate(1 / 7))))
            overtime = random.choices(["Yes", "No"], weights=[28, 72])[0]
            job_satisfaction = random.randint(1, 4)
            environment = random.randint(1, 4)
            work_life = random.randint(1, 4)
            promotion_gap = random.randint(0, min(15, max(1, years_at_company)))
            income = random.randint(2400, 20000)
            distance = random.randint(1, 30)
            risk = 0
            risk += 0.23 if overtime == "Yes" else -0.06
            risk += 0.16 if job_satisfaction <= 2 else -0.08
            risk += 0.12 if environment <= 2 else -0.05
            risk += 0.09 if work_life <= 2 else -0.04
            risk += 0.09 if distance > 15 else 0
            risk += 0.08 if promotion_gap >= 4 else 0
            risk += 0.08 if income < 5000 else -0.04
            risk += 0.05 if years_at_company < 2 else 0
            attrition = "Yes" if random.random() < max(0.05, min(0.78, 0.16 + risk)) else "No"
            writer.writerow(
                {
                    "Age": age,
                    "BusinessTravel": random.choices(["Travel_Rarely", "Travel_Frequently", "Non-Travel"], weights=[72, 18, 10])[0],
                    "Department": department,
                    "DistanceFromHome": distance,
                    "EducationField": random.choice(["Life Sciences", "Medical", "Marketing", "Technical Degree", "Human Resources", "Other"]),
                    "Gender": random.choice(["Male", "Female"]),
                    "JobRole": random.choice(roles[department]),
                    "JobLevel": random.randint(1, 5),
                    "MonthlyIncome": income,
                    "NumCompaniesWorked": random.randint(0, 8),
                    "OverTime": overtime,
                    "PercentSalaryHike": random.randint(11, 25),
                    "StockOptionLevel": random.randint(0, 3),
                    "TotalWorkingYears": max(years_at_company, random.randint(0, max(1, age - 18))),
                    "TrainingTimesLastYear": random.randint(0, 6),
                    "EnvironmentSatisfaction": environment,
                    "JobSatisfaction": job_satisfaction,
                    "RelationshipSatisfaction": random.randint(1, 4),
                    "WorkLifeBalance": work_life,
                    "YearsAtCompany": years_at_company,
                    "YearsInCurrentRole": random.randint(0, max(1, years_at_company)),
                    "YearsSinceLastPromotion": promotion_gap,
                    "YearsWithCurrManager": random.randint(0, max(1, years_at_company)),
                    "Attrition": attrition,
                }
            )


def load_rows(path: Path) -> tuple[list[dict], list[int]]:
    features = []
    target = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            record = {}
            for column in FEATURE_COLUMNS:
                value = row.get(column, "")
                record[column] = int(float(value or 0)) if column in INTEGER_COLUMNS else str(value or "")
            features.append(record)
            target.append(1 if row.get("Attrition") == "Yes" else 0)
    return features, target


def build_pipeline(model) -> Pipeline:
    return Pipeline([("vectorizer", DictVectorizer(sparse=False)), ("model", model)])


def train() -> dict:
    if not DATASET_PATH.exists():
        make_synthetic_dataset(DATASET_PATH)
    x, y = load_rows(DATASET_PATH)
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.22, random_state=42, stratify=y)
    candidates = {
        "Logistic Regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "Decision Tree": DecisionTreeClassifier(max_depth=7, random_state=42, class_weight="balanced"),
        "Random Forest": RandomForestClassifier(n_estimators=180, random_state=42, class_weight="balanced", max_depth=9),
    }
    results = []
    best_name = ""
    best_pipeline = None
    best_auc = -1.0
    for name, model in candidates.items():
        pipeline = build_pipeline(model)
        pipeline.fit(x_train, y_train)
        predictions = pipeline.predict(x_test)
        probabilities = pipeline.predict_proba(x_test)[:, 1]
        metrics = {
            "model": name,
            "accuracy": accuracy_score(y_test, predictions),
            "precision": precision_score(y_test, predictions, zero_division=0),
            "recall": recall_score(y_test, predictions, zero_division=0),
            "f1": f1_score(y_test, predictions, zero_division=0),
            "roc_auc": roc_auc_score(y_test, probabilities),
        }
        results.append(metrics)
        if metrics["roc_auc"] > best_auc:
            best_auc = metrics["roc_auc"]
            best_name = name
            best_pipeline = pipeline
    assert best_pipeline is not None
    joblib.dump({"model_name": best_name, "pipeline": best_pipeline, "features": FEATURE_COLUMNS}, MODEL_PATH)
    with METRICS_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["model", "accuracy", "precision", "recall", "f1", "roc_auc"])
        writer.writeheader()
        writer.writerows(results)
    return {"best_model": best_name, "metrics": results, "dataset": str(DATASET_PATH)}


if __name__ == "__main__":
    summary = train()
    print(summary)
