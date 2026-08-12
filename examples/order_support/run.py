"""End-to-end walkthrough: build a capability registry from real app
code, show what an agent sees before writing any code, then run one
agent-authored script that resolves a multi-step support task in a
single sandboxed round trip.

Run with:  uv run python3 -m examples.order_support.run

This mirrors what smile/server/execute_script.py does inside the MCP
server, minus MCP itself -- useful both as a "how do I use this as a
library" reference and as a fast way to sanity-check a registry without
spinning up the server or an LLM.
"""

from __future__ import annotations

from smile.sandbox import run_script

from examples.order_support.app import build_registry

# The task an agent was asked to do: "Refund every pending order over
# $1000 for cust_1, email the customer, and log what you did." Without
# SMiLE this is 1 tool call to list orders + N calls to refund + N calls
# to email + N calls to log -- each round trip paid in full context. With
# SMiLE it's one script; only the final summary crosses back out.
AGENT_SCRIPT = """
customer = get_customer("cust_1")
customer_orders = list_orders_for_customer(customer["id"])

refunded = []
for order in customer_orders:
    if order["status"] == "paid" and order["amount_cents"] > 100000:
        payments.refund(order["id"], order["amount_cents"])
        send_refund_email(customer["email"], order["id"], order["amount_cents"])
        log_support_action(f"Refunded {order['id']} for {customer['name']}")
        refunded.append(order["id"])

__result__ = {
    "customer": customer["name"],
    "refunded_order_ids": refunded,
    "total_refunded_cents": payments.get_refund_total_cents(),
}
"""


def main() -> None:
    registry = build_registry(payment_api_key="sk_test_51ExampleKey0000")

    print("=" * 72)
    print("CAPABILITY CATALOG -- what the agent sees before writing any code")
    print("=" * 72)
    print(registry.stub_file())

    print("=" * 72)
    print("AGENT SCRIPT -- one round trip, no matter how many orders match")
    print("=" * 72)
    print(AGENT_SCRIPT.strip())
    print()

    result = run_script(AGENT_SCRIPT, registry.namespace())

    print("=" * 72)
    print("RESULT")
    print("=" * 72)
    if result.error:
        print("Script raised an error:")
        print(result.error)
        raise SystemExit(1)

    print("Returned value (the only thing that crosses back out):")
    print(result.return_value)

    assert result.return_value == {
        "customer": "Ada Lovelace",
        "refunded_order_ids": ["ord_101"],
        "total_refunded_cents": 420000,
    }
    print("\nOK: matches expected output.")


if __name__ == "__main__":
    main()
