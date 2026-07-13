import sys

from tests.test_pipeline import (
    test_langgraph_reasoning_agent,
    test_specialized_parsers_fallback,
    test_vector_store_indexing,
)


def main():
    print("=" * 60)
    print(" 🧪 RUNNING AUTONOMOUS REASONING AGENT UNIT TESTS")
    print("=" * 60)
    
    tests = [
        ("Specialized Multi-Modal Parsers", test_specialized_parsers_fallback),
        ("Vector Store & Embedding Memory", test_vector_store_indexing),
        ("LangGraph Cyclical Reasoning Pipeline", test_langgraph_reasoning_agent),
    ]
    
    passed = 0
    for name, func in tests:
        try:
            print(f"[*] Executing Test: {name} ... ", end="")
            func()
            print("PASSED ✅")
            passed += 1
        except Exception as e:
            print(f"FAILED ❌ ({e})")
            
    print("-" * 60)
    print(f"Test Summary: {passed}/{len(tests)} Passed.")
    print("=" * 60)
    if passed != len(tests):
        sys.exit(1)

if __name__ == "__main__":
    main()
