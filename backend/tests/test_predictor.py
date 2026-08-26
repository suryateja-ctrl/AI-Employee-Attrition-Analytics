from ml.predict import AttritionPredictor


def test_predictor_returns_reasons_and_recommendations():
    predictor = AttritionPredictor(model_path=None)
    employee = {
        "OverTime": "Yes",
        "JobSatisfaction": 1,
        "EnvironmentSatisfaction": 2,
        "WorkLifeBalance": 1,
        "DistanceFromHome": 22,
        "YearsSinceLastPromotion": 6,
        "MonthlyIncome": 3200,
        "YearsAtCompany": 1,
        "StockOptionLevel": 0,
    }
    result = predictor.predict(employee)
    assert result["probability"] > 0.5
    assert result["prediction"] == "Likely to Leave"
    assert result["reasons"]
    assert result["recommendations"]
