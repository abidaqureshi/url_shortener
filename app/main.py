from fastapi import FastAPI, Request
from app import database as sqlLite
from app.controllers.url_controller import router as url_router
from app.controllers.analytics_controller import router as analytics_router
import time

from app.database import create_tables, check_db_connection

app = FastAPI(
    title="URL Shortener API",
    description="A comprehensive URL shortener with, Rate limiting, Caching and analytics",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    await create_tables()

    if await check_db_connection():
        print(" Database connection successful")
    else:
        print(" Database connection failed")


app.include_router(url_router)
app.include_router(analytics_router)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/")
async def root():
    return {"message": "URL shortener API is up and running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
