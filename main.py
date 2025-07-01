from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import httpx, os
from dotenv import load_dotenv

# Load API key
load_dotenv()
API_KEY = os.getenv("API_KEY", "").strip()

if not API_KEY:
    raise RuntimeError("API_KEY is not set in environment variables")

app = FastAPI(
    title="BIN Checker API",
    description="Lookup card scheme, type, issuing bank, country and prepaid status from the first 6-8 digits (BIN/IIN).",
    version="1.0.0"
)

# Middleware: allow public docs and health check, protect all other routes
@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    public_paths = ["/", "/docs", "/redoc", "/openapi.json"]
    if any(request.url.path.startswith(p) for p in public_paths):
        return await call_next(request)

    if request.headers.get("x-api-key") != API_KEY:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return await call_next(request)

# Health check
@app.get("/", tags=["Health"])
async def health_check():
    return {"status": "alive"}

# Main BIN lookup endpoint
@app.get("/bin/{bin_number}", summary="Lookup BIN details", tags=["BIN"])
async def lookup_bin(bin_number: str):
    if not (bin_number.isdigit() and 6 <= len(bin_number) <= 8):
        raise HTTPException(status_code=400, detail="Invalid BIN format")

    url = f"https://lookup.binlist.net/{bin_number}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="External service error")

    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="BIN not found")

    data = response.json()
    return {
        "scheme": data.get("scheme"),
        "type": data.get("type"),
        "bank": data.get("bank", {}).get("name"),
        "country": data.get("country", {}).get("name"),
        "prepaid": data.get("prepaid")
    }
