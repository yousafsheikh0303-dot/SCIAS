from orchestrator import run_query

test_queries = [
    "What's the best way to produce cotton?",
    "How should wheat be irrigated during growth stages?",
    "What is the recommended sowing time for rice in Punjab?",
    "How do I manage pests on tomato crops?",
    "Will it rain tomorrow?",
    "How much water does wheat need right now?",
    "My tomato leaves have brown spots",
    "What's the current price of wheat in the mandi?",
    "What yield can I expect from my cotton field?",
    "second largest export of pakistan crop?",
    "What causal organism is responsible for Yellow (Stripe) Rust in wheat, and what environmental conditions favor its spread?",
    "Why is Karnal Bunt in wheat considered more of a marketability problem than a yield problem?",
]

for q in test_queries:
    print(f"\nQuery: {q}")
    result = run_query(q)
    print(f"Routed to: {result['agent_used']}")
    print(f"Answer: {result['answer'][:300]}")

# --- Quick sanity check for the disease-routing fix ---
print("\n--- Disease routing check ---")
result = run_query("my tomato leaves have brown spots")
print(f"Routed to: {result['agent_used']}")   # expect: disease
print(f"Answer: {result['answer'][:300]}")