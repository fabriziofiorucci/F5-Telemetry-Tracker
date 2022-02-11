from typing import Callable
from fastapi import FastAPI

def create_start_app_handler(app: FastAPI) -> Callable:
    async def start_app() -> None:
        # await connect_to_db(app)
        printf("In create start_app_handler")
        yield

    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:
    async def stop_app() -> None:
        # await close_db_connection(app)
        printf("In create stop_app_handler")
        yield

    return stop_app
