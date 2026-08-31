from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.config import get_settings
from app.routes.wallet import router as wallet_router

settings = get_settings()

app = FastAPI(
    title="SIH Crypto Fraud Intelligence - Milestone 3",
    description=(
        "Backend prototype for multi-hop fund-flow graph tracing and asset transfer normalization "
        "(native ETH and ERC-20 tokens) via Alchemy API for crypto fraud tracking."
    ),
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for the local Vite frontend dev server.
# Narrowed from ["*"] to specific origins for local development safety.
# To allow additional origins (e.g. staging), add them to the list below.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://cryptotrace-mcgbdn055-ananyalotankar1904-codes-projects.vercel.app",
    ],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["Accept", "Content-Type"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Format validation errors into a clean, consistent schema."""
    errors = exc.errors()
    simplified_errors = [
        {
            "field": " -> ".join(str(loc) for loc in err.get("loc", [])),
            "issue": err.get("msg"),
            "type": err.get("type"),
        }
        for err in errors
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Invalid request parameter(s) provided.",
            "details": {"validation_errors": simplified_errors},
        },
    )


@app.get("/", tags=["General"])
async def root():
    """Root endpoint providing project overview and health status."""
    return {
        "project": "SIH - Crypto Fraud Intelligence Engine",
        "milestone": "Milestone 3: Basic Multi-Hop Fund-Flow Tracing",
        "status": "online",
        "alchemy_network": settings.ALCHEMY_NETWORK,
        "is_api_key_configured": settings.is_api_key_configured,
        "docs": "/docs",
    }


@app.get("/health", tags=["General"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "api_key_configured": settings.is_api_key_configured,
    }


from app.routes.report import router as report_router

# Include routes
app.include_router(wallet_router)
app.include_router(report_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
