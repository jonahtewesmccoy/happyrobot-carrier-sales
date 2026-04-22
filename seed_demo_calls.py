"""
Run this script to populate the DB with realistic demo call data.
Usage: python seed_demo_calls.py
"""
import sqlite3
import os
import random
from datetime import datetime, timedelta
import uuid

DB_PATH = os.getenv("DB_PATH", "data/carrier_sales.db")

CARRIERS = [
    ("MC-123456", "Swift Transport LLC"),
    ("MC-234567", "Blue Ridge Carriers"),
    ("MC-345678", "Lone Star Freight"),
    ("MC-456789", "Great Lakes Logistics"),
    ("MC-567890", "Pacific Coast Haulers"),
    ("MC-678901", "Mountain West Transport"),
    ("MC-789012", "Sunbelt Freight Inc"),
    ("MC-890123", "Midwest Express Carriers"),
    ("MC-901234", "Atlantic Freight Solutions"),
    ("MC-012345", "Southern Cross Logistics"),
]

OUTCOMES = ["booked", "booked", "booked", "declined", "transferred", "cancelled", "no_answer"]
SENTIMENTS = ["positive", "positive", "neutral", "neutral", "negative", "frustrated"]

LOADS = [
    ("LD-001", "Chicago, IL", "Dallas, TX", 2800),
    ("LD-002", "Los Angeles, CA", "Phoenix, AZ", 1450),
    ("LD-003", "Atlanta, GA", "Miami, FL", 1900),
    ("LD-004", "Houston, TX", "Nashville, TN", 2200),
    ("LD-005", "Seattle, WA", "Portland, OR", 650),
    ("LD-006", "Denver, CO", "Kansas City, MO", 1750),
    ("LD-007", "Memphis, TN", "Chicago, IL", 2100),
    ("LD-008", "New York, NY", "Boston, MA", 950),
]

def seed_calls(n=40):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for i in range(n):
        mc, name = random.choice(CARRIERS)
        load = random.choice(LOADS)
        outcome = random.choice(OUTCOMES)
        sentiment = random.choice(SENTIMENTS)
        rounds = random.randint(0, 3)
        
        loadboard_rate = load[3] * random.uniform(0.9, 1.1)
        
        if outcome == "booked":
            # Agreed between 95% and 102% of loadboard
            agreed_rate = loadboard_rate * random.uniform(0.95, 1.02)
            sentiment = random.choice(["positive", "positive", "neutral"])
        else:
            agreed_rate = None
            if outcome == "declined":
                sentiment = random.choice(["negative", "frustrated", "neutral"])

        days_ago = random.randint(0, 7)
        hours_ago = random.randint(0, 23)
        created = (datetime.now() - timedelta(days=days_ago, hours=hours_ago)).strftime("%Y-%m-%d %H:%M:%S")
        duration = random.randint(90, 480) if outcome != "no_answer" else random.randint(15, 45)

        call_id = f"CALL-{uuid.uuid4().hex[:8].upper()}"

        cur.execute("""
            INSERT OR IGNORE INTO call_logs
            (call_id, mc_number, carrier_name, load_id, origin, destination,
             loadboard_rate, final_agreed_rate, negotiation_rounds, outcome,
             sentiment, call_duration_seconds, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            call_id, mc, name, load[0], load[1], load[2],
            round(loadboard_rate, 2),
            round(agreed_rate, 2) if agreed_rate else None,
            rounds, outcome, sentiment, duration, created
        ))

    conn.commit()
    conn.close()
    print(f"✅ Seeded {n} demo calls into {DB_PATH}")

if __name__ == "__main__":
    seed_calls(40)
