import csv
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable

from .config import DB_PATH


EMPLOYEE_COLUMNS = [
    "Age",
    "BusinessTravel",
    "Department",
    "DistanceFromHome",
    "EducationField",
    "Gender",
    "JobRole",
    "JobLevel",
    "MonthlyIncome",
    "NumCompaniesWorked",
    "OverTime",
    "PercentSalaryHike",
    "StockOptionLevel",
    "TotalWorkingYears",
    "TrainingTimesLastYear",
    "EnvironmentSatisfaction",
    "JobSatisfaction",
    "RelationshipSatisfaction",
    "WorkLifeBalance",
    "YearsAtCompany",
    "YearsInCurrentRole",
    "YearsSinceLastPromotion",
    "YearsWithCurrManager",
    "Attrition",
]

INTEGER_COLUMNS = {
    "Age",
    "DistanceFromHome",
    "JobLevel",
    "MonthlyIncome",
    "NumCompaniesWorked",
    "PercentSalaryHike",
    "StockOptionLevel",
    "TotalWorkingYears",
    "TrainingTimesLastYear",
    "EnvironmentSatisfaction",
    "JobSatisfaction",
    "RelationshipSatisfaction",
    "WorkLifeBalance",
    "YearsAtCompany",
    "YearsInCurrentRole",
    "YearsSinceLastPromotion",
    "YearsWithCurrManager",
}


@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    typed = []
    for column in EMPLOYEE_COLUMNS:
        kind = "INTEGER" if column in INTEGER_COLUMNS else "TEXT"
        typed.append(f"{column} {kind} NOT NULL")
    with connect() as conn:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                {", ".join(typed)}
            )
            """
        )


def normalize_employee(row: dict) -> dict:
    normalized = {}
    for column in EMPLOYEE_COLUMNS:
        value = row.get(column, "")
        if column in INTEGER_COLUMNS:
            normalized[column] = int(float(value or 0))
        else:
            normalized[column] = str(value or default_value(column))
    return normalized


def default_value(column: str) -> str:
    defaults = {
        "BusinessTravel": "Travel_Rarely",
        "Department": "Research & Development",
        "EducationField": "Life Sciences",
        "Gender": "Male",
        "JobRole": "Research Scientist",
        "OverTime": "No",
        "Attrition": "No",
    }
    return defaults.get(column, "")


def row_to_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in row.keys()}


def list_employees(search: str | None = None) -> list[dict]:
    with connect() as conn:
        if search:
            term = f"%{search.lower()}%"
            rows = conn.execute(
                """
                SELECT * FROM employees
                WHERE lower(Department) LIKE ? OR lower(JobRole) LIKE ? OR lower(Gender) LIKE ?
                ORDER BY id DESC
                """,
                (term, term, term),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM employees ORDER BY id DESC").fetchall()
    return [row_to_dict(row) for row in rows]


def get_employee(employee_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()
    return row_to_dict(row) if row else None


def create_employee(data: dict) -> dict:
    normalized = normalize_employee(data)
    columns = ", ".join(EMPLOYEE_COLUMNS)
    placeholders = ", ".join("?" for _ in EMPLOYEE_COLUMNS)
    values = [normalized[column] for column in EMPLOYEE_COLUMNS]
    with connect() as conn:
        cursor = conn.execute(f"INSERT INTO employees ({columns}) VALUES ({placeholders})", values)
        employee_id = int(cursor.lastrowid)
    created = get_employee(employee_id)
    assert created is not None
    return created


def update_employee(employee_id: int, data: dict) -> dict | None:
    if get_employee(employee_id) is None:
        return None
    normalized = normalize_employee(data)
    assignments = ", ".join(f"{column} = ?" for column in EMPLOYEE_COLUMNS)
    values = [normalized[column] for column in EMPLOYEE_COLUMNS] + [employee_id]
    with connect() as conn:
        conn.execute(f"UPDATE employees SET {assignments} WHERE id = ?", values)
    return get_employee(employee_id)


def delete_employee(employee_id: int) -> bool:
    with connect() as conn:
        cursor = conn.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
    return cursor.rowcount > 0


def import_csv(path: Path) -> int:
    count = 0
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if not row:
                continue
            create_employee(row)
            count += 1
    return count


def seed_if_empty(rows: Iterable[dict]) -> None:
    with connect() as conn:
        total = conn.execute("SELECT COUNT(*) AS total FROM employees").fetchone()["total"]
    if total == 0:
        for row in rows:
            create_employee(row)
