"""Run the OTEM Temporal worker (polls task queue and executes workflows/activities)."""

from __future__ import annotations

import asyncio
import logging

from src.otem_temporal.activities import OTEM_ACTIVITIES
from src.otem_temporal.config import (
    OTEM_TEMPORAL_NAMESPACE,
    OTEM_TEMPORAL_TASK_QUEUE,
    TEMPORAL_ADDRESS,
    otem_temporal_enabled,
)
from src.otem_temporal.workflows import OTEMExecutionTemporalWorkflow

logger = logging.getLogger(__name__)


async def run_worker() -> None:
    if not otem_temporal_enabled():
        raise RuntimeError(
            "Cannot start OTEM Temporal worker: set AAIS_OTEM_TEMPORAL_ENABLED=1 and pip install temporalio"
        )
    from temporalio.client import Client
    from temporalio.worker import Worker

    client = await Client.connect(TEMPORAL_ADDRESS, namespace=OTEM_TEMPORAL_NAMESPACE)
    worker = Worker(
        client,
        task_queue=OTEM_TEMPORAL_TASK_QUEUE,
        workflows=[OTEMExecutionTemporalWorkflow],
        activities=OTEM_ACTIVITIES,
    )
    logger.info(
        "OTEM Temporal worker listening on queue=%s address=%s namespace=%s",
        OTEM_TEMPORAL_TASK_QUEUE,
        TEMPORAL_ADDRESS,
        OTEM_TEMPORAL_NAMESPACE,
    )
    await worker.run()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
