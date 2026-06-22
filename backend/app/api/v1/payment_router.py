from decimal import Decimal
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
import hmac
import hashlib

from pydantic import BaseModel

from app.api.depends.cache import CacheDep
from app.api.depends.uow import UOWDepInit, get_uow_init, get_uow_init_with_isolation_level
from app.core.config import settings
from urllib.parse import quote

from app.services.video import VideoService
from app.api.depends.user import get_user
from app.domain.entitites import BalanceEntity, UserEntity
import aiohttp

from app.repositories.implementations.sqlalchemy.uow import UOW
from app.services.payment import PaymentService
from app.schemas.schemas import ConfirmationTokenResponse, StatusResponse
from app.api.depends.services import VideoServiceDep

router = APIRouter(prefix="/api/payment")
    

from fastapi import APIRouter, Request, HTTPException
from app.services.video import VideoService, VideoServiceException
from decimal import Decimal

router = APIRouter(prefix="/api/payment")


@router.post("/notification")
async def notification(
    request: Request,
    cache: CacheDep,
    uow: UOW = Depends(get_uow_init_with_isolation_level("SERIALIZABLE")),
) -> StatusResponse:
    data: dict = await request.json()

    event: str = data.get("event")
    obj: dict = data.get("object")

    if not event or not obj:
        raise HTTPException(400, "Invalid payload")

    payment_id_provider: str = obj.get("id")
    amount = Decimal(obj["amount"]["value"])

    metadata = obj.get("metadata", {})
    payment_id = metadata.get("payment_id")
    user_id = int(metadata.get("user_id"))
    subscription_id = int(metadata.get("subscription_id"))

    if not payment_id:
        raise HTTPException(400, "No payment_id in metadata")

    video_service = VideoService(uow, cache)

    payment_service = PaymentService(uow, cache, video_service)
    await payment_service.process_notification(
        event=event,
        amount=amount,
        payment_id=payment_id,
        user_id=user_id,
        subscription_id=subscription_id,
        operation_id=payment_id_provider,
    )

    return {"status": "ok"}
    

@router.post("/confirmation_token")
async def confirmation_token(
    sub_id: int,
    uow: UOWDepInit,
    cache: CacheDep,
    video_service: VideoServiceDep,
    user: UserEntity = Depends(get_user)
) -> ConfirmationTokenResponse:
    payment_data = await PaymentService(uow, cache, video_service).create_payment(user.id, sub_id)

    idempotency_key = str(uuid.uuid4())
    price: Decimal = payment_data["price"]

    payload = {
        "amount": {
            "value": format(price.quantize(Decimal("0.01")), "f"),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "embedded"
        },
        "capture": True,
        "description": f"Subscription {sub_id}",
        "metadata": {
            "payment_id": str(payment_data["payment_id"]),
            "user_id": user.id,
            "subscription_id": sub_id
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url="https://api.yookassa.ru/v3/payments",
            headers={
                "Idempotence-Key": idempotency_key,
                "Content-Type": "application/json"
            },
            json=payload,
            auth=aiohttp.BasicAuth(
                login=str(settings.SHOP_ID),
                password=settings.SECRET_KEY_YOUKASSA
            )
        ) as rsp:
            if rsp.status not in (200, 201):
                raise HTTPException(status_code=400, detail=await rsp.text())

            data = await rsp.json()

            confirmation = data.get("confirmation", {})
            token = confirmation.get("confirmation_token")

            if not token:
                raise HTTPException(500, "No confirmation_token")

            return {
                "confirmation_token": token
            }
            
@router.post("/balance")
async def notification(
    uow: UOWDepInit,
    cache: CacheDep,
    user: UserEntity = Depends(get_user)
) -> BalanceEntity:
    video_service = VideoService(uow, cache)
    payment_service = PaymentService(uow, cache, video_service)
    balance = await payment_service.get_balance(user.id)

    return balance