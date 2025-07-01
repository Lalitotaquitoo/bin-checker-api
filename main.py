from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import httpx, os
from dotenv import load_dotenv

# 1. Cargar API_KEY desde .env o entorno
load_dotenv()
API_KEY = os.getenv("API_KEY", "").strip()

app = FastAPI(
    title="BIN Checker API",
    description="Consulta la marca, tipo, banco, país y si es prepaga a partir de los primeros 6 dígitos de una tarjeta (BIN/IIN).",
    version="1.0.0"
)

# 2. Middleware para validar API Key (excepto en rutas públicas)
@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    public_paths = ["/", "/docs", "/redoc", "/openapi.json"]
    if any(request.url.path.startswith(path) for path in public_paths):
        return await call_next(request)

    if request.headers.get("x-api-key") != API_KEY:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    return await call_next(request)

# 3. Ruta de salud para Railway
@app.get("/")
async def root():
    return {"mensaje": "La API de BIN Checker está viva 🚀"}

# 4. Endpoint principal
@app.get("/bin/{bin_number}", summary="Consultar información de BIN", tags=["BIN"])
async def get_bin(bin_number: str):
    # Validar formato del BIN
    if not bin_number.isdigit() or len(bin_number) != 6:
        raise HTTPException(status_code=400, detail="BIN inválido")

    # Consultar API pública de BINLIST
    url = f"https://lookup.binlist.net/{bin_number}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(url)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Error al conectar con el proveedor externo")

    if r.status_code != 200:
        raise HTTPException(status_code=404, detail="BIN no encontrado")

    data = r.json()

    # Devolver datos filtrados
    return {
        "marca": data.get("scheme"),
        "tipo": data.get("type"),
        "banco": data.get("bank", {}).get("name"),
        "pais": data.get("country", {}).get("name"),
        "prepaga": data.get("prepaid")
    }
