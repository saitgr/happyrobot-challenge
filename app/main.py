from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
import pandas as pd
from datetime import datetime
import os

app = FastAPI()

API_KEY = os.getenv("API_KEY", "dev-key")


def validate_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


class CarrierRequest(BaseModel):
    mc_number: str


class LoadSearchRequest(BaseModel):
    origin: str | None = None
    destination: str | None = None
    equipment_type: str | None = None


class OfferEvaluationRequest(BaseModel):
    load_id: str
    loadboard_rate: float
    carrier_offer: float
    round_number: int


class CallLogRequest(BaseModel):
    mc_number: str
    eligible: bool
    load_id: str | None = None
    initial_rate: float | None = None
    carrier_offer: float | None = None
    final_rate: float | None = None
    negotiation_rounds: int = 0
    outcome: str
    sentiment: str
    transferred_to_rep: bool = False
    summary: str


@app.get("/")
def root():
    return {"message": "HappyRobot challenge API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/loads")
def get_loads(_: str = Depends(validate_api_key)):
    df = pd.read_csv("data/loads.csv")
    return df.to_dict(orient="records")


@app.get("/call-logs")
def get_call_logs(_: str = Depends(validate_api_key)):
    if not os.path.exists("data/call_logs.csv"):
        return {"count": 0, "logs": []}

    df = pd.read_csv("data/call_logs.csv")
    return {
        "count": len(df),
        "logs": df.to_dict(orient="records")
    }


@app.post("/verify-carrier")
def verify_carrier(request: CarrierRequest, _: str = Depends(validate_api_key)):
    approved_mc_numbers = {
        "123456": "ABC Trucking LLC",
        "654321": "Lone Star Freight",
        "111222": "Sunrise Logistics"
    }

    mc_number = request.mc_number.strip()

    if mc_number in approved_mc_numbers:
        return {
            "mc_number": mc_number,
            "eligible": True,
            "carrier_name": approved_mc_numbers[mc_number],
            "status": "authorized",
            "reason": None
        }

    return {
        "mc_number": mc_number,
        "eligible": False,
        "carrier_name": None,
        "status": "not_found_or_not_authorized",
        "reason": "MC number not found in approved carrier list"
    }


@app.post("/search-loads")
def search_loads(request: LoadSearchRequest, _: str = Depends(validate_api_key)):
    df = pd.read_csv("data/loads.csv")

    if request.origin:
        df = df[df["origin"].astype(str).str.lower() == request.origin.strip().lower()]

    if request.destination:
        df = df[df["destination"].astype(str).str.lower() == request.destination.strip().lower()]

    if request.equipment_type:
        df = df[df["equipment_type"].astype(str).str.lower() == request.equipment_type.strip().lower()]

    return {
        "count": len(df),
        "loads": df.to_dict(orient="records")
    }


@app.post("/evaluate-offer")
def evaluate_offer(request: OfferEvaluationRequest, _: str = Depends(validate_api_key)):
    loadboard_rate = request.loadboard_rate
    carrier_offer = request.carrier_offer
    round_number = request.round_number

    if round_number >= 3:
        return {
            "load_id": request.load_id,
            "decision": "reject",
            "counter_offer": None,
            "message": "We’ve reached our negotiation limit on this load."
        }

    acceptable_max = loadboard_rate * 1.05
    counter_max = loadboard_rate * 1.12

    if carrier_offer <= acceptable_max:
        return {
            "load_id": request.load_id,
            "decision": "accept",
            "counter_offer": carrier_offer,
            "message": f"We can do {carrier_offer:.0f} on this load."
        }

    if carrier_offer <= counter_max:
        midpoint = (loadboard_rate + carrier_offer) / 2
        return {
            "load_id": request.load_id,
            "decision": "counter",
            "counter_offer": round(midpoint, 2),
            "message": f"I may be able to do {midpoint:.0f} on this one."
        }

    return {
        "load_id": request.load_id,
        "decision": "reject",
        "counter_offer": None,
        "message": "That rate is above our range for this load."
    }


@app.post("/log-call")
def log_call(request: CallLogRequest, _: str = Depends(validate_api_key)):
    log_entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "mc_number": request.mc_number,
        "eligible": request.eligible,
        "load_id": request.load_id,
        "initial_rate": request.initial_rate,
        "carrier_offer": request.carrier_offer,
        "final_rate": request.final_rate,
        "negotiation_rounds": request.negotiation_rounds,
        "outcome": request.outcome,
        "sentiment": request.sentiment,
        "transferred_to_rep": request.transferred_to_rep,
        "summary": request.summary
    }

    file_path = "data/call_logs.csv"
    df_new = pd.DataFrame([log_entry])

    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        df_existing = pd.read_csv(file_path)
        df_all = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_all = df_new

    df_all.to_csv(file_path, index=False)

    return {
        "message": "Call log saved successfully",
        "log": log_entry
    }