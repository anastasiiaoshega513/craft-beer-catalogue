from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes.beer import router as beer_router

app = FastAPI()


app.include_router(beer_router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
