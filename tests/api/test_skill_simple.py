"""Simple test to see full error traceback"""

import pandas as pd
import numpy as np
import traceback
import importlib
import sys
import os

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Force reload of modules to pick up code changes
if 'server.api.services.skill_executor' in sys.modules:
    del sys.modules['server.api.services.skill_executor']

from server.api.services.skill_executor import get_executor

# Create test data
np.random.seed(42)
n = 100

data = {
    'age': [np.random.randint(18, 80) if i % 3 != 0 else None for i in range(n)],
    'email': ['user{}@example.com'.format(i) if i % 2 == 0 else None for i in range(n)],
}

df = pd.DataFrame(data)

print(f"Test dataset: {df.shape}")
print(f"Columns: {df.columns.tolist()}\n")

executor = get_executor()

print("Executing check-completeness skill...")
try:
    result = executor.execute("check-completeness", df)

    if result['success']:
        print("✅ SUCCESS")
        print(result['output'])
    else:
        print("❌ FAILED")
        print(f"Error: {result['error']}")
except Exception as e:
    print("❌ EXCEPTION")
    print(f"Error: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
