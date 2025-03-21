import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.routes import users, wallets
from app.database import engine
from app.models import Base


@asynccontextmanager
async def lifespan(app_name: FastAPI):
    """
    I was having issues with uvicorn being executed in the terminal. It would often keep the server up and running
    after I would terminate the server and this led to no feedback coming from the terminal when re-running
    uvicorn. Thus, I've moved to this approach to control start and stop of the server, documented in FastAPI docs.
    """
    print("App has started!")
    yield
    print("App has shut down!")


app = FastAPI(lifespan=lifespan)
app.include_router(users.router)
app.include_router(wallets.router)

Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
