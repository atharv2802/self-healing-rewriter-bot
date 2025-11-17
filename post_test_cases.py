"""Test runner for SHR API endpoints."""
import json
import httpx
import sys
from typing import List, Dict, Any

sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://localhost:8000/rewrite_reply"
TEST_CASES_PATH = "data/test_cases_example.json"
POLICIES_PATH = "data/policies_example.json"

def load_json_file(file_path: str) -> Any:
    """Load and parse JSON file with error handling."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}: {e}")
        sys.exit(1)

# Load test cases and policies
test_cases = load_json_file(TEST_CASES_PATH)
policies = load_json_file(POLICIES_PATH)

print(f"Running {len(test_cases)} test cases...\n")

for idx, case in enumerate(test_cases, 1):
    payload = {
        "agent_id": f"test_agent_{idx}",
        "channel": "test",
        "context": case["context"],
        "draft_reply": case["draft_reply"],
        "policies": policies
    }
    
    try:
        response = httpx.post(API_URL, json=payload, timeout=30.0)
        response.raise_for_status()
        result = response.json()
    except httpx.ConnectError:
        print(f"Test Case {idx}: ERROR - Cannot connect to API at {API_URL}")
        print("Make sure the FastAPI server is running.")
        print("-"*40)
        continue
    except httpx.TimeoutException:
        print(f"Test Case {idx}: ERROR - Request timed out")
        print("-"*40)
        continue
    except httpx.HTTPStatusError as e:
        print(f"Test Case {idx}: ERROR - HTTP {e.response.status_code}")
        print("-"*40)
        continue
    except Exception as e:
        print(f"Test Case {idx}: ERROR - {e}")
        print("-"*40)
        continue
    
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

print(f"\nCompleted {len(test_cases)} test cases.")
