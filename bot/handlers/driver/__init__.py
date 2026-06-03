"""Driver-facing handlers for GPS dispatch (Card 26)."""

from aiogram import Router

from .availability import router as availability_router
from .job_offer import router as job_offer_router
from .registration import router as registration_router

router = Router()
router.include_router(registration_router)
router.include_router(availability_router)
router.include_router(job_offer_router)
