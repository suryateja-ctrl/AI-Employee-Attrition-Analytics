from collections import Counter, defaultdict

from ml.predict import AttritionPredictor


def dashboard_metrics(employees: list[dict], predictor: AttritionPredictor) -> dict:
    total = len(employees)
    if total == 0:
        return {
            "total_employees": 0,
            "employees_at_risk": 0,
            "average_salary": 0,
            "average_satisfaction": 0,
            "departments": {},
            "attrition_rate": 0,
        }
    predictions = [predictor.predict(employee)["probability"] for employee in employees]
    return {
        "total_employees": total,
        "employees_at_risk": sum(probability >= 0.5 for probability in predictions),
        "average_salary": round(sum(int(e["MonthlyIncome"]) for e in employees) / total, 2),
        "average_satisfaction": round(sum(int(e["JobSatisfaction"]) for e in employees) / total, 2),
        "departments": dict(Counter(e["Department"] for e in employees)),
        "attrition_rate": round(sum(e["Attrition"] == "Yes" for e in employees) / total, 4),
    }


def grouped_attrition(employees: list[dict], field: str) -> list[dict]:
    grouped = defaultdict(lambda: {"total": 0, "attrition": 0})
    for employee in employees:
        key = str(employee.get(field, "Unknown"))
        grouped[key]["total"] += 1
        grouped[key]["attrition"] += 1 if employee.get("Attrition") == "Yes" else 0
    return [
        {
            "label": key,
            "total": value["total"],
            "attrition": value["attrition"],
            "rate": round(value["attrition"] / value["total"], 4) if value["total"] else 0,
        }
        for key, value in sorted(grouped.items())
    ]


def histogram(employees: list[dict], field: str, bucket_size: int) -> list[dict]:
    buckets = defaultdict(int)
    for employee in employees:
        value = int(employee.get(field, 0))
        start = value // bucket_size * bucket_size
        buckets[f"{start}-{start + bucket_size - 1}"] += 1
    return [{"label": label, "count": count} for label, count in sorted(buckets.items(), key=lambda item: int(item[0].split("-")[0]))]


def analytics_payload(employees: list[dict]) -> dict:
    return {
        "attrition_by_department": grouped_attrition(employees, "Department"),
        "attrition_by_gender": grouped_attrition(employees, "Gender"),
        "overtime_vs_attrition": grouped_attrition(employees, "OverTime"),
        "job_satisfaction": grouped_attrition(employees, "JobSatisfaction"),
        "work_life_balance": grouped_attrition(employees, "WorkLifeBalance"),
        "promotion_analysis": grouped_attrition(employees, "YearsSinceLastPromotion"),
        "age_distribution": histogram(employees, "Age", 5),
        "income_distribution": histogram(employees, "MonthlyIncome", 2500),
        "years_at_company": histogram(employees, "YearsAtCompany", 3),
    }
