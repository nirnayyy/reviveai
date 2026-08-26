import random
from typing import List, Dict, Any


class SyntheticDatasetGenerator:
    """
    Generates realistic, representative payment failure events based on real-world Indian fintech & Razorpay subscription patterns.
    Distribution:
    - 38% Insufficient balance (sensitive to morning / salary cycles)
    - 22% UPI AutoPay mandate issues / limits
    - 16% Expired payment tokens / replaced cards
    - 12% Transient gateway / banking switch downtime
    - 7%  Hard declines (lost/stolen card, closed account)
    - 5%  3DS Auth timeouts / drop-offs
    """

    SCENARIOS = [
        {
            "weight": 0.38,
            "category": "insufficient_funds",
            "error_code": "BAD_REQUEST_PAYMENT_DECLINED_BY_BANK",
            "error_description": "Payment declined due to insufficient balance in customer account",
            "payment_methods": ["card", "upi", "netbanking"],
            "amount_range": (499.0, 9999.0),
            "recoverable": True,
            "optimal_action": "smart_timing_retry"
        },
        {
            "weight": 0.22,
            "category": "upi_mandate_failed",
            "error_code": "BAD_REQUEST_UPI_MANDATE_REVOKED",
            "error_description": "UPI AutoPay recurring charge failed or mandate limit reached",
            "payment_methods": ["upi"],
            "amount_range": (199.0, 4999.0),
            "recoverable": True,
            "optimal_action": "customer_reminder_whatsapp"
        },
        {
            "weight": 0.16,
            "category": "expired_payment_method",
            "error_code": "BAD_REQUEST_PAYMENT_CARD_EXPIRED",
            "error_description": "The card or mandate token has expired",
            "payment_methods": ["card"],
            "amount_range": (999.0, 14999.0),
            "recoverable": True,
            "optimal_action": "payment_method_update_request"
        },
        {
            "weight": 0.12,
            "category": "bank_decline_temporary",
            "error_code": "GATEWAY_ERROR",
            "error_description": "Issuing bank network timed out during transaction capture",
            "payment_methods": ["netbanking", "card"],
            "amount_range": (1499.0, 29999.0),
            "recoverable": True,
            "optimal_action": "delayed_retry"
        },
        {
            "weight": 0.07,
            "category": "bank_decline_hard",
            "error_code": "BAD_REQUEST_PAYMENT_CARD_STOLEN",
            "error_description": "Card reported lost or stolen by cardholder",
            "payment_methods": ["card"],
            "amount_range": (999.0, 19999.0),
            "recoverable": False,  # Impossible to recover on same instrument!
            "optimal_action": "payment_method_update_request"
        },
        {
            "weight": 0.05,
            "category": "auth_abandonment",
            "error_code": "BAD_REQUEST_PAYMENT_OTP_VALIDATION_FAILED",
            "error_description": "Customer dropped off during 3DS OTP validation",
            "payment_methods": ["card", "netbanking"],
            "amount_range": (499.0, 8999.0),
            "recoverable": True,
            "optimal_action": "customer_reminder_email"
        }
    ]

    @classmethod
    def generate_dataset(cls, count: int = 10000, seed: int = 42) -> List[Dict[str, Any]]:
        random.seed(seed)
        events = []

        weights = [s["weight"] for s in cls.SCENARIOS]

        for i in range(count):
            scenario = random.choices(cls.SCENARIOS, weights=weights, k=1)[0]
            amt = round(random.uniform(*scenario["amount_range"]), 2)
            # Occasional high-value enterprise transaction (> Rs 50k)
            if random.random() < 0.03:
                amt = round(random.uniform(55000.0, 125000.0), 2)

            method = random.choice(scenario["payment_methods"])
            cust_id = f"cust_synth_{i:06d}"
            ltv = round(amt * random.uniform(2.0, 15.0), 2)
            is_sub = random.random() < 0.65
            risk_age = round(random.uniform(0.1, 72.0), 1)
            retry_count = 0 if random.random() > 0.35 else random.randint(1, 3)

            events.append({
                "case_id": f"SYNTH-{i:06d}",
                "customer_id": cust_id,
                "customer_email": f"user_{i:06d}@company.in",
                "customer_phone": f"+9198{random.randint(10000000, 99999999)}",
                "customer_ltv_inr": ltv,
                "amount_inr": amt,
                "payment_method": method,
                "error_code": scenario["error_code"],
                "error_description": scenario["error_description"],
                "failure_category": scenario["category"],
                "is_recoverable_ground_truth": scenario["recoverable"],
                "optimal_action_ground_truth": scenario["optimal_action"],
                "is_subscription": is_sub,
                "risk_age_hours": risk_age,
                "previous_retry_count": retry_count
            })

        return events
