from fastapi import APIRouter
from app.database import get_db

router = APIRouter()

@router.get("/metrics")
def get_metrics():
    """
    Return all business metrics needed to power the dashboard.
    Covers: volume, conversion, revenue, negotiation, sentiment.
    """
    conn = get_db()
    cur = conn.cursor()

    # --- Core call volumes ---
    cur.execute("SELECT COUNT(*) FROM call_logs")
    total_calls = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM call_logs WHERE outcome = 'booked'")
    booked = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM call_logs WHERE outcome = 'declined'")
    declined = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM call_logs WHERE outcome = 'transferred'")
    transferred = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM call_logs WHERE outcome = 'cancelled'")
    cancelled = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM call_logs WHERE outcome = 'no_answer'")
    no_answer = cur.fetchone()[0]

    # --- Revenue metrics ---
    cur.execute("""
        SELECT 
            SUM(final_agreed_rate) as total_revenue,
            AVG(final_agreed_rate) as avg_rate,
            SUM(loadboard_rate) as total_loadboard,
            AVG(loadboard_rate) as avg_loadboard
        FROM call_logs WHERE outcome = 'booked'
    """)
    rev = cur.fetchone()
    total_revenue = rev[0] or 0
    avg_agreed_rate = rev[1] or 0
    total_loadboard = rev[2] or 0
    avg_loadboard = rev[3] or 0

    # Rate savings (how much below loadboard we sold)
    rate_efficiency = ((avg_loadboard - avg_agreed_rate) / avg_loadboard * 100) if avg_loadboard else 0

    # --- Negotiation metrics ---
    cur.execute("SELECT AVG(negotiation_rounds) FROM call_logs WHERE outcome = 'booked'")
    avg_rounds = cur.fetchone()[0] or 0

    cur.execute("SELECT AVG(call_duration_seconds) FROM call_logs")
    avg_duration = cur.fetchone()[0] or 0

    cur.execute("""
        SELECT negotiation_rounds, COUNT(*) as count
        FROM call_logs WHERE outcome = 'booked'
        GROUP BY negotiation_rounds ORDER BY negotiation_rounds
    """)
    rounds_dist = [{"rounds": r[0], "count": r[1]} for r in cur.fetchall()]

    # --- Sentiment breakdown ---
    cur.execute("""
        SELECT sentiment, COUNT(*) as count 
        FROM call_logs WHERE sentiment IS NOT NULL
        GROUP BY sentiment
    """)
    sentiment_data = [{"sentiment": r[0], "count": r[1]} for r in cur.fetchall()]

    # --- Outcome breakdown ---
    cur.execute("""
        SELECT outcome, COUNT(*) as count 
        FROM call_logs WHERE outcome IS NOT NULL
        GROUP BY outcome
    """)
    outcome_data = [{"outcome": r[0], "count": r[1]} for r in cur.fetchall()]

    # --- Recent calls ---
    cur.execute("""
        SELECT call_id, carrier_name, mc_number, origin, destination,
               loadboard_rate, final_agreed_rate, outcome, sentiment,
               negotiation_rounds, call_duration_seconds, created_at
        FROM call_logs
        ORDER BY created_at DESC LIMIT 10
    """)
    recent_calls = [dict(r) for r in cur.fetchall()]

    # --- Load availability ---
    cur.execute("SELECT status, COUNT(*) FROM loads GROUP BY status")
    load_status = {r[0]: r[1] for r in cur.fetchall()}

    # --- Top lanes by booking ---
    cur.execute("""
        SELECT origin, destination, COUNT(*) as bookings, AVG(final_agreed_rate) as avg_rate
        FROM call_logs WHERE outcome = 'booked'
        GROUP BY origin, destination
        ORDER BY bookings DESC LIMIT 5
    """)
    top_lanes = [dict(r) for r in cur.fetchall()]

    # --- Daily call volume (last 7 days) ---
    cur.execute("""
        SELECT DATE(created_at) as day, COUNT(*) as total,
               SUM(CASE WHEN outcome='booked' THEN 1 ELSE 0 END) as booked
        FROM call_logs
        GROUP BY DATE(created_at)
        ORDER BY day DESC LIMIT 7
    """)
    daily_volume = [dict(r) for r in cur.fetchall()]

    conn.close()

    conversion_rate = (booked / total_calls * 100) if total_calls else 0

    return {
        "summary": {
            "total_calls": total_calls,
            "booked": booked,
            "declined": declined,
            "transferred": transferred,
            "cancelled": cancelled,
            "no_answer": no_answer,
            "conversion_rate": round(conversion_rate, 1),
            "total_revenue": round(total_revenue, 2),
            "avg_agreed_rate": round(avg_agreed_rate, 2),
            "avg_loadboard_rate": round(avg_loadboard, 2),
            "rate_efficiency_pct": round(rate_efficiency, 2),
            "avg_negotiation_rounds": round(avg_rounds, 1),
            "avg_call_duration_seconds": round(avg_duration),
        },
        "charts": {
            "sentiment_breakdown": sentiment_data,
            "outcome_breakdown": outcome_data,
            "negotiation_rounds_distribution": rounds_dist,
            "daily_volume": daily_volume,
            "top_lanes": top_lanes,
        },
        "load_inventory": load_status,
        "recent_calls": recent_calls
    }
