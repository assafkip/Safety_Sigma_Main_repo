# SQL Field Mapping Guide

## Overview
Map Sigma's `log_field_targets` to your database table columns for threat detection queries.

## Common Field Mappings

| Sigma Field | SQL Column Examples | Data Type |
|------------|-------------------|-----------|
| `message` | `message`, `event_text`, `log_content` | TEXT, VARCHAR |
| `caller_id` | `caller_id`, `phone_number`, `source_phone` | VARCHAR(20) |
| `payment_method` | `payment_type`, `transaction_method` | VARCHAR(50) |
| `redirect_url` | `url`, `redirect_target`, `link_url` | TEXT |
| `platform` | `app_name`, `service_name`, `platform` | VARCHAR(100) |

## Schema Design
```sql
CREATE TABLE fraud_events (
    id BIGINT PRIMARY KEY,
    timestamp DATETIME,
    message TEXT,
    caller_id VARCHAR(20),
    payment_method VARCHAR(50),
    redirect_url TEXT,
    platform VARCHAR(100),
    -- Sigma metadata
    rule_owner VARCHAR(50) DEFAULT 'Sigma',
    severity_label VARCHAR(20) DEFAULT 'Medium',
    sla_hours INT DEFAULT 48,
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fraud_events_message ON fraud_events(message(100));
CREATE INDEX idx_fraud_events_caller ON fraud_events(caller_id);
CREATE INDEX idx_fraud_events_payment ON fraud_events(payment_method);
```

## Query Examples
```sql
-- Pattern matching for behavioral indicators
SELECT * FROM fraud_events 
WHERE message REGEXP 'gift cards?' 
   OR message REGEXP 'wire transfer' 
   OR message REGEXP 'crypto(currency)?'
ORDER BY timestamp DESC 
LIMIT 100;

-- Caller ID spoofing detection
SELECT caller_id, COUNT(*) as frequency
FROM fraud_events 
WHERE message LIKE '%spoof%caller%ID%'
GROUP BY caller_id
HAVING frequency > 1;

-- Platform redirect analysis
SELECT platform, redirect_url, COUNT(*) as cases
FROM fraud_events 
WHERE message REGEXP 'redirect.*(WhatsApp|Telegram|Signal)'
GROUP BY platform, redirect_url
ORDER BY cases DESC;
```

## Performance Tips
- Use appropriate indexes on frequently searched columns
- Consider full-text search indexes for message content
- Partition large tables by date for better query performance
- Use `EXPLAIN` to analyze query performance