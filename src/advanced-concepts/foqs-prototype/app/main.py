import os
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import FastAPI, HTTPException
import mysql.connector
from pydantic import BaseModel

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "foqsdb")
DB_USER = os.getenv("DB_USER", "foqsuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "foqspass")

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )

# Data Models

class EnqueueItem(BaseModel):
    namespace: str
    topic: str
    priority: int = 100
    delay_seconds: int = 0  # how many seconds from now
    payload: Optional[str] = None
    metadata: Optional[str] = None
    lease_duration: int = 30  # default lease duration


class DequeueRequest(BaseModel):
    namespace: str
    topic: str
    count: int = 1


class DequeuedItem(BaseModel):
    id: int
    namespace: str
    topic: str
    priority: int
    deliver_after: datetime
    payload: Optional[str]
    metadata: Optional[str]
    lease_until: Optional[datetime]


class AckNackRequest(BaseModel):
    item_ids: List[int]


class NackRequest(BaseModel):
    item_ids: List[int]
    delay_seconds: int = 0
    new_metadata: Optional[str] = None


app = FastAPI()


@app.post("/enqueue")
def enqueue_item(item: EnqueueItem):
    conn = get_db_connection()
    cursor = conn.cursor()
    deliver_after = datetime.now(timezone.utc) + timedelta(seconds=item.delay_seconds)
    sql = """
        INSERT INTO queue_items (namespace, topic, priority, deliver_after, payload, metadata)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    vals = (item.namespace, item.topic, item.priority, deliver_after, item.payload, item.metadata)
    cursor.execute(sql, vals)
    item_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "ok", "item_id": item_id}


@app.post("/dequeue")
def dequeue_items(req: DequeueRequest) -> List[DequeuedItem]:
    now_utc = datetime.now(timezone.utc)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 1) Find items that are:
    #  - Not acked
    #  - deliver_after <= now
    #  - lease_until is null or lease_until <= now (meaning they're not leased or lease expired)
    #  - matches namespace/topic
    #  - sorted by priority ascending, then deliver_after ascending
    #  - limit to `count`
    sql_select = """
    SELECT id, namespace, topic, priority, deliver_after, payload, metadata
    FROM queue_items
    WHERE 
        acked=0
        AND namespace = %s
        AND topic = %s
        AND deliver_after <= %s
        AND (lease_until IS NULL OR lease_until <= %s)
    ORDER BY priority ASC, deliver_after ASC, id ASC
    LIMIT %s
    """
    cursor.execute(sql_select, (req.namespace, req.topic, now_utc, now_utc, req.count))
    rows = cursor.fetchall()

    if not rows:
        cursor.close()
        conn.close()
        return []
    

    # 2) For each selected item, update lease_until to (now + default lease_duration).
    #    We'll store a default lease duration (30s), but in a more advanced system,
    #    you might store it in the item row or pass it in the DequeueRequest.
    lease_duration_seconds = 30
    lease_until = datetime.now(timezone.utc) + timedelta(seconds=lease_duration_seconds)
    
    item_ids = [row["id"] for row in rows]
    sql_update_lease = """
    UPDATE queue_items
    SET lease_until = %s
    WHERE id IN ({})
    """.format(",".join(["%s"] * len(item_ids)))
    cursor.execute(sql_update_lease, (lease_until, *item_ids))
    conn.commit()

    dequeued_items = []
    for r in rows:
        di = DequeuedItem(
            id=r["id"],
            namespace=r["namespace"],
            topic=r["topic"],
            priority=r["priority"],
            deliver_after=r["deliver_after"],
            payload=r["payload"],
            metadata=r["metadata"],
            lease_until=lease_until
        )
        dequeued_items.append(di)

    cursor.close()
    conn.close()
    return dequeued_items


@app.post("/ack")
def ack_items(req: AckNackRequest):
    if not req.item_ids:
        raise HTTPException(status_code=400, detail="No item IDs provided")

    conn = get_db_connection()
    cursor = conn.cursor()

    sql = """
    UPDATE queue_items
    SET acked = 1
    WHERE id IN ({})
    """.format(",".join(["%s"] * len(req.item_ids)))
    cursor.execute(sql, (*req.item_ids,))
    conn.commit()

    updated_count = cursor.rowcount
    cursor.close()
    conn.close()

    return {"status": "ok", "acked_count": updated_count}


@app.post("/nack")
def nack_items(req: NackRequest):
    """
    Mark items for redelivery. Optionally set a delay and update metadata.
    """
    if not req.item_ids:
        raise HTTPException(status_code=400, detail="No item IDs provided")

    now_utc = datetime.now(timezone.utc)
    new_deliver_after = now_utc + datetime.timedelta(seconds=req.delay_seconds)

    conn = get_db_connection()
    cursor = conn.cursor()

    # We also reset lease_until = NULL so they become available after that new deliver_after
    # If the user wants to update metadata, do it too:
    sql_set = ["deliver_after = %s", "lease_until = NULL"]
    vals = [new_deliver_after]

    if req.new_metadata is not None:
        sql_set.append("metadata = %s")
        vals.append(req.new_metadata)

    sql_update = f"""
    UPDATE queue_items
    SET {', '.join(sql_set)}
    WHERE id IN ({','.join(['%s'] * len(req.item_ids))})
    """

    cursor.execute(sql_update, (*vals, *req.item_ids))
    conn.commit()

    updated_count = cursor.rowcount
    cursor.close()
    conn.close()

    return {"status": "ok", "nacked_count": updated_count}



@app.get("/topics")
def get_active_topics(namespace: str):
    now_utc = datetime.now(timezone.utc)
    conn = get_db_connection()
    cursor = conn.cursor()

    # We define "active" as any item that is not acked and is either ready or will be ready soon.
    # This is a simplistic approach. You can refine it to exactly match your needs.
    sql = """
    SELECT DISTINCT topic
    FROM queue_items
    WHERE acked=0
      AND namespace=%s
      AND (deliver_after <= %s OR deliver_after > %s)
    """
    cursor.execute(sql, (namespace, now_utc, now_utc))

    results = cursor.fetchall()
    cursor.close()
    conn.close()

    active_topics = [r[0] for r in results]
    return {"namespace": namespace, "active_topics": active_topics}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)