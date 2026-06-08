from fastapi import APIRouter

router = APIRouter(
    prefix="/carts",
    tags=["Carts"],
)