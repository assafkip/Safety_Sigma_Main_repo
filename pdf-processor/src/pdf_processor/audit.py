def append_jsonl(record, path="logs/audit.jsonl"):
    import json
    import os

    # Ensure the directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, 'a') as f:
        json_record = json.dumps(record)
        f.write(json_record + '\n')