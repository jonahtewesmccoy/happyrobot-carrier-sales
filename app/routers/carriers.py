from fastapi import APIRouter, HTTPException
import httpx
import os

router = APIRouter()

FMCSA_API_KEY = os.getenv("FMCSA_API_KEY", "")
FMCSA_BASE = "https://mobile.fmcsa.dot.gov/qc/services/carriers"

@router.get("/verify/{mc_number}")
async def verify_carrier(mc_number: str):
    """
    Verify a carrier's eligibility using the FMCSA API.
    Called by the agent to vet carriers before offering loads.
    Returns eligibility status and key carrier info.
    """
    # Strip 'MC' prefix if present
    clean_mc = mc_number.upper().replace("MC", "").replace("-", "").strip()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{FMCSA_BASE}/{clean_mc}?webKey={FMCSA_API_KEY}"
            resp = await client.get(url)

            if resp.status_code == 404:
                return {
                    "eligible": False,
                    "mc_number": mc_number,
                    "reason": "MC number not found in FMCSA database",
                    "carrier": None
                }

            if resp.status_code != 200:
                # Fallback: don't block the call on API errors
                return {
                    "eligible": True,
                    "mc_number": mc_number,
                    "reason": "FMCSA lookup unavailable - proceeding with caution",
                    "carrier": {"name": "Unknown", "mc_number": mc_number}
                }

            data = resp.json()
            carrier_data = data.get("content", {}).get("carrier", {})

            if not carrier_data:
                return {
                    "eligible": False,
                    "mc_number": mc_number,
                    "reason": "No carrier data found for this MC number",
                    "carrier": None
                }

            # Check eligibility conditions
            allowed_to_operate = carrier_data.get("allowedToOperate", "N")
            out_of_service = carrier_data.get("outOfService", 0)
            safety_rating = carrier_data.get("safetyRating", "")

            is_eligible = (
                allowed_to_operate == "Y" and
                int(out_of_service) == 0 and
                safety_rating not in ["Unsatisfactory"]
            )

            return {
                "eligible": is_eligible,
                "mc_number": mc_number,
                "reason": _get_ineligibility_reason(allowed_to_operate, out_of_service, safety_rating) if not is_eligible else "Carrier is active and authorized to operate",
                "carrier": {
                    "name": carrier_data.get("legalName", "Unknown"),
                    "mc_number": mc_number,
                    "dot_number": carrier_data.get("dotNumber"),
                    "city": carrier_data.get("phyCity"),
                    "state": carrier_data.get("phyState"),
                    "allowed_to_operate": allowed_to_operate,
                    "out_of_service": bool(int(out_of_service)),
                    "safety_rating": safety_rating or "Not Rated",
                    "total_drivers": carrier_data.get("totalDrivers"),
                    "total_power_units": carrier_data.get("totalPowerUnits"),
                }
            }

    except httpx.TimeoutException:
        return {
            "eligible": True,
            "mc_number": mc_number,
            "reason": "FMCSA API timeout - proceeding with standard verification",
            "carrier": {"name": "Pending verification", "mc_number": mc_number}
        }
    except Exception as e:
        return {
            "eligible": True,
            "mc_number": mc_number,
            "reason": f"Verification service error - proceeding: {str(e)}",
            "carrier": {"name": "Unknown", "mc_number": mc_number}
        }

def _get_ineligibility_reason(allowed, out_of_service, safety_rating):
    if allowed != "Y":
        return "Carrier is not authorized to operate"
    if int(out_of_service) != 0:
        return "Carrier is currently out of service"
    if safety_rating == "Unsatisfactory":
        return "Carrier has an Unsatisfactory safety rating"
    return "Carrier does not meet eligibility requirements"
