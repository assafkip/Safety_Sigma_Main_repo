# Elastic Field Mapping Guide

## Overview
Map Sigma's `log_field_targets` to your Elasticsearch index fields for effective threat detection.

## Common Field Mappings

| Sigma Field | Elastic Field Examples | Mapping Type |
|------------|----------------------|--------------|
| `message` | `message`, `event.original`, `log.message` | text/keyword |
| `caller_id` | `source.phone`, `caller.number`, `phone_number` | keyword |
| `payment_method` | `transaction.method`, `payment.type` | keyword |
| `redirect_url` | `url.full`, `redirect.target`, `link` | keyword |
| `platform` | `service.name`, `app.name`, `platform` | keyword |

## Index Template Example
```json
{
  "mappings": {
    "properties": {
      "message": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
      "caller_id": {"type": "keyword"},
      "payment_method": {"type": "keyword"},
      "sigma_metadata": {
        "properties": {
          "rule_owner": {"type": "keyword"},
          "severity_label": {"type": "keyword"},
          "sla": {"type": "integer"}
        }
      }
    }
  }
}
```

## Query Examples
```json
{
  "query": {
    "bool": {
      "should": [
        {"regexp": {"message": ".*gift cards.*"}},
        {"regexp": {"event.original": ".*wire transfer.*"}}
      ],
      "minimum_should_match": 1
    }
  }
}
```

## Performance Optimization
- Use `keyword` fields for exact matches
- Consider `wildcard` field type for pattern matching
- Set appropriate `ignore_above` limits for text fields