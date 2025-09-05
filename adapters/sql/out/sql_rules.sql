-- Sigma pattern (span: span_123)
SELECT * FROM events WHERE REGEXP_LIKE(message, '.*gift cards.*');

-- Sigma pattern (span: span_456)
SELECT * FROM events WHERE REGEXP_LIKE(message, '.*wire transfer.*');