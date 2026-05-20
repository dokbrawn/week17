from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="notifications-svc-s01")

class NotificationRequest(BaseModel):
    tracking: str
    status: str
    recipient_email: str = "user@example.com"

class NotificationResponse(BaseModel):
    success: bool
    message: str

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/api/notify", response_model=NotificationResponse)
def send_notification(req: NotificationRequest):
    
    print(f"📧 [notifications-svc] Отправка уведомления: {req.tracking} → {req.status}")
    print(f"   Получатель: {req.recipient_email}")
    return NotificationResponse(success=True, message=f"Notification sent for {req.tracking}")

@app.get("/api/notifications")
def get_notifications():
    return {"notifications": []}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8131)