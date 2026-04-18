"""
SALF FastAPI Main Application
Secure Academic Ledger Framework
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from app.core.config import settings
from app.api import auth, contributions, portfolio, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📦 Blockchain RPC: {settings.BESU_RPC_URL}")
    print(f"📡 IPFS Gateway: {settings.IPFS_GATEWAY}")
    
    yield
    
    # Shutdown
    print("👋 Shutting down SALF...")


app = FastAPI(
    title=settings.APP_NAME,
    description="""
    ## Secure Academic Ledger Framework (SALF)
    
    A blockchain-backed system for managing faculty academic contributions and credits.
    
    ### Features
    - **MetaMask Authentication**: Secure login using Ethereum wallets
    - **IPFS Storage**: Decentralized document storage
    - **AI Evaluation**: Automated quality and novelty scoring
    - **Fraud Detection**: ML-based anomaly detection
    - **Immutable Ledger**: Hyperledger Besu blockchain for transparency
    
    ### Roles
    - **Faculty**: Submit contributions, view portfolio
    - **HoD**: Review contributions, audit department
    - **Admin**: System governance, user management
    """,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log slow requests (exceeding P95 latency target)
    if process_time > settings.P95_LATENCY_MS / 1000:
        print(f"⚠️ Slow request: {request.url.path} took {process_time:.3f}s")
    
    return response


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(contributions.router, prefix=settings.API_V1_PREFIX)
app.include_router(portfolio.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin.router, prefix=settings.API_V1_PREFIX)


# Health check endpoints
@app.get("/", tags=["Health"])
async def root():
    """API root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    from app.services.blockchain_service import blockchain_service
    from app.services.ipfs_service import ipfs_service
    
    return {
        "status": "healthy",
        "services": {
            "api": True,
            "blockchain": blockchain_service.is_connected,
            "ipfs": ipfs_service.is_connected
        }
    }


@app.get("/metrics", tags=["Health"])
async def metrics():
    """Basic metrics endpoint."""
    from app.api.contributions import _contributions
    from app.api.auth import _users
    
    return {
        "total_users": len(_users),
        "total_contributions": len(_contributions),
        "blockchain_connected": True,  # Would check actual status
        "ipfs_connected": True
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
