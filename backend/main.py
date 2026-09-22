import uvicorn
from app.server import app, settings

if __name__ == "__main__":
    uvicorn.run("app.server:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)

