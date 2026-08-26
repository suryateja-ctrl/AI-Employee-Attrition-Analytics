from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EmployeeIn(BaseModel):
    Age: int = Field(ge=18, le=70)
    BusinessTravel: str = "Travel_Rarely"
    Department: str
    DistanceFromHome: int = Field(ge=1, le=40)
    EducationField: str = "Life Sciences"
    Gender: str
    JobRole: str
    JobLevel: int = Field(ge=1, le=5)
    MonthlyIncome: int = Field(ge=1000)
    NumCompaniesWorked: int = Field(ge=0, le=15)
    OverTime: str
    PercentSalaryHike: int = Field(ge=0, le=40)
    StockOptionLevel: int = Field(ge=0, le=3)
    TotalWorkingYears: int = Field(ge=0, le=50)
    TrainingTimesLastYear: int = Field(ge=0, le=10)
    EnvironmentSatisfaction: int = Field(ge=1, le=4)
    JobSatisfaction: int = Field(ge=1, le=4)
    RelationshipSatisfaction: int = Field(ge=1, le=4)
    WorkLifeBalance: int = Field(ge=1, le=4)
    YearsAtCompany: int = Field(ge=0, le=50)
    YearsInCurrentRole: int = Field(ge=0, le=40)
    YearsSinceLastPromotion: int = Field(ge=0, le=25)
    YearsWithCurrManager: int = Field(ge=0, le=40)
    Attrition: str = "No"


class Employee(EmployeeIn):
    id: int


class PredictionResponse(BaseModel):
    employee_id: int | None = None
    probability: float
    prediction: str
    risk_level: str
    reasons: list[str]
    recommendations: list[str]


class DashboardMetrics(BaseModel):
    total_employees: int
    employees_at_risk: int
    average_salary: float
    average_satisfaction: float
    departments: dict[str, int]
    attrition_rate: float
