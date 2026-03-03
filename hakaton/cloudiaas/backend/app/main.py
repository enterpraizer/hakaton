from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CloudIaaS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers are registered here after they are implemented
# from app.routers import auth, vms, networks, quotas, admin
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
# app.include_router(vms.router, prefix="/api/v1/vms", tags=["vms"])
# app.include_router(networks.router, prefix="/api/v1/networks", tags=["networks"])
# app.include_router(quotas.router, prefix="/api/v1/quotas", tags=["quotas"])
# app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])


@app.get("/health")
async def health():
    return {"status": "ok"}
