from fastapi import FastAPI
from app.api.v1.routers import tasks, users

app = FastAPI(title="Taskhub API", description="BE system", version="1.0.0")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Taskhub API is up!", "version": "1.0.0"}
