"""
E2E test for /playground page

Tests the experiment lineage visualization dashboard:
- Frontend loads at /playground/
- API endpoint returns experiment data
- Page can be accessed without errors
"""

import requests
import time
import sys


def test_backend_api_running():
    """Test that backend API is responding."""
    try:
        # Test the root API endpoint or experiments list
        response = requests.get('http://localhost:8000/api/experiments', timeout=5)
        assert response.status_code == 200, f"Backend health check failed: {response.status_code}"
        print("✓ Backend API is running")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ Backend API not responding: {e}")
        return False


def test_frontend_running():
    """Test that frontend dev server is responding."""
    try:
        # Check if the playground page loads
        response = requests.get('http://localhost:5173/playground/', timeout=5)
        assert response.status_code == 200, f"Frontend not accessible: {response.status_code}"

        # Check that it's the Vite app (contains vite/modulepreload-polyfill or similar)
        content = response.text.lower()
        assert 'datavint' in content or 'vite' in content, "Frontend doesn't contain expected content"

        print("✓ Frontend is running at /playground/")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ Frontend not responding: {e}")
        return False


def test_experiment_lineage_api():
    """Test that the experiment lineage API endpoint works."""
    try:
        # Test the main lineage endpoint
        response = requests.get(
            'http://localhost:8000/api/experiments/test_exp/lineage',
            timeout=5
        )
        assert response.status_code == 200, f"API returned {response.status_code}"

        data = response.json()

        # Verify the response structure
        assert 'experimentId' in data, "Missing experimentId in response"
        assert 'dataCommits' in data, "Missing dataCommits in response"
        assert 'modelRuns' in data, "Missing modelRuns in response"
        assert 'connections' in data, "Missing connections in response"

        # Verify we have data
        assert len(data['dataCommits']) > 0, "No data commits returned"
        assert len(data['modelRuns']) > 0, "No model runs returned"

        # Verify the winner logic: lowest NE = best
        model_runs = data['modelRuns']
        best_run = next((r for r in model_runs if r.get('best')), None)
        if best_run:
            best_ne = best_run['metrics']['NE']['value']
            print(f"✓ Best model run has NE={best_ne}")

            # Verify it's the lowest NE
            all_ne_values = [r['metrics']['NE']['value'] for r in model_runs if 'NE' in r['metrics']]
            assert best_ne == min(all_ne_values), f"Best model doesn't have lowest NE: {best_ne} vs {min(all_ne_values)}"
            print(f"✓ Winner logic correct: lowest NE ({best_ne}) = best")

        print("✓ Experiment lineage API working correctly")
        return True

    except requests.exceptions.RequestException as e:
        print(f"✗ API not responding: {e}")
        return False
    except (AssertionError, KeyError, ValueError) as e:
        print(f"✗ API response validation failed: {e}")
        return False


def test_experiments_list_api():
    """Test that the experiments list endpoint works."""
    try:
        response = requests.get('http://localhost:8000/api/experiments', timeout=5)
        assert response.status_code == 200, f"Experiments list returned {response.status_code}"

        data = response.json()
        assert 'experiments' in data, "Missing experiments in response"

        print("✓ Experiments list API working")
        return True

    except requests.exceptions.RequestException as e:
        print(f"✗ Experiments list API not responding: {e}")
        return False


def main():
    """Run all e2e tests."""
    print("\n" + "="*60)
    print("E2E Tests: /playground Page")
    print("="*60 + "\n")

    all_passed = True

    # Test backend first
    if not test_backend_api_running():
        print("\n⚠️  Backend not running. Start with: cd server && uvicorn api.main:app --reload")
        all_passed = False

    # Test frontend
    if not test_frontend_running():
        print("\n⚠️  Frontend not running. Start with: cd client && npm run dev")
        all_passed = False

    # If both servers are up, test the APIs
    if all_passed:
        if not test_experiment_lineage_api():
            all_passed = False

        if not test_experiments_list_api():
            all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("✅ All e2e tests passed!")
        print("="*60 + "\n")
        return 0
    else:
        print("❌ Some e2e tests failed")
        print("="*60 + "\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
