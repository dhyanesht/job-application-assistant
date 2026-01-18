import csv
from pathlib import Path
from datetime import datetime
import logging
import aiofiles
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def generate_timestamped_filename(prefix: str, suffix: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"{prefix}_{timestamp}.{suffix}"


def write_jobs_to_csv(jobs: list[dict], output_dir: str, prefix="dice_jobs"):
    if not jobs:
        logger.warning("No jobs to write to CSV")
        return None

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    filename = generate_timestamped_filename(prefix, "csv")
    full_path = output_path / filename

    with full_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=jobs[0].keys())
        writer.writeheader()
        writer.writerows(jobs)

    logger.info("CSV written", extra={"path": str(full_path), "jobs": len(jobs)})
    return full_path

async def write_jobs_to_jsonl_async(
    jobs: list[dict],
    output_dir: str,
    prefix: str = "dice_jobs",
    append: bool = False,
    jsonl_path: Path | None = None,
):
    if not jobs:
        logger.warning("No jobs to write to JSONL")
        return None

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Create file once, reuse when appending
    if jsonl_path is None:
        filename = generate_timestamped_filename(prefix, "jsonl")
        jsonl_path = output_path / filename

    mode = "a" if append else "w"

    async with aiofiles.open(jsonl_path, mode=mode, encoding="utf-8") as f:
        for job in jobs:
            await f.write(json.dumps(job, ensure_ascii=False) + "\n")

    logger.info(
        "JSONL write complete",
        extra={
            "path": str(jsonl_path),
            "jobs_written": len(jobs),
            "append": append,
        },
    )

    return jsonl_path