from celery import Celery
from pathlib import Path
import os
from app.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

celery = Celery(
    "jarvis_v11",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.tasks"],
)
celery.conf.task_track_started = True
celery.conf.result_expires = 3600

if CELERY_BROKER_URL.startswith("filesystem://"):
    fs_role = os.getenv("CELERY_FS_ROLE", "producer").strip().lower() or "producer"
    fs_base = Path(os.getenv("CELERY_FS_BASE", ".runtime/celery-broker")).resolve()
    default_incoming = fs_base / "incoming"
    default_outgoing = fs_base / "outgoing"

    explicit_in = os.getenv("CELERY_FS_IN")
    explicit_out = os.getenv("CELERY_FS_OUT")
    if explicit_in and explicit_out:
        data_in = Path(explicit_in).resolve()
        data_out = Path(explicit_out).resolve()
    elif fs_role == "worker":
        data_in = default_outgoing
        data_out = default_incoming
    else:
        data_in = default_incoming
        data_out = default_outgoing

    data_processed = Path(os.getenv("CELERY_FS_PROCESSED", str(fs_base / "processed"))).resolve()

    data_in.mkdir(parents=True, exist_ok=True)
    data_out.mkdir(parents=True, exist_ok=True)
    data_processed.mkdir(parents=True, exist_ok=True)

    celery.conf.broker_transport_options = {
        "data_folder_in": str(data_in),
        "data_folder_out": str(data_out),
        "data_folder_processed": str(data_processed),
    }

if hasattr(celery, "autodiscover_tasks"):
    celery.autodiscover_tasks(["app"], force=True)
