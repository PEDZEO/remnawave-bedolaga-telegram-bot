from aiogram import Bot

from app.services.nalogo_queue_service import nalogo_queue_service
from app.services.payment_service import PaymentService
from app.services.payment_verification_service import auto_payment_verification_service


def setup_payment_runtime(bot: Bot) -> PaymentService:
    payment_service = PaymentService(bot)
    auto_payment_verification_service.set_payment_service(payment_service)

    if payment_service.nalogo_service:
        nalogo_queue_service.set_nalogo_service(payment_service.nalogo_service)
        nalogo_queue_service.set_bot(bot)

    return payment_service
