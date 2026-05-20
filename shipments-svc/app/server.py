"""
Shipments Service — shipments-svc-s01

Микросервис для управления отслеживанием грузов.
Предоставляет REST API для создания, чтения, обновления и удаления грузов.

Project Code: shipments-s01
Student: s01 | Group: 431
"""
import time
from typing import List

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="shipments-svc-s01")


class ShipmentCreate(BaseModel):
    """Модель для создания нового груза."""

    tracking: str = Field(..., min_length=1, description="Трекинг-номер")
    origin: str = Field(..., min_length=1, description="Откуда")
    destination: str = Field(..., min_length=1, description="Куда")
    status: str = Field(default="pending", description="Статус груза")


class ShipmentUpdate(BaseModel):
    """Модель для обновления груза."""

    tracking: str = Field(..., min_length=1, description="Трекинг-номер")
    origin: str = Field(..., min_length=1, description="Откуда")
    destination: str = Field(..., min_length=1, description="Куда")
    status: str = Field(default="pending", description="Статус груза")


class Shipment(BaseModel):
    """Модель груза с полным набором полей."""

    id: int
    tracking: str
    origin: str
    destination: str
    status: str
    created_at: float
    updated_at: float


class AppState:
    """
    Контейнер состояния приложения.

    Избегает использования global statement для хранения данных.
    """

    # pylint: disable=too-few-public-methods

    def __init__(self) -> None:
        self.db: List[dict] = []
        self.next_id: int = 1


state = AppState()


@app.get("/")
def root() -> dict:
    """Возвращает базовую информацию о сервисе."""
    return {"service": "shipments-svc-s01", "status": "running"}


@app.get("/health")
def health() -> dict:
    """Проверка здоровья сервиса (health check)."""
    return {"status": "healthy"}


@app.post("/api/shipments", response_model=Shipment, status_code=201)
def create_shipment(shipment: ShipmentCreate) -> dict:
    """
    Создать новый груз.

    Args:
        shipment: Данные груза для создания

    Returns:
        Созданный груз с присвоенным ID

    Raises:
        HTTPException: Если трекинг-номер уже существует (400)
    """
    for existing in state.db:
        if existing["tracking"] == shipment.tracking:
            raise HTTPException(
                status_code=400, detail="Tracking number already exists"
            )

    new_shipment = {
        "id": state.next_id,
        "tracking": shipment.tracking,
        "origin": shipment.origin,
        "destination": shipment.destination,
        "status": shipment.status,
        "created_at": time.time(),
        "updated_at": time.time(),
    }
    state.db.append(new_shipment)
    state.next_id += 1

    print(f"📧 [gRPC → notifications-svc] Shipment {shipment.tracking} → {shipment.status}")

    return new_shipment


@app.get("/api/shipments", response_model=List[Shipment])
def get_all_shipments() -> List[dict]:
    """
    Получить все грузы.

    Returns:
        Список всех грузов в системе
    """
    return state.db


@app.get("/api/shipments/{shipment_id}", response_model=Shipment)
def get_shipment(shipment_id: int) -> dict:
    """
    Получить груз по ID.

    Args:
        shipment_id: Уникальный идентификатор груза

    Returns:
        Данные груза

    Raises:
        HTTPException: Если груз не найден (404)
    """
    for shipment in state.db:
        if shipment["id"] == shipment_id:
            return shipment
    raise HTTPException(status_code=404, detail="Shipment not found")


@app.get("/api/shipments/tracking/{tracking}", response_model=Shipment)
def get_shipment_by_tracking(tracking: str) -> dict:
    """
    Найти груз по трекинг-номеру.

    Args:
        tracking: Трекинг-номер для поиска

    Returns:
        Данные груза

    Raises:
        HTTPException: Если груз не найден (404)
    """
    for shipment in state.db:
        if shipment["tracking"] == tracking:
            return shipment
    raise HTTPException(status_code=404, detail="Shipment not found")


@app.put("/api/shipments/{shipment_id}", response_model=Shipment)
def update_shipment(shipment_id: int, shipment: ShipmentUpdate) -> dict:
    """
    Обновить данные груза.

    Args:
        shipment_id: Уникальный идентификатор груза
        shipment: Новые данные груза

    Returns:
        Обновлённые данные груза

    Raises:
        HTTPException: Если груз не найден (404)
    """
    for i, existing in enumerate(state.db):
        if existing["id"] == shipment_id:
            state.db[i] = {
                "id": shipment_id,
                "tracking": shipment.tracking,
                "origin": shipment.origin,
                "destination": shipment.destination,
                "status": shipment.status,
                "created_at": existing["created_at"],
                "updated_at": time.time(),
            }

            print(f"📧 [gRPC → notifications-svc] Shipment {shipment.tracking} → {shipment.status}")

            return state.db[i]
    raise HTTPException(status_code=404, detail="Shipment not found")


@app.delete("/api/shipments/{shipment_id}", status_code=204)
def delete_shipment(shipment_id: int) -> None:
    """
    Удалить груз по ID.

    Args:
        shipment_id: Уникальный идентификатор груза

    Raises:
        HTTPException: Если груз не найден (404)
    """
    for i, shipment in enumerate(state.db):
        if shipment["id"] == shipment_id:
            state.db.pop(i)
            return None
    raise HTTPException(status_code=404, detail="Shipment not found")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8130)
