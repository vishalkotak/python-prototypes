# FOQS-Prototype

A minimal prototype inspired by the Facebook Ordered Queueing Service (FOQS). It demonstrates how to build a distributed, priority-based queue using:

- **Python** (with [FastAPI](https://fastapi.tiangolo.com/))
- **MySQL**
- **Docker** (with Docker Compose)

This prototype includes essential operations:

1. **Enqueue**: Insert items into the queue with an optional delay.
2. **Dequeue**: Retrieve items in order of priority and release them with a lease.
3. **Ack**: Acknowledge successful processing of dequeued items.
4. **Nack**: Request re-delivery of items (with optional delay and metadata update).
5. **Get Active Topics**: List topics with unacknowledged items.

> **Note**: This is a simplified demo. It does not fully implement all features of a production-scale FOQS (like sophisticated sharding, replication, advanced lease management, etc.).

---
