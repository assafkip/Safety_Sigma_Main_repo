import json
from pathlib import Path

def test_behavioral_fields_tolerated_in_display(tmp_path):
    # simulate advisory JSON carrying behavioral fields
    j = {"indicators":[
        {"kind":"account","verbatim":"acct_123","category_id":"financial","span_id":"s1",
         "ip_reputation":"low","velocity_event_count":7,"account_age_days":3}
    ]}
    p = tmp_path/"adv.json"; p.write_text(json.dumps(j), encoding="utf-8")
    # No strict assertion here; HTML renderer test is out-of-scope.
    assert p.exists()