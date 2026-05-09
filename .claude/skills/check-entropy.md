---
name: check-entropy
description: Check for low/high entropy features (information content)
triggers:
  - entropy
  - information
  - information content
  - low information
  - constant features
---

# Check Entropy

Analyzes features for unusual entropy levels. Low entropy indicates near-constant features (low information), high entropy may indicate noise.

## When to Use
- User asks about entropy or information content
- User wants to find constant or near-constant features
- User mentions "low information features"

## Execution

```python
import pandas as pd
import datavint as vint

if 'df' not in locals():
    print("❌ No dataset loaded.")
    exit()

print("Running entropy analysis...\n")
stats, issues = vint.profile(df)

# Extract entropy issues
entropy_issues = [issue for issue in issues if 'entropy' in issue.type.value]

print("="*60)
print("ENTROPY ANALYSIS")
print("="*60)

# Get entropy for all features
entropy_data = []
for feat_name, feat_stats in stats.features.items():
    if feat_stats.entropy is not None:
        entropy_data.append({
            'feature': feat_name,
            'entropy': feat_stats.entropy,
            'type': feat_stats.type,
        })

entropy_data.sort(key=lambda x: x['entropy'])

print(f"\n📊 Entropy by Feature ({len(entropy_data)} features):\n")
for data in entropy_data:
    ent = data['entropy']

    if ent < 0.1:
        icon = "🔴"
        category = "VERY LOW"
    elif ent < 0.5:
        icon = "🟡"
        category = "LOW"
    elif ent > 4.0:
        icon = "⚠️"
        category = "HIGH"
    else:
        icon = "✅"
        category = "NORMAL"

    bar = "█" * min(int(ent * 10), 50)

    print(f"{icon} {data['feature']:<30} {ent:>6.3f} nats {bar}")
    print(f"   [{category:9}] ({data['type']})\n")

if entropy_issues:
    print(f"⚠️  {len(entropy_issues)} Entropy Issue(s) Detected:\n")
    for issue in entropy_issues:
        severity_icon = "🔴" if issue.severity.value == "high" else "🟡"
        print(f"{severity_icon} [{issue.severity.value.upper()}] {issue.feature}")
        print(f"   {issue.description}")
        print()
else:
    print("✅ No entropy issues detected")

print("\n" + "="*60)
print("RECOMMENDATIONS")
print("="*60)

low_entropy = [d for d in entropy_data if d['entropy'] < 0.1]
if low_entropy:
    print("\nLow entropy features (< 0.1 nats):")
    for d in low_entropy:
        print(f"  🔴 {d['feature']}")
        print(f"     → Consider dropping (near-constant, low information)")

high_entropy = [d for d in entropy_data if d['entropy'] > 4.0]
if high_entropy:
    print("\nHigh entropy features (> 4.0 nats):")
    for d in high_entropy:
        print(f"  ⚠️  {d['feature']}")
        print(f"     → Check if this is noise or meaningful variation")

print("\n" + "="*60)
```
