import json
import httpx
import sys
sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://localhost:8000/rewrite_reply"
TEST_CASES_PATH = "data/test_cases_example.json"

# Load test cases
with open(TEST_CASES_PATH, "r") as f:
    test_cases = json.load(f)

# Load policies
with open("data/policies_example.json", "r") as f:
    policies = json.load(f)

for idx, case in enumerate(test_cases, 1):
    payload = {
        "agent_id": f"test_agent_{idx}",
        "channel": "test",
        "context": case["context"],
        "draft_reply": case["draft_reply"],
        "policies": policies
    }
    response = httpx.post(API_URL, json=payload, timeout=30.0)
    result = response.json()
    print(f"Test Case {idx}:")
    print(f"Input Draft Reply: {case['draft_reply']}")
    print("Risk Level:", result.get('risk_level'))
    print("Confidence Score:", result.get('confidence_score'))
    print("Issues Detected:", ', '.join(result.get('issues_detected', [])))
    print("Action:", result.get('action'))
    print("Safe Reply:", result.get('safe_reply'))
    print("Explanation:", result.get('explanation'))
    if result.get('before_after_diff'):
        print("Diff:", result['before_after_diff'])
    if result.get('violation_details'):
        print("Violations:")
        for v in result['violation_details']:
            print(f"  - Policy: {v.get('policy_id')} | Phrase: '{v.get('violated_phrase')}' | Pos: {v.get('position_in_text')}")
    print("Escalate:", result.get('escalate'))
    print("-"*40)
