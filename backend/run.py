import uvicorn

from app.config import get_config

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=get_config().port, reload=True)
