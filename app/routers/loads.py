from fastapi import APIRouter, HTTPException, Query
from app.database import get_db

router = APIRouter()

@router.get("/search")
def search_loads(
    origin: str = Query(None, description="Origin city/state"),
    destination: str = Query(None, description="Destination city/state"),
    equipment_type: str = Query(None, description="Equipment type: Dry Van, Flatbed, Reefer"),
    max_results: int = Query(5, description="Max loads to return")
):
    """
    Search available loads by origin, destination, or equipment type.
    Called by the HappyRobot agent during carrier calls.
    """
    conn = get_db()
    cur = conn.cursor()

    query = "SELECT * FROM loads WHERE status = 'available'"
    params = []

    if origin:
        query += " AND LOWER(origin) LIKE ?"
        params.append(f"%{origin.lower()}%")
    if destination:
        query += " AND LOWER(destination) LIKE ?"
        params.append(f"%{destination.lower()}%")
    if equipment_type:
        query += " AND LOWER(equipment_type) LIKE ?"
        params.append(f"%{equipment_type.lower()}%")

    query += f" LIMIT {max_results}"

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return {"loads": [], "message": "No available loads match the search criteria"}

    return {
        "loads": [dict(r) for r in rows],
        "count": len(rows)
    }

@router.get("/{load_id}")
def get_load(load_id: str):
    """Get a specific load by ID."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM loads WHERE load_id = ?", (load_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail=f"Load {load_id} not found")
    return dict(row)

@router.get("/")
def list_loads(status: str = Query("available")):
    """List all loads, optionally filtered by status."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM loads WHERE status = ?", (status,))
    rows = cur.fetchall()
    conn.close()
    return {"loads": [dict(r) for r in rows], "count": len(rows)}
