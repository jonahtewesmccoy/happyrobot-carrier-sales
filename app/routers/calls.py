from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
import uuid

router = APIRouter()

class CallResult(BaseModel):
    call_id: Optional[str] = None
    mc_number: Optional[str] = None
    carrier_name: Optional[str] = None
    load_id: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    loadboard_rate: Optional[float] = None
    final_agreed_rate: Optional[float] = None
    negotiation_rounds: Optional[int] = 0
    outcome: Optional[str] = None          # booked, declined, no_answer, transferred, cancelled
    sentiment: Optional[str] = None        # positive, neutral, negative, frustrated
    call_duration_seconds: Optional[int] = None
    notes: Optional[str] = None

class NegotiationEvaluate(BaseModel):
    load_id: str
    loadboard_rate: float
    carrier_offer: float
    negotiation_round: int  # 1, 2, or 3

@router.post("/log")
def log_call(result: CallResult):
    """
    Save call outcome after a carrier interaction.
    Called by HappyRobot agent at end of each call.
    """
    call_id = result.call_id or f"CALL-{uuid.uuid4().hex[:8].upper()}"

    conn = get_db()
    cur = conn.cursor()

    # Mark load as booked if outcome is booked
    if result.outcome == "booked" and result.load_id:
        cur.execute("UPDATE loads SET status = 'booked' WHERE load_id = ?", (result.load_id,))

    cur.execute("""
        INSERT OR REPLACE INTO call_logs
        (call_id, mc_number, carrier_name, load_id, origin, destination,
         loadboard_rate, final_agreed_rate, negotiation_rounds, outcome,
         sentiment, call_duration_seconds, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        call_id,
        result.mc_number,
        result.carrier_name,
        result.load_id,
        result.origin,
        result.destination,
        result.loadboard_rate,
        result.final_agreed_rate,
        result.negotiation_rounds or 0,
        result.outcome,
        result.sentiment,
        result.call_duration_seconds,
        result.notes
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "call_id": call_id,
        "message": f"Call logged with outcome: {result.outcome}"
    }

@router.post("/evaluate-offer")
def evaluate_offer(data: NegotiationEvaluate):
    """
    Evaluate a carrier's counter offer during negotiation.
    Returns whether to accept, counter, or reject with a suggested counter price.
    
    Business logic:
    - We can go up to 5% below loadboard rate (our floor)
    - Round 1: counter at midpoint between their offer and our rate
    - Round 2: drop 2% from last counter
    - Round 3: final offer, 5% below loadboard (max discount)
    """
    loadboard = data.loadboard_rate
    offer = data.carrier_offer
    floor = loadboard * 0.95  # max 5% discount

    if offer >= loadboard:
        return {
            "decision": "accept",
            "message": "Carrier offer meets or exceeds loadboard rate. Accept immediately.",
            "agreed_rate": offer
        }

    if offer < floor:
        if data.negotiation_round >= 3:
            return {
                "decision": "reject",
                "message": f"Carrier offer is too low. Our final offer is ${floor:,.2f} and we cannot go lower.",
                "our_counter": floor,
                "agreed_rate": None
            }
        # Counter offer
        midpoint = round((offer + loadboard) / 2, 2)
        counter = max(midpoint, floor)
        return {
            "decision": "counter",
            "message": f"Carrier offer is below our threshold. Counter with ${counter:,.2f}.",
            "our_counter": counter,
            "agreed_rate": None
        }

    # Offer is between floor and loadboard - acceptable
    return {
        "decision": "accept",
        "message": f"Carrier offer of ${offer:,.2f} is within acceptable range. Accept the deal.",
        "agreed_rate": offer
    }

@router.get("/")
def list_calls(limit: int = 50):
    """List recent call logs."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM call_logs ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return {"calls": [dict(r) for r in rows], "count": len(rows)}

@router.get("/{call_id}")
def get_call(call_id: str):
    """Get a specific call log."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM call_logs WHERE call_id = ?", (call_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Call not found")
    return dict(row)
