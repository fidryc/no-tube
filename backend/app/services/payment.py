from decimal import Decimal
import decimal
from enum import Enum
from typing import Optional

from app.infrastructure.cache.interface import ICache
from app.repositories.interfaces.uow import IUOW
from app.domain.enums import PaymentStatuses
from app.repositories.exceptions import BaseRepositoryException
from app.repositories.filter.filter import Filter
from app.services.video import VideoService
from app.services.base_errs import BaseServiceErrs
from app.services.exception import BaseServiceException
from app.services.handler import get_handler


class PaymentErrs(BaseServiceErrs):
    NO_RIGHTS = "NO_RIGHTS"
    NO_FOUND = "NO_FOUND"
    
    
class PaymentEvent(Enum):
    SUCCESS = "payment.succeeded" # Платеж прошел успешно
    WAITING = "payment.waiting_for_capture" # Платеж ожидает подверждения
    CANCEL = "payment.canceled" # Платеж отменен
    REFUND = "refund.succeeded" # Возврат средств

    
class PaymentServiceException(BaseServiceException):
    def __init__(self, *args, err: PaymentErrs = BaseServiceErrs.UNKNOWN, **kwargs):
        super().__init__(*args, **kwargs)
        self.err = err

payment_service_handler = get_handler(PaymentServiceException)
    
class PaymentService:
    def __init__(self, uow: IUOW, cache: ICache, video_service: VideoService):
        self.uow = uow
        self.cache = cache
        self.video_service = video_service
    
    @payment_service_handler("PaymentService.create_balance")
    async def create_balance(self, user_id: int) -> str:
        id = await self.uow.balance_repo.add(
            {
                "user_id": user_id,
            }
        )
        return str(id)
    
    @payment_service_handler("PaymentService.update_balance")   
    async def update_balance(self, user_id: int, amount: Decimal):
        if amount < 0:
            raise PaymentServiceException("Amount le 0", err=PaymentErrs.INVALID_DATA)
        
        objs = await self.uow.balance_repo.get_by_filters(
            Filter("user_id", user_id)
        )
        
        if not objs:
            raise PaymentServiceException("Balance not exists", err=PaymentErrs.NO_FOUND) 
        
        balance = objs[0]
        
        await self.uow.balance_repo.update_many(
            Filter("user_id", user_id),
            {
                "amount": balance.amount + amount
            }
        )
    
    @payment_service_handler("PaymentService.create_payment")       
    async def create_payment(self, user_id: int, sub_id: int) -> dict:
        sub = await self.uow.author_subscriptions_repo.get_by_id(sub_id)
        if not sub:
            raise PaymentServiceException("Not found subscription", err=PaymentErrs.NO_FOUND)
        
        price = sub.price
        payment_id = await self.uow.payment_repo.add(
            {
                "user_id": user_id,
                "author_subscription_id": sub.id,
                "status": PaymentStatuses.PENDING,
                "amount": price,
            }
        )
        
        return {
            "payment_id": payment_id,
            "price": price
        }
    
    @payment_service_handler("PaymentService.payment_sub_processing")    
    async def payment_sub_processing(self, payment_id: str, amount: str | decimal.Decimal, operation_id: Optional[str] = None) -> int:
        await self.uow.payment_repo.update_many(
            Filter("id", payment_id),
            {
                "provider_payment_id": operation_id,
            }
        )
        
        payment = await self.uow.payment_repo.get_by_id(payment_id)

        if not payment:
            raise PaymentServiceException("Not found payment", err=PaymentErrs.NO_FOUND)
        if payment.status == PaymentStatuses.PAID:
            return
        
        # Проверка, что сумма платежа соответствует сумме подписки
        if decimal.Decimal(amount).normalize() != payment.amount.normalize():
            payment_id = await self.uow.payment_repo.update_many(
                Filter("id", payment_id),
                {
                    "status": PaymentStatuses.FAILED
                }
            )
            return
        subscription_id = payment.author_subscription_id
        subscriber_id = payment.user_id
        sub = await self.uow.author_subscriptions_repo.get_by_id(subscription_id)
        if not sub:
            raise PaymentServiceException("Not found subscription", err=PaymentErrs.NO_FOUND)
        
        author_user_id = sub.author_id
        
        # Пополняем баланс для владельца подписки
        await self.update_balance(author_user_id, amount)
        
        user_sub_id = await self.video_service.subscribe(subscriber_id, subscription_id)
        
        # Фиксируем, что платеж завершен корректно
        await self.uow.payment_repo.update_many(
            Filter("id", payment_id),
            {
                "status": PaymentStatuses.PAID
            }
        )
        
        return user_sub_id
    
    @payment_service_handler("PaymentService.process_notification")
    async def process_notification(
        self,
        event: str,
        amount: decimal.Decimal,
        payment_id: str,
        user_id: int,
        subscription_id: int,
        operation_id: Optional[str] = None
    ):
        await self.validate_notification_payment_data(
            payment_id=payment_id,
            user_id=user_id,
            subscription_id=subscription_id,
        )
        if event == PaymentEvent.SUCCESS.value:
            await self.payment_sub_processing(
                payment_id=payment_id,
                amount=amount,
                operation_id=operation_id
            )
            return
        
        elif event == PaymentEvent.WAITING.value:
            return
        elif event == PaymentEvent.CANCEL.value:
            await self.uow.payment_repo.update_many(
                Filter("id", payment_id),
                {
                    "status": PaymentStatuses.FAILED
                }
            )
        elif event == PaymentEvent.REFUND.value:
            # Возврат средств
            return
    
    @payment_service_handler("PaymentService.validate_notification_payment_data")       
    async def validate_notification_payment_data(self, payment_id: str, user_id: int, subscription_id: int):
        payment = await self.uow.payment_repo.get_by_id(payment_id)
        if not payment:
            raise PaymentServiceException("Not found payment", err=PaymentErrs.NO_FOUND)
        
        if payment.user_id != user_id or \
            payment.author_subscription_id != subscription_id:
                raise PaymentServiceException("Not found payment", err=PaymentErrs.NO_FOUND)