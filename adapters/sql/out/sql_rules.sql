-- Sigma pattern (span: s_amt)
SELECT * FROM events WHERE REGEXP_LIKE(message, '.*$1,998.88.*');

-- Sigma pattern (span: s_acc)
SELECT * FROM events WHERE REGEXP_LIKE(message, '.*Zelle ID 123456789.*');