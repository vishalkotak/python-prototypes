-- ./db/init.sql
CREATE TABLE IF NOT EXISTS queue_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    namespace VARCHAR(255) NOT NULL,
    topic VARCHAR(255) NOT NULL,
    priority INT NOT NULL,
    deliver_after DATETIME NOT NULL,
    lease_until DATETIME NULL,
    payload TEXT,
    metadata TEXT,
    acked TINYINT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_namespace_topic ON queue_items (namespace, topic);
CREATE INDEX idx_priority_deliver_after ON queue_items (priority, deliver_after);
