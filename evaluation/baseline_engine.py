import random
from typing import Dict, Any, Tuple


class BaselineFixedRetryEngine:
    """
    Industry-standard baseline: Fixed blind retry schedule (naive 24h retries up to 3 times).
    Features:
    - Zero contextual diagnosis.
    - Blindly retries hard declines (wasting gateway cost and creating bank friction).
    - Cannot prompt for payment method updates when cards expire.
    - Zero friction awareness.
    """

    @classmethod
    def evaluate_case(cls, event: Dict[str, Any]) -> Tuple[bool, float, float, float, int]:
        """
        Returns:
        (is_recovered, recovered_amount, total_cost, friction_penalty, attempts_used)
        """
        category = event["failure_category"]
        amt = event["amount_inr"]
        prev_retries = event.get("previous_retry_count", 0)

        # Baseline allows up to 3 fixed retries
        max_retries = 3
        remaining_retries = max(0, max_retries - prev_retries)

        if remaining_retries == 0:
            return False, 0.0, 0.0, 0.0, 0

        # Success probabilities for fixed naive retry:
        # - Temporary gateway error: decent recovery (60%)
        # - Insufficient funds: mediocre recovery (35% because naive timing misses salary windows)
        # - Expired card: 0% recovery (retrying expired token always fails!)
        # - Hard decline (stolen/closed): 0% recovery (100% waste!)
        # - UPI Mandate failed: low recovery (18% without customer re-auth)
        # - Auth abandon: low recovery (15% without reminder link)

        prob_per_retry = {
            "bank_decline_temporary": 0.60,
            "insufficient_funds": 0.35,
            "expired_payment_method": 0.0,
            "bank_decline_hard": 0.0,
            "upi_mandate_failed": 0.18,
            "auth_abandonment": 0.15,
        }.get(category, 0.25)

        total_cost = 0.0
        total_friction = 0.0
        is_recovered = False
        attempts = 0

        for attempt in range(remaining_retries):
            attempts += 1
            total_cost += 5.0  # Rs 5 gateway cost per retry
            total_friction += 10.0  # Customer friction per blind retry attempt

            # For hard declines, issuing banks charge extra penalty / risk score degradation
            if category == "bank_decline_hard":
                total_friction += 25.0

            # Cumulative probability check
            if random.random() < prob_per_retry:
                is_recovered = True
                break

        recovered_amt = amt if is_recovered else 0.0
        return is_recovered, recovered_amt, total_cost, total_friction, attempts
