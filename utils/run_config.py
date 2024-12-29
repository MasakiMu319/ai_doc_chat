import os
from pydantic import BaseModel, Field


class RunConfig(BaseModel):
    """
    Configuration for execution of tasks.
    """

    timeout: int = Field(
        default=180,
        description="Maximum time (in seconds) to wait for a single operation.",
    )
    max_retries: int = Field(
        default=10,
        description="Maximum number of retry attempts.",
    )
    max_wait: int = Field(
        default=60,
        description="Maximum wait time (in seconds) between retries.",
    )
    max_workers: int = Field(
        default=os.cpu_count() or 4,
        description="Maximum number of concurrent workers.",
    )
