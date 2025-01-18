
# Steps executed before execution:
# 1. docker pull redis
# 2. docker run --name redis-server -d -p 6379:6379 redis
# 3. docker exec -it redis-server redis-cli

import redis
import time

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def main():
    # Expected output:
    # User 3 status: None
    # User 1 status: 1737212862
    # User 2 status: 1737212862
    # User 1 status after idle time: None
    # User 2 status after idle time: None
    current_epoch_time = int(time.time())
    r.set("user1", current_epoch_time, ex=30)
    r.set("user2", current_epoch_time, ex=30)
    
    user_3_status = r.get("user3")
    print(f"User 3 status: {user_3_status}")

    for _ in range(6):
        time.sleep(10)
        r.set("user1", current_epoch_time, ex=30)
        r.set("user2", current_epoch_time, ex=30)

    user_1_status = r.get("user1")
    user_2_status = r.get("user2")
    print(f"User 1 status: {user_1_status}")
    print(f"User 2 status: {user_2_status}")

    time.sleep(35)
    user_1_status = r.get("user1")
    user_2_status = r.get("user2")
    print(f"User 1 status after idle time: {user_1_status}")
    print(f"User 2 status after idle time: {user_2_status}")

if __name__ == "__main__":
    main()
