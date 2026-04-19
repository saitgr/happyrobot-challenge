from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel, field_validator
import pandas as pd
from datetime import datetime
import os
import httpx

app = FastAPI()

API_KEY = os.getenv("API_KEY", "dev-key")
FMCSA_API_KEY = os.getenv("FMCSA_API_KEY", "cdc33e44d693a3a58451898d4ec9df862c65b954")


def validate_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


class CarrierRequest(BaseModel):
    mc_number: str


class LoadSearchRequest(BaseModel):
    origin: str | None = None
    destination: str | None = None
    equipment_type: str | None = None
    pickup_date: str | None = None


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
    summary: str

    @field_validator('initial_rate', 'carrier_offer', 'final_rate', mode='before')
    @classmethod
    def empty_to_none(cls, v):
        if v == "" or v is None or str(v).strip() in ("null", "undefined", "none"):
            return None
        return v


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


# FMCSA API integration — ready to connect when API key is active
# async def verify_with_fmcsa(mc_number: str):
#     url = f"https://mobile.fmcsa.dot.gov/qc/services/carriers/docket-number/{mc_number}?webKey={FMCSA_API_KEY}"
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#         data = response.json()
#         carrier = data.get("content", {}).get("carrier", {})
#         allowed = carrier.get("allowedToOperate") == "Y"
#         name = carrier.get("legalName") or carrier.get("dbaName")
#         return allowed, name


@app.post("/verify-carrier")
def verify_carrier(request: CarrierRequest, _: str = Depends(validate_api_key)):
    # Simulated carrier database — in production this calls the FMCSA API
    approved_mc_numbers = {
        "123456": "ABC Trucking LLC",
        "654321": "Lone Star Freight",
        "111222": "Sunrise Logistics",
        "789012": "Blue Ridge Transport",
        "345678": "Pacific Haulers Inc",
        "901234": "Midwest Freight Co",
        "456789": "Southern Cross Carriers",
        "234567": "Great Plains Logistics",
        "678901": "Atlas Trucking Group",
        "112233": "Liberty Freight LLC",
    }

    mc_number = str(request.mc_number).strip()

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

    if request.pickup_date:
        df = df[df["pickup_datetime"].astype(str).str.startswith(request.pickup_date)]

    return {
        "count": len(df),
        "loads": df.to_dict(orient="records")
    }


@app.post("/evaluate-offer")
def evaluate_offer(request: OfferEvaluationRequest, _: str = Depends(validate_api_key)):
    loadboard_rate = request.loadboard_rate
    carrier_offer = request.carrier_offer
    round_number = request.round_number

    acceptable_max = loadboard_rate * 1.05
    counter_max = loadboard_rate * 1.12

    # Evaluate price first, regardless of round number
    if carrier_offer <= acceptable_max:
        return {
            "load_id": request.load_id,
            "decision": "accept",
            "counter_offer": carrier_offer,
            "message": f"We can do {carrier_offer:.0f} on this load."
        }

    if carrier_offer <= counter_max:
        if round_number >= 3:
            return {
                "load_id": request.load_id,
                "decision": "reject",
                "counter_offer": None,
                "message": "We've reached our negotiation limit on this load."
            }
        midpoint = (loadboard_rate + carrier_offer) / 2
        return {
            "load_id": request.load_id,
            "decision": "counter",
            "counter_offer": round(midpoint, 2),
            "message": f"I may be able to do {midpoint:.0f} on this one."
        }

    if round_number >= 3:
        return {
            "load_id": request.load_id,
            "decision": "reject",
            "counter_offer": None,
            "message": "We've reached our negotiation limit on this load."
        }

    return {
        "load_id": request.load_id,
        "decision": "too_high",
        "counter_offer": None,
        "message": "That rate is above our range. Could you come back with a lower offer?"
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