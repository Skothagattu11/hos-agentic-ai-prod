"""Check latest behavior analysis"""
import requests
import json

# Query the behavior analysis endpoint
response = requests.post(
    "http://localhost:8002/api/user/35pDPUIfAoRl2Y700bFkxPKYjjf2/behavior/analyze",
    json={"archetype": "Systematic Improver", "force_refresh": True},
    headers={"X-API-Key": "hosa_flutter_app_2024"},
    timeout=120
)

if response.status_code == 200:
    result = response.json()
    behavior = result.get('behavior_analysis', {})

    print("="*80)
    print("LATEST BEHAVIOR ANALYSIS RESULT")
    print("="*80)
    print(f"\nStatus: {result.get('status')}")
    print(f"Analysis Type: {result.get('analysis_type')}")
    print(f"\nData Insights:")
    print(behavior.get('data_insights', 'No data insights')[:500])
    print(f"\n\nBehavioral Signature:")
    sig = behavior.get('behavioral_signature', {})
    print(f"  - Signature: {sig.get('signature', 'N/A')[:200]}")
    print(f"  - Confidence: {sig.get('confidence', 0)}")
    print(f"\nSophistication:")
    soph = behavior.get('sophistication_assessment', {})
    print(f"  - Category: {soph.get('category', 'N/A')}")
    print(f"  - Score: {soph.get('score', 0)}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
