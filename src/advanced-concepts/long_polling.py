import asyncio
import time

import uvicorn
from fastapi import FastAPI

app = FastAPI()
jobs = dict()


@app.post("/submit")
async def submit():
    job_id = f"job-{time.time()}"
    jobs[job_id] = 0
    asyncio.create_task(update_job(job_id))
    return {"job_id": job_id}


@app.get("/check-status")
async def check_status(job_id: str):
    while jobs[job_id] != 100:
        await asyncio.sleep(5)
    return {"job_id": f"{jobs[job_id]}"}


async def update_job(job_id: str):
    while jobs[job_id] != 100:
        jobs[job_id] += 10
        print(f"{job_id} progress {jobs[job_id]}")
        await asyncio.sleep(5)


if __name__ == "__main__":
    uvicorn.run("long_polling:app", host="127.0.0.1", port=8000, reload=True)
