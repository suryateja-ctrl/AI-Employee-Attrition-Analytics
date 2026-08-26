from pathlib import Path

import joblib

from app.config import MODEL_DIR
from app.database import INTEGER_COLUMNS

MODEL_PATH = MODEL_DIR / "attrition_model.joblib"


class AttritionPredictor:
    def __init__(self, model_path: Path | None = MODEL_PATH):
        self.model_path = model_path
        self.bundle = None
        if model_path and model_path.exists():
            self.bundle = joblib.load(model_path)

    @property
    def available(self) -> bool:
        return self.bundle is not None

    def predict(self, employee: dict) -> dict:
        if self.bundle:
            features = self.bundle["features"]
            row = {column: self._coerce(employee.get(column), column) for column in features}
            probability = float(self.bundle["pipeline"].predict_proba([row])[0][1])
        else:
            probability = self._heuristic_probability(employee)
        reasons = self.reasons(employee)
        return {
            "probability": round(probability, 4),
            "prediction": "Likely to Leave" if probability >= 0.5 else "Likely to Stay",
            "risk_level": self.risk_level(probability),
            "reasons": reasons,
            "recommendations": self.recommendations(employee, reasons),
        }

    def _coerce(self, value, column: str):
        return int(float(value or 0)) if column in INTEGER_COLUMNS else str(value or "")

    def _heuristic_probability(self, employee: dict) -> float:
        score = 0.15
        score += 0.2 if employee.get("OverTime") == "Yes" else -0.04
        score += 0.14 if int(employee.get("JobSatisfaction", 4)) <= 2 else -0.05
        score += 0.1 if int(employee.get("EnvironmentSatisfaction", 4)) <= 2 else -0.04
        score += 0.1 if int(employee.get("WorkLifeBalance", 4)) <= 2 else -0.03
        score += 0.08 if int(employee.get("DistanceFromHome", 0)) > 15 else 0
        score += 0.08 if int(employee.get("YearsSinceLastPromotion", 0)) >= 4 else 0
        score += 0.07 if int(employee.get("MonthlyIncome", 999999)) < 5000 else -0.03
        score += 0.04 if int(employee.get("YearsAtCompany", 5)) <= 1 else 0
        return max(0.03, min(0.95, score))

    def reasons(self, employee: dict) -> list[str]:
        checks = [
            ("Frequent overtime workload", employee.get("OverTime") == "Yes"),
            ("Low job satisfaction", int(employee.get("JobSatisfaction", 4)) <= 2),
            ("Low environment satisfaction", int(employee.get("EnvironmentSatisfaction", 4)) <= 2),
            ("Weak work-life balance", int(employee.get("WorkLifeBalance", 4)) <= 2),
            ("Long distance from home", int(employee.get("DistanceFromHome", 0)) > 15),
            ("No recent promotion", int(employee.get("YearsSinceLastPromotion", 0)) >= 4),
            ("Low monthly income compared with peers", int(employee.get("MonthlyIncome", 999999)) < 5000),
            ("Short tenure and higher early-exit risk", int(employee.get("YearsAtCompany", 5)) <= 1),
            ("No stock option benefit", int(employee.get("StockOptionLevel", 0)) == 0),
        ]
        reasons = [label for label, applies in checks if applies]
        return reasons[:5] or ["No major risk driver detected"]

    def recommendations(self, employee: dict, reasons: list[str]) -> list[str]:
        recommendations = []
        reason_text = " ".join(reasons).lower()
        if "income" in reason_text:
            recommendations.append("Review compensation band and salary growth plan.")
        if "promotion" in reason_text:
            recommendations.append("Schedule a career progression and promotion discussion.")
        if "overtime" in reason_text or "work-life" in reason_text:
            recommendations.append("Reduce overtime load and rebalance work allocation.")
        if "satisfaction" in reason_text:
            recommendations.append("Plan a manager one-on-one to understand role and workplace concerns.")
        if "distance" in reason_text:
            recommendations.append("Consider flexible work, remote days, or location support.")
        if "tenure" in reason_text:
            recommendations.append("Assign mentorship and a 30-60-90 day engagement plan.")
        if not recommendations:
            recommendations.append("Maintain engagement through regular check-ins and recognition.")
        return recommendations[:5]

    def risk_level(self, probability: float) -> str:
        if probability >= 0.75:
            return "Critical"
        if probability >= 0.5:
            return "High"
        if probability >= 0.3:
            return "Medium"
        return "Low"
