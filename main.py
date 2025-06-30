from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import httpx, os
from dotenv import load_dotenv

# 1. Carga la API_KEY desde el archivo .env
load_dotenv()
API_KEY = os.getenv("API_KEY")

app = FastAPI(title="BIN Checker API")

# 2. Middleware para validar la API Key en cada petición
@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    if request.headers.get("x-api-key") != API_KEY:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return await call_next(request)

# 3. Endpoint para consultar el BIN
@app.get("/bin/{bin_number}")
async def get_bin(bin_number: str):
    # Validar que sean 6 dígitos numéricos
    if not bin_number.isdigit() or len(bin_number) != 6:
        raise HTTPException(status_code=400, detail="BIN inválido")
    # Consultar la API pública de binlist.net
    url = f"https://lookup.binlist.net/{bin_number}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
    if r.status_code != 200:
        raise HTTPException(status_code=404, detail="BIN no encontrado")
    data = r.json()
    # Devolver solo los campos que nos interesan
    return {
        "marca": data.get("scheme"),
        "tipo": data.get("type"),
        "banco": data.get("bank", {}).get("name"),
        "pais": data.get("country", {}).get("name"),
        "prepaga": data.get("prepaid")
    }
