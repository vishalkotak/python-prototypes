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
    asyncio.create_task(update(job_id))
    return {"jobId": job_id}


@app.get("/check-status")
async def check_status(job_id: str):
    if job_id not in jobs:
        return {"error": "Job Id Not Found"}
    return {"job_id": jobs[job_id]}


async def update(job_id: strß):
    while jobs[job_id] < 100:
        await asyncio.sleep(1)
        jobs[job_id] = jobs[job_id] + 10
        print(f"{job_id} progress: {jobs[job_id]}")


if __name__ == "__main__":
    uvicorn.run("short_polling:app", host="127.0.0.1", port=8000, reload=True)
