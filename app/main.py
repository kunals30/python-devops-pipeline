from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Python DevOps Demo", version="1.0.0")


class CalculationRequest(BaseModel):
    a: float
    b: float


@app.get("/")
def home():
    return {"message": "Python CI/CD pipeline is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/add")
def add_numbers(request: CalculationRequest):
    return {"result": request.a + request.b}
