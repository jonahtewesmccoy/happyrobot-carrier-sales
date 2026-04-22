import sqlite3
import os
import json
from datetime import datetime, timedelta
import random

DB_PATH = os.getenv("DB_PATH", "data/carrier_sales.db")

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS loads (
            load_id TEXT PRIMARY KEY,
            origin TEXT NOT NULL,
            destination TEXT NOT NULL,
            pickup_datetime TEXT NOT NULL,
            delivery_datetime TEXT NOT NULL,
            equipment_type TEXT NOT NULL,
            loadboard_rate REAL NOT NULL,
            notes TEXT,
            weight REAL,
            commodity_type TEXT,
            num_of_pieces INTEGER,
            miles REAL,
            dimensions TEXT,
            status TEXT DEFAULT 'available'
        );

        CREATE TABLE IF NOT EXISTS call_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id TEXT UNIQUE NOT NULL,
            mc_number TEXT,
            carrier_name TEXT,
            load_id TEXT,
            origin TEXT,
            destination TEXT,
            loadboard_rate REAL,
            final_agreed_rate REAL,
            negotiation_rounds INTEGER DEFAULT 0,
            outcome TEXT,
            sentiment TEXT,
            call_duration_seconds INTEGER,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)

    # Seed loads if empty
    cur.execute("SELECT COUNT(*) FROM loads")
    if cur.fetchone()[0] == 0:
        _seed_loads(cur)

    conn.commit()
    conn.close()
    print("✅ Database initialized")

def _seed_loads(cur):
    base = datetime.now()
    loads = [
        ("LD-001", "Chicago, IL", "Dallas, TX", base+timedelta(days=1), base+timedelta(days=2), "Dry Van", 2800, "No touch freight", 42000, "Auto Parts", 1, 921, '48"x96"x96"'),
        ("LD-002", "Los Angeles, CA", "Phoenix, AZ", base+timedelta(days=1), base+timedelta(days=1,hours=8), "Flatbed", 1450, "Tarping required", 38000, "Steel Coils", 4, 372, '48"x102"x60"'),
        ("LD-003", "Atlanta, GA", "Miami, FL", base+timedelta(days=2), base+timedelta(days=3), "Reefer", 1900, "Temp: 34-38°F", 28000, "Produce", 320, 662, '48"x96"x96"'),
        ("LD-004", "Houston, TX", "Nashville, TN", base+timedelta(days=1), base+timedelta(days=2), "Dry Van", 2200, "Dock doors required", 35000, "Consumer Goods", 200, 783, '48"x96"x96"'),
        ("LD-005", "Seattle, WA", "Portland, OR", base+timedelta(hours=6), base+timedelta(hours=12), "Flatbed", 650, "Oversize load", 44000, "Lumber", 1, 174, '53"x102"x72"'),
        ("LD-006", "Denver, CO", "Kansas City, MO", base+timedelta(days=2), base+timedelta(days=3), "Dry Van", 1750, "Driver assist required", 33000, "Electronics", 150, 601, '48"x96"x96"'),
        ("LD-007", "Memphis, TN", "Chicago, IL", base+timedelta(days=1), base+timedelta(days=2), "Reefer", 2100, "Temp: 0°F frozen", 24000, "Frozen Foods", 400, 534, '48"x96"x102"'),
        ("LD-008", "New York, NY", "Boston, MA", base+timedelta(hours=8), base+timedelta(hours=14), "Dry Van", 950, "Liftgate required", 18000, "Retail Goods", 80, 215, '48"x96"x96"'),
        ("LD-009", "Phoenix, AZ", "Las Vegas, NV", base+timedelta(days=1), base+timedelta(days=1,hours=5), "Flatbed", 780, "No tarping needed", 36000, "Construction Equip", 2, 297, '48"x102"x72"'),
        ("LD-010", "Minneapolis, MN", "Detroit, MI", base+timedelta(days=2), base+timedelta(days=3), "Dry Van", 1600, "Team drivers preferred", 40000, "Machine Parts", 50, 698, '48"x96"x96"'),
        ("LD-011", "Dallas, TX", "San Antonio, TX", base+timedelta(hours=4), base+timedelta(hours=10), "Dry Van", 620, "No touch", 31000, "Packaged Goods", 250, 274, '48"x96"x96"'),
        ("LD-012", "Charlotte, NC", "Washington, DC", base+timedelta(days=1), base+timedelta(days=2), "Reefer", 1350, "Temp: 36-40°F", 22000, "Dairy Products", 280, 395, '48"x96"x96"'),
        ("LD-013", "Columbus, OH", "Pittsburgh, PA", base+timedelta(hours=10), base+timedelta(hours=16), "Dry Van", 750, "Dock to dock", 29000, "Paper Products", 100, 185, '48"x96"x96"'),
        ("LD-014", "Salt Lake City, UT", "Reno, NV", base+timedelta(days=1), base+timedelta(days=2), "Flatbed", 1100, "Step deck OK", 41000, "Heavy Equipment", 3, 521, '48"x102"x60"'),
        ("LD-015", "Jacksonville, FL", "Atlanta, GA", base+timedelta(days=1), base+timedelta(days=2), "Dry Van", 1200, "No hazmat", 27000, "Home Goods", 180, 346, '48"x96"x96"'),
        ("LD-016", "St. Louis, MO", "Indianapolis, IN", base+timedelta(hours=6), base+timedelta(hours=12), "Dry Van", 820, "Appointment required", 38000, "Auto Parts", 90, 241, '48"x96"x96"'),
        ("LD-017", "San Diego, CA", "Fresno, CA", base+timedelta(days=1), base+timedelta(days=1,hours=6), "Reefer", 980, "Temp: 32-36°F", 26000, "Fresh Produce", 350, 316, '48"x96"x96"'),
        ("LD-018", "Louisville, KY", "Cleveland, OH", base+timedelta(days=2), base+timedelta(days=3), "Dry Van", 1050, "Team load bonus available", 44000, "Industrial Parts", 60, 308, '48"x96"x96"'),
        ("LD-019", "Albuquerque, NM", "El Paso, TX", base+timedelta(hours=8), base+timedelta(hours=14), "Flatbed", 720, "Military base delivery", 39000, "Steel Beams", 6, 265, '53"x102"x48"'),
        ("LD-020", "Oklahoma City, OK", "Tulsa, OK", base+timedelta(hours=3), base+timedelta(hours=7), "Dry Van", 420, "Short haul", 21000, "Retail Merchandise", 120, 100, '48"x96"x96"'),
    ]

    cur.executemany("""
        INSERT INTO loads (load_id, origin, destination, pickup_datetime, delivery_datetime,
        equipment_type, loadboard_rate, notes, weight, commodity_type, num_of_pieces, miles, dimensions)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [(
        l[0], l[1], l[2],
        l[3].strftime("%Y-%m-%d %H:%M"),
        l[4].strftime("%Y-%m-%d %H:%M"),
        l[5], l[6], l[7], l[8], l[9], l[10], l[11], l[12]
    ) for l in loads])

    print(f"✅ Seeded {len(loads)} loads")
