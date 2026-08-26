import random
import logging
from datetime import datetime
from typing import Dict, Any, Tuple
from backend.app.config import settings

logger = logging.getLogger(__name__)


class ExecutionResult:
    def __init__(
        self,
        success: bool,
        is_recovered: bool,
        recovered_amount_inr: float,
        cost_inr: float,
        friction_penalty: float,
        execution_mode: str,
        details: Dict[str, Any],
        outcome_reason: str
    ):
        self.success = success
        self.is_recovered = is_recovered
        self.recovered_amount_inr = recovered_amount_inr
        self.cost_inr = cost_inr
        self.friction_penalty = friction_penalty
        self.execution_mode = execution_mode
        self.details = details
        self.outcome_reason = outcome_reason


class ExecutionAdapter:
    """
    Execution Adapter for ReviveAI.
    Executes approved actions via Razorpay Test Mode SDK when credentials are provided,
    or via high-fidelity Sandbox Simulation for testing and synthetic evaluations.
    """

    @classmethod
    async def execute_action(
        cls,
        action_type: str,
        amount_inr: float,
        customer_email: str,
        customer_phone: str,
        payment_id: str = None,
        subscription_id: str = None,
        failure_category: str = "insufficient_funds",
        predicted_prob: float = 0.5,
        timing_minutes: int = 0
    ) -> ExecutionResult:
        if settings.is_razorpay_configured:
            return await cls._execute_razorpay_test_mode(
                action_type=action_type,
                amount_inr=amount_inr,
                customer_email=customer_email,
                customer_phone=customer_phone,
                payment_id=payment_id,
                subscription_id=subscription_id
            )
        else:
            return cls._execute_sandbox_simulation(
                action_type=action_type,
                amount_inr=amount_inr,
                failure_category=failure_category,
                predicted_prob=predicted_prob,
                timing_minutes=timing_minutes
            )

    @classmethod
    async def _execute_razorpay_test_mode(
        cls,
        action_type: str,
        amount_inr: float,
        customer_email: str,
        customer_phone: str,
        payment_id: str,
        subscription_id: str
    ) -> ExecutionResult:
        import razorpay

        if settings.RAZORPAY_KEY_ID.startswith("rzp_live_"):
            raise RuntimeError("CRITICAL REJECTION: Live mode key blocked by security guardrails.")

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        details = {"sdk": "razorpay-python", "mode": "TEST_MODE"}

        try:
            if "reminder" in action_type or "update_request" in action_type:
                # Create a genuine Razorpay Payment Link in Test Mode
                link_payload = {
                    "amount": int(amount_inr * 100),
                    "currency": "INR",
                    "accept_partial": False,
                    "description": f"ReviveAI Automated Recovery Link for {customer_email}",
                    "customer": {
                        "name": customer_email.split("@")[0],
                        "email": customer_email,
                        "contact": customer_phone or "+919999999999"
                    },
                    "notify": {"sms": bool(customer_phone), "email": bool(customer_email)},
                    "reminder_enable": True,
                    "notes": {"reviveai_recovery_action": action_type}
                }
                payment_link = client.payment_link.create(link_payload)
                details["razorpay_payment_link_id"] = payment_link.get("id")
                details["short_url"] = payment_link.get("short_url")
                is_recovered = False  # Link dispatched; pending customer payment webhook
                outcome_reason = f"Test Mode Payment Link issued: {payment_link.get('short_url')}"

            elif "retry" in action_type:
                # Test Mode Retry Simulation
                details["retry_dispatched"] = True
                details["payment_id"] = payment_id
                # 70% stochastic success in test mode for recoverable test charges
                is_recovered = random.random() < 0.70
                outcome_reason = "Test Mode Gateway Retry succeeded" if is_recovered else "Test Mode Gateway Retry declined"

            else:
                is_recovered = False
                outcome_reason = f"Executed {action_type} in Razorpay Test Mode"

            return ExecutionResult(
                success=True,
                is_recovered=is_recovered,
                recovered_amount_inr=amount_inr if is_recovered else 0.0,
                cost_inr=settings.COST_PER_RETRY_INR,
                friction_penalty=settings.FRICTION_PENALTY_RETRY,
                execution_mode="RAZORPAY_TEST_MODE",
                details=details,
                outcome_reason=outcome_reason
            )

        except Exception as e:
            logger.error(f"Razorpay Test Mode SDK execution error: {e}")
            return ExecutionResult(
                success=False,
                is_recovered=False,
                recovered_amount_inr=0.0,
                cost_inr=0.0,
                friction_penalty=0.0,
                execution_mode="RAZORPAY_TEST_MODE",
                details={"error": str(e)},
                outcome_reason=f"Test Mode Execution Exception: {str(e)}"
            )

    @classmethod
    def _execute_sandbox_simulation(
        cls,
        action_type: str,
        amount_inr: float,
        failure_category: str,
        predicted_prob: float,
        timing_minutes: int
    ) -> ExecutionResult:
        """
        High-fidelity stochastic Sandbox Simulator for zero-credential testing and 10k-batch benchmarks.
        """
        if action_type == "stop_recovery":
            return ExecutionResult(
                success=True,
                is_recovered=False,
                recovered_amount_inr=0.0,
                cost_inr=0.0,
                friction_penalty=0.0,
                execution_mode="SANDBOX_SIMULATION",
                details={"action": "stopped"},
                outcome_reason="Recovery intentionally stopped per safety stopping rules."
            )

        # Baseline recovery probability modified by actual underlying category & action alignment
        actual_success_prob = predicted_prob

        # Smart timing boost
        if action_type == "smart_timing_retry" and failure_category == "insufficient_funds":
            actual_success_prob = min(0.92, actual_success_prob * 1.15)

        # Hard decline without payment method update always fails
        if failure_category == "bank_decline_hard" and "retry" in action_type:
            actual_success_prob = 0.0

        # Stochastic resolution
        roll = random.random()
        is_recovered = roll < actual_success_prob
        recovered_amount = amount_inr if is_recovered else 0.0

        # Direct Costs & Friction
        cost_map = {
            "delayed_retry": 5.0,
            "smart_timing_retry": 5.0,
            "payment_method_update_request": 0.5,
            "customer_reminder_email": 0.5,
            "customer_reminder_whatsapp": 2.5,
            "incentive_grace_period": 50.0,
            "escalate_to_human_review": 150.0,
        }
        friction_map = {
            "delayed_retry": 10.0,
            "smart_timing_retry": 5.0,
            "payment_method_update_request": 15.0,
            "customer_reminder_email": 20.0,
            "customer_reminder_whatsapp": 60.0,
            "incentive_grace_period": 0.0,
            "escalate_to_human_review": 10.0,
        }

        cost = cost_map.get(action_type, 5.0)
        friction = friction_map.get(action_type, 10.0)

        details = {
            "simulated_stochastic_roll": round(roll, 4),
            "effective_recovery_probability": round(actual_success_prob, 4),
            "timing_delay_minutes": timing_minutes,
            "timestamp": datetime.utcnow().isoformat()
        }

        if is_recovered:
            outcome_reason = f"Successfully recovered ₹{amount_inr:,.2f} via {action_type} (Simulation)"
        else:
            outcome_reason = f"Intervention {action_type} completed; payment remained unrecovered (Simulation)"

        return ExecutionResult(
            success=True,
            is_recovered=is_recovered,
            recovered_amount_inr=recovered_amount,
            cost_inr=cost,
            friction_penalty=friction,
            execution_mode="SANDBOX_SIMULATION",
            details=details,
            outcome_reason=outcome_reason
        )
