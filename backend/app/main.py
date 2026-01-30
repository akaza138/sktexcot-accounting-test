from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import Request
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="SK Texcot API", version="1.0.0")

# Handle CORS configuration with wildcard support
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
allow_origins = ["*"] if "*" in origins else [origin.strip() for origin in origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True if "*" not in allow_origins else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler to ensure all errors return JSON
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__}
    )

@app.get("/")
def read_root():
    return {"message": "Welcome to SK Texcot API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Import all routers
from .routers import auth, company, sales, billing, payments, ledger, dashboard, gst, tds, excel

# Register all routers (once each)
app.include_router(auth.router)
app.include_router(company.router)
app.include_router(sales.router)
app.include_router(billing.router)
app.include_router(payments.router)
app.include_router(ledger.router)
app.include_router(dashboard.router)
app.include_router(gst.router)
app.include_router(tds.router)
app.include_router(excel.router)
