from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID

class PaymentMethodSchema(BaseModel):
    payment_method_id: Optional[str] = None

class PaymentIntentResponse(BaseModel):
    payment_intent_id: str
    client_secret: str
    status: str
    amount: float
    platform_fee: float
    driver_payout: float
    
class RefundRequest(BaseModel):
    reason: Optional[str] = "requested_by_customer"

class PaymentCaptureResponse(BaseModel):
    status: str
    charge_id: str
    transfer_id: str
    amount_captured: float
    driver_payout: float
    platform_fee: float

class RefundResponse(BaseModel):
    status: str
    refund_id: str
    amount_refunded: float
    percentage: float
