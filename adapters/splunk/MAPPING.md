# Splunk Field Mapping Guide

## Overview
Map Sigma's `log_field_targets` to your indexes/sourcetypes for optimal detection coverage.

## Common Field Mappings

| Sigma Field | Splunk Field Examples | Description |
|------------|----------------------|-------------|
| `message` | `_raw`, `msg`, `event_message` | Main message content |
| `caller_id` | `caller_id`, `phone_number`, `source_number` | Phone number fields |
| `payment_method` | `payment_type`, `transaction_method` | Payment/transaction fields |
| `redirect_url` | `url`, `redirect`, `link` | URL/redirect fields |
| `platform` | `app_name`, `service`, `platform` | Application/platform fields |

## Index Configuration
- **Recommended indexes**: `fraud`, `security`, `transactions`
- **Sourcetypes**: `fraud:scam`, `security:alerts`, `comms:sms`

## Performance Tips
- Use `tstats` for high-volume searches
- Add time bounds: `earliest=-7d@d latest=now`
- Consider field extraction optimization for frequently searched fields

## Example Usage
```splunk
search index=fraud sourcetype=scam _raw="gift cards"
| eval rule_owner="Sigma", sla_hours=48
| table _time, _raw, caller_id, payment_method
```