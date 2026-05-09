"""
Test script for hybrid routing layer

Demonstrates how different queries route to either:
1. Skills (fast, free, reliable)
2. LLM generation (flexible, slower, costs API calls)
"""

import pandas as pd
import numpy as np
import sys
import os

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from server.api.services.skill_router import get_router
from server.api.services.skill_executor import get_executor


def create_test_dataset():
    """Create a test dataset with various data quality issues"""
    np.random.seed(42)
    n = 1000

    data = {
        'user_id': range(1, n + 1),
        'age': [np.random.randint(18, 80) if i % 3 != 0 else None for i in range(n)],  # 33% missing
        'email': ['user{}@example.com'.format(i) if i % 2 == 0 else None for i in range(n)],  # 50% missing
        'signup_date': pd.date_range('2024-01-01', periods=n).strftime('%Y-%m-%d').tolist(),
        'is_active': np.random.choice([True, False], n, p=[0.8, 0.2]),  # 80/20 imbalance
        'country': np.random.choice(['US', 'UK', 'CA'], n, p=[0.7, 0.2, 0.1]),
        'high_card_id': [f'ID_{i}_{np.random.randint(1, 100000)}' for i in range(n)]  # High cardinality
    }

    return pd.DataFrame(data)


def test_routing():
    """Test routing layer with various queries"""

    # Create test dataset
    df = create_test_dataset()
    print(f"Test dataset: {df.shape[0]} rows × {df.shape[1]} columns\n")

    # Test queries
    test_queries = [
        # Should route to skills
        ("/check-completeness", "Command match"),
        ("check missing values across all columns", "Keyword match: missing"),
        ("show me completeness for the dataset", "Pattern match: completeness"),
        ("check imbalance in the dataset", "Keyword match: imbalance"),
        ("find class imbalance", "Pattern match: class imbalance"),
        ("check cardinality of all features", "Keyword match: cardinality"),

        # Should route to LLM
        ("compare train/test missing rates and visualize", "Novel request - no skill match"),
        ("cluster features by correlation", "Complex analysis - no skill match"),
        ("generate a summary report with visualizations", "Multi-step - no skill match"),
        ("predict which features are most important", "ML task - no skill match")
    ]

    router = get_router()
    executor = get_executor()

    print("=" * 100)
    print("ROUTING TESTS")
    print("=" * 100)

    for query, expected in test_queries:
        print(f"\n📝 Query: \"{query}\"")
        print(f"   Expected: {expected}")

        routing_decision = router.route_query(query)

        if routing_decision['use_skill']:
            skill_name = routing_decision['skill_name']
            print(f"   ✅ Routed to SKILL: {skill_name}")
            print(f"      Confidence: {routing_decision['confidence']}")
            print(f"      Trigger: {routing_decision['trigger_type']}")
            print(f"      Reason: {routing_decision['reason']}")

            # Execute skill if it's a completeness or imbalance check
            if skill_name in ['check-completeness', 'check-imbalance', 'check-cardinality']:
                print(f"\n      Executing {skill_name}...")
                result = executor.execute(skill_name, df)

                if result['success']:
                    print(f"      ✅ Execution successful")
                    # Show first 200 chars of output
                    output_preview = result['output'][:200] + "..." if len(result['output']) > 200 else result['output']
                    print(f"      Output preview:\n{output_preview}")
                else:
                    print(f"      ❌ Execution failed: {result['error']}")
        else:
            print(f"   🔄 Routed to LLM")
            print(f"      Reason: {routing_decision['reason']}")

    # Print final metrics
    print("\n" + "=" * 100)
    print("ROUTING METRICS")
    print("=" * 100)

    metrics = router.get_metrics()
    print(f"\nTotal queries: {metrics['total_queries']}")
    print(f"Skill routed: {metrics['skill_routed']} ({metrics['skill_percentage']:.1f}%)")
    print(f"LLM routed: {metrics['llm_routed']} ({metrics['llm_percentage']:.1f}%)")
    print(f"\nSkill breakdown:")
    for skill_name, count in metrics['skill_breakdown'].items():
        if count > 0:
            print(f"  • {skill_name}: {count} queries")

    # Cost/latency savings
    skill_cost = 0.0
    llm_cost = 0.03
    skill_latency = 100  # ms
    llm_latency = 3000  # ms

    actual_cost = (metrics['skill_routed'] * skill_cost) + (metrics['llm_routed'] * llm_cost)
    if_all_llm_cost = metrics['total_queries'] * llm_cost
    cost_saved = if_all_llm_cost - actual_cost

    actual_latency = (metrics['skill_routed'] * skill_latency) + (metrics['llm_routed'] * llm_latency)
    if_all_llm_latency = metrics['total_queries'] * llm_latency
    latency_saved = if_all_llm_latency - actual_latency

    print(f"\nCost savings:")
    print(f"  Actual cost: ${actual_cost:.2f}")
    print(f"  If all LLM: ${if_all_llm_cost:.2f}")
    print(f"  Saved: ${cost_saved:.2f} ({(cost_saved/if_all_llm_cost*100):.1f}% reduction)")

    print(f"\nLatency savings:")
    print(f"  Actual latency: {actual_latency}ms")
    print(f"  If all LLM: {if_all_llm_latency}ms")
    print(f"  Saved: {latency_saved}ms ({(latency_saved/if_all_llm_latency*100):.1f}% reduction)")
    print(f"  Speedup: {if_all_llm_latency/actual_latency:.1f}x faster")


if __name__ == "__main__":
    print("\n🚀 Testing Hybrid Routing Layer\n")
    test_routing()
    print("\n✅ All tests completed\n")
