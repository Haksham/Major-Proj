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
from app.api import auth, contributions, portfolio, admin, institutes, institute_admin


async def _init_db():
    """Create all ORM tables and seed the initial admin user."""
    from sqlalchemy import text
    from app.core.database import engine, AsyncSessionLocal
    from app.models.database import Base, User, UserRole

    # Safe enum migrations (must run outside a transaction)
    async with engine.execution_options(isolation_level="AUTOCOMMIT").connect() as conn:
        await conn.execute(text(
            "ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'INSTITUTE_ADMIN'"
        ))
        # Create designation enum if missing, then add column
        await conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE userdesignation AS ENUM (
                    'professor','associate_professor','assistant_professor','staff'
                );
            EXCEPTION WHEN duplicate_object THEN NULL;
            END $$;
        """))
        await conn.execute(text("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS designation userdesignation;
        """))

    # Create tables (no-op if they already exist)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed admin wallet if not present
    from sqlalchemy import select
    ADMIN_WALLET = "0xa0dbb25771341a35d6be0e676a311b4eddd82b71"
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.wallet_address == ADMIN_WALLET)
        )
        if result.scalar_one_or_none() is None:
            session.add(User(
                wallet_address=ADMIN_WALLET,
                name="Admin User",
                email="admin@salf.edu",
                employee_id="ADMIN001",
                role=UserRole.ADMIN,
                is_active=True,
                total_credits=0.0,
            ))
            await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📦 Blockchain RPC: {settings.BESU_RPC_URL}")
    print(f"📡 IPFS: {settings.IPFS_API_URL}")
    print(f"🗄️  Database: {settings.DATABASE_URL}")

    try:
        await _init_db()
    except Exception as e:
        print(f"⚠️  DB init failed (is Postgres running?): {e}")
        print("   App will start but DB-dependent endpoints will fail until Postgres is available.")

    yield

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
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    if process_time > settings.P95_LATENCY_MS / 1000:
        print(f"⚠️ Slow request: {request.url.path} took {process_time:.3f}s")
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )


# Routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(institutes.router, prefix=settings.API_V1_PREFIX)
app.include_router(contributions.router, prefix=settings.API_V1_PREFIX)
app.include_router(portfolio.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin.router, prefix=settings.API_V1_PREFIX)
app.include_router(institute_admin.router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Health"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    from app.services.blockchain_service import blockchain_service
    from app.services.ipfs_service import ipfs_service

    return {
        "status": "healthy",
        "services": {
            "api": True,
            "blockchain": blockchain_service.is_connected,
            "ipfs": ipfs_service.is_connected,
        },
    }


@app.get("/metrics", tags=["Health"])
async def metrics():
    from app.core.database import AsyncSessionLocal
    from app.models.database import User, Contribution
    from sqlalchemy import func, select

    async with AsyncSessionLocal() as session:
        user_count = (await session.execute(select(func.count(User.id)))).scalar()
        contrib_count = (await session.execute(select(func.count(Contribution.id)))).scalar()

    return {
        "total_users": user_count,
        "total_contributions": contrib_count,
        "blockchain_connected": True,
        "ipfs_connected": True,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
