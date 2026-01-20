from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="SK Texcot API", version="1.0.0")

origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
