from fastapi import FastAPI
from server.src.app.api import health, welcome
import uvicorn

app = FastAPI()

app.include_router(health.router, tags=["Test"])
app.include_router(welcome.router, tags=["Test"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)