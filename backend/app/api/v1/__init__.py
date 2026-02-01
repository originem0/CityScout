from fastapi import APIRouter

from app.api.v1.cities import router as cities_router
from app.api.v1.keywords import router as keywords_router
from app.api.v1.sources import router as sources_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.manual_import import router as import_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.rent import router as rent_router
from app.api.v1.forum import router as forum_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.export import router as export_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.settings import router as settings_router
from app.api.v1.logs import router as logs_router
from app.api.v1.ws import router as ws_router

router = APIRouter()

router.include_router(cities_router)
router.include_router(keywords_router)
router.include_router(sources_router)
router.include_router(tasks_router)
router.include_router(import_router)
router.include_router(jobs_router)
router.include_router(rent_router)
router.include_router(forum_router)
router.include_router(analysis_router)
router.include_router(export_router)
router.include_router(dashboard_router)
router.include_router(settings_router)
router.include_router(logs_router)
router.include_router(ws_router)
