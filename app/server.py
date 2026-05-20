from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn
import time

app = FastAPI(title="shipments-svc-s01")

class ShipmentCreate(BaseModel):
    tracking: str = Field(..., min_length=1)
    origin: str = Field(..., min_length=1)
    destination: str = Field(..., min_length=1)
    status: str = Field(default="pending")

class ShipmentUpdate(BaseModel):
    tracking: str = Field(..., min_length=1)
    origin: str = Field(..., min_length=1)
    destination: str = Field(..., min_length=1)
    status: str = Field(default="pending")

class Shipment(BaseModel):
    id: int
    tracking: str
    origin: str
    destination: str
    status: str
    created_at: float
    updated_at: float

db: List[dict] = []
next_id = 1

@app.get("/")
def root():
    return {"service": "shipments-svc-s01", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/api/shipments", response_model=Shipment, status_code=201)
def create_shipment(shipment: ShipmentCreate):
    global next_id
    # Проверка уникальности трекинг-номера
    for existing in db:
        if existing["tracking"] == shipment.tracking:
            raise HTTPException(status_code=400, detail="Tracking number already exists")
    
    new_shipment = {
        "id": next_id,
        "tracking": shipment.tracking,
        "origin": shipment.origin,
        "destination": shipment.destination,
        "status": shipment.status,
        "created_at": time.time(),
        "updated_at": time.time()
    }
    db.append(new_shipment)
    next_id += 1
    return new_shipment

@app.get("/api/shipments", response_model=List[Shipment])
def get_all_shipments():
    return db

@app.get("/api/shipments/{shipment_id}", response_model=Shipment)
def get_shipment(shipment_id: int):
    for shipment in db:
        if shipment["id"] == shipment_id:
            return shipment
    raise HTTPException(status_code=404, detail="Shipment not found")

@app.get("/api/shipments/tracking/{tracking}", response_model=Shipment)
def get_shipment_by_tracking(tracking: str):
    for shipment in db:
        if shipment["tracking"] == tracking:
            return shipment
    raise HTTPException(status_code=404, detail="Shipment not found")

@app.put("/api/shipments/{shipment_id}", response_model=Shipment)
def update_shipment(shipment_id: int, shipment: ShipmentUpdate):
    for i, existing in enumerate(db):
        if existing["id"] == shipment_id:
            db[i] = {
                "id": shipment_id,
                "tracking": shipment.tracking,
                "origin": shipment.origin,
                "destination": shipment.destination,
                "status": shipment.status,
                "created_at": existing["created_at"],
                "updated_at": time.time()
            }
            return db[i]
    raise HTTPException(status_code=404, detail="Shipment not found")

@app.delete("/api/shipments/{shipment_id}", status_code=204)
def delete_shipment(shipment_id: int):
    for i, shipment in enumerate(db):
        if shipment["id"] == shipment_id:
            db.pop(i)
            return None
    raise HTTPException(status_code=404, detail="Shipment not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8130)