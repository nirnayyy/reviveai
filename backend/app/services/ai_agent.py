import json
import time
import hashlib
import logging
from typing import Dict, Any, List, Optional
from backend.app.config import settings
from backend.app.schemas.ai import AIDecisionSchema, CounterfactualEvaluation
from backend.app.services.value_model import RecoveryValueModel
from backend.app.services.diagnosis_engine import DiagnosisResult
from backend.app.services.risk_detector import RiskAssessment

logger = logging.getLogger(__name__)


class AIRecoveryAgent:
    """
    Tiered AI Revenue Recovery Agent.
    - Layer 1: Deterministic safety & equation guards.
    - Layer 2: Statistical prior scoring for 10k batch evaluation.
    - Layer 3: Gemini 3.7 Flash contextual reasoning for edge cases & high value.
    - Caching & Rate Budgeting to prevent wasteful API requests.
    """

    CANDIDATE_ACTIONS = [
        "delayed_retry",
        "smart_timing_retry",
        "payment_method_update_request",
        "customer_reminder_email",
        "customer_reminder_whatsapp",
        "incentive_grace_period",
        "escalate_to_human_review",
        "stop_recovery",
    ]

    # In-memory Decision Cache
    _decision_cache: Dict[str, AIDecisionSchema] = {}
    
    # Rate Limiting & Call Budget Trackers
    _call_count_run: int = 0
    _call_timestamps: List[float] = []

    @classmethod
    def _compute_cache_key(cls, case_context: Dict[str, Any], diagnosis: DiagnosisResult, risk: RiskAssessment) -> str:
        cache_data = {
            "category": diagnosis.category,
            "method": case_context.get("payment_method", "card").lower(),
            "retry_count": case_context.get("retry_count", 0),
            "tier": risk.customer_tier,
            "is_sub": case_context.get("is_subscription", False),
            "is_hard_decline": diagnosis.is_hard_decline,
            "amount_band": round(risk.amount_at_risk_inr / 1000.0) * 1000  # Band into 1k increments
        }
        raw = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    def _is_rate_limited(cls) -> bool:
        now = time.time()
        # Clean timestamps older than 60 seconds
        cls._call_timestamps = [t for t in cls._call_timestamps if now - t < 60.0]
        
        if len(cls._call_timestamps) >= settings.MAX_GEMINI_CALLS_PER_MINUTE:
            logger.warning("Gemini per-minute call budget reached. Using deterministic heuristic fallback.")
            return True
            
        if cls._call_count_run >= settings.MAX_GEMINI_CALLS_PER_RUN:
            logger.warning("Gemini per-run call budget reached. Using deterministic heuristic fallback.")
            return True
            
        return False

    @classmethod
    async def evaluate_case(
        cls,
        case_context: Dict[str, Any],
        diagnosis: DiagnosisResult,
        risk: RiskAssessment
    ) -> AIDecisionSchema:
        """
        Main entry point for AI evaluation.
        Evaluates cache -> budget -> Gemini 3.7 Flash -> Heuristic Fallback.
        """
        cache_key = cls._compute_cache_key(case_context, diagnosis, risk)

        # 1. Check Cache
        if settings.GEMINI_CACHE_ENABLED and cache_key in cls._decision_cache:
            logger.info(f"Retrieved AI recovery decision from cache for category: {diagnosis.category}")
            return cls._decision_cache[cache_key]

        # 2. Check if Gemini is enabled, configured, and within budget
        if settings.is_gemini_configured and not cls._is_rate_limited():
            try:
                decision = await cls._generate_with_gemini(case_context, diagnosis, risk)
                cls._call_count_run += 1
                cls._call_timestamps.append(time.time())
                
                if settings.GEMINI_CACHE_ENABLED:
                    cls._decision_cache[cache_key] = decision
                    
                return decision
            except Exception as e:
                logger.warning(f"Gemini generation failed or timed out: {e}. Engaging deterministic heuristic fallback.")
                fallback_decision = cls._generate_heuristic_decision(case_context, diagnosis, risk, is_fallback=True)
                return fallback_decision
        else:
            # Deterministic heuristic reasoner (Layer 2)
            return cls._generate_heuristic_decision(case_context, diagnosis, risk, is_fallback=not settings.is_gemini_configured)

    @classmethod
    async def _generate_with_gemini(
        cls,
        case_context: Dict[str, Any],
        diagnosis: DiagnosisResult,
        risk: RiskAssessment
    ) -> AIDecisionSchema:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        prompt = f"""
You are ReviveAI, an expert revenue recovery decision system for Razorpay merchants.
Analyze the following payment failure context and produce a structured, high-value recovery recommendation.

### Context:
- Amount at Risk: ₹{risk.amount_at_risk_inr:,.2f}
- Customer Lifetime Value (LTV): ₹{risk.customer_ltv_inr:,.2f}
- Customer Tier: {risk.customer_tier}
- Urgency Score: {risk.urgency_score}
- Payment Method: {case_context.get('payment_method', 'card')}
- Failure Category: {diagnosis.category}
- Consecutive Failures: {case_context.get('retry_count', 0)}
- Is Subscription: {case_context.get('is_subscription', False)}
- Known Facts: {json.dumps(diagnosis.known_facts)}
- Inferred Factors: {json.dumps(diagnosis.inferred_factors)}
- Unknown Factors: {json.dumps(diagnosis.unknown_factors)}

### Strict Rules:
1. You only PROPOSE a recommendation. Deterministic policy engine validates your output.
2. If this is a hard decline (stolen card/account closed), recommended action MUST be 'payment_method_update_request' or 'stop_recovery'. Never recommend a gateway retry for hard declines.
3. For high-value transactions (>₹50,000) or high ambiguity, set requires_human_review to true.
4. Calculate realistic probabilities and provide full counterfactual evaluations for all candidate actions.
5. Clearly distinguish verified known facts from statistical inferences and unknowns.
"""

        # Verify model name - default to gemini-3.7-flash or fallback
        model_name = settings.GEMINI_MODEL or "gemini-3.7-flash"

        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AIDecisionSchema,
                    temperature=0.2,
                ),
            )
            raw_text = response.text
            data = json.loads(raw_text)
            return AIDecisionSchema(**data)
        except Exception as e:
            # If 3.7 flash identifier fails, attempt 2.5 flash fallback
            if "not found" in str(e).lower() or "404" in str(e):
                logger.info(f"Model {model_name} not available; falling back to gemini-2.5-flash.")
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=AIDecisionSchema,
                        temperature=0.2,
                    ),
                )
                data = json.loads(response.text)
                return AIDecisionSchema(**data)
            raise e

    @classmethod
    def _generate_heuristic_decision(
        cls,
        case_context: Dict[str, Any],
        diagnosis: DiagnosisResult,
        risk: RiskAssessment,
        is_fallback: bool = False
    ) -> AIDecisionSchema:
        """
        Deterministic, mathematically grounded statistical reasoning engine.
        Produces full structured output, probabilities, and counterfactuals without LLM costs.
        """
        amount = risk.amount_at_risk_inr
        ltv = risk.customer_ltv_inr
        retries = case_context.get("retry_count", 0)
        category = diagnosis.category

        # Determine Primary Action & Timing & Probability based on diagnosis
        if category == "bank_decline_hard":
            recommended_action = "payment_method_update_request"
            timing_minutes = 0
            prob = 0.28
            conf = 0.95
            reasoning = (
                "Hard bank decline detected (card blocked/stolen/account closed). Immediate automated retry would 100% fail. "
                "The optimal safe path is requesting a new payment method while preserving merchant reputation."
            )
            requires_human = False

        elif category == "insufficient_funds":
            if retries == 0:
                recommended_action = "smart_timing_retry"
                timing_minutes = 1440  # 24 hours later
                prob = 0.72
                conf = 0.88
                reasoning = (
                    "Insufficient balance indicated. Direct immediate retry has high bounce rate. Scheduling smart delayed retry "
                    "for next morning window allows customer liquidity replenishment with zero customer communication friction."
                )
                requires_human = False
            elif retries == 1:
                recommended_action = "customer_reminder_email"
                timing_minutes = 0
                prob = 0.58
                conf = 0.82
                reasoning = (
                    "Second insufficient balance occurrence. A polite email reminder prompts customer to fund account or switch card "
                    "before subscription halts."
                )
                requires_human = False
            else:
                recommended_action = "customer_reminder_whatsapp"
                timing_minutes = 0
                prob = 0.42
                conf = 0.80
                reasoning = "Multiple retries exhausted. Direct WhatsApp alert required for immediate customer action."
                requires_human = False

        elif category == "expired_payment_method":
            recommended_action = "payment_method_update_request"
            timing_minutes = 0
            prob = 0.64
            conf = 0.92
            reasoning = (
                "Saved payment method or recurring token has expired. Issuing direct Razorpay token update link via email "
                "yields highest frictionless renewal probability."
            )
            requires_human = False

        elif category == "bank_decline_temporary":
            recommended_action = "delayed_retry"
            timing_minutes = 180  # 3 hours
            prob = 0.84
            conf = 0.90
            reasoning = "Transient gateway or banking switch timeout. Retrying in 3 hours after banking switch stabilizes."
            requires_human = False

        elif category == "auth_abandonment":
            recommended_action = "customer_reminder_email"
            timing_minutes = 30  # 30 minutes
            prob = 0.62
            conf = 0.85
            reasoning = "Customer dropped out during 3DS OTP verification. Sending an instant 1-click resumption link recovers high purchase intent."
            requires_human = False

        elif category == "upi_mandate_failed":
            recommended_action = "customer_reminder_whatsapp"
            timing_minutes = 0
            prob = 0.68
            conf = 0.86
            reasoning = "UPI AutoPay mandate failed. Sending interactive WhatsApp notification with UPI intent link enables instant 1-tap re-auth."
            requires_human = False

        elif category == "subscription_halted":
            recommended_action = "customer_reminder_email"
            timing_minutes = 0
            prob = 0.51
            conf = 0.84
            reasoning = "Subscription entered halted state. Automated retries halted by gateway. Immediate payment link required to reactivate subscription."
            requires_human = False

        else:  # unknown_ambiguous
            if retries == 0:
                recommended_action = "delayed_retry"
                timing_minutes = 720  # 12 hours
                prob = 0.55
                conf = 0.70
                reasoning = "Unclassified decline code. Testing a single delayed retry before escalating to customer contact."
                requires_human = False
            else:
                recommended_action = "customer_reminder_email"
                timing_minutes = 0
                prob = 0.45
                conf = 0.68
                reasoning = "Subsequent decline on ambiguous code. Prompting customer for alternate payment method."
                requires_human = False

        # High-value transaction flag for human sign-off
        if amount > settings.AUTONOMOUS_AMOUNT_LIMIT_INR:
            requires_human = True
            reasoning += f" [NOTICE: High-value case exceeding ₹{settings.AUTONOMOUS_AMOUNT_LIMIT_INR:,.0f} flagged for human review approval]."

        # Generate Counterfactual Evaluations
        counterfactuals = cls._generate_counterfactuals(
            amount=amount,
            ltv=ltv,
            category=category,
            retries=retries,
            recommended_action=recommended_action,
            recommended_prob=prob
        )

        return AIDecisionSchema(
            diagnosis_category=category,
            diagnosis_reasoning=f"Identified {category} from gateway indicators: {', '.join(diagnosis.known_facts[:2])}",
            known_facts=diagnosis.known_facts,
            inferred_factors=diagnosis.inferred_factors,
            unknown_factors=diagnosis.unknown_factors,
            recommended_action=recommended_action,
            timing_schedule_minutes=timing_minutes,
            expected_recovery_probability=prob,
            confidence_score=conf,
            reasoning_summary=reasoning,
            counterfactual_evaluations=counterfactuals,
            requires_human_review=requires_human
        )

    @classmethod
    def _generate_counterfactuals(
        cls,
        amount: float,
        ltv: float,
        category: str,
        retries: int,
        recommended_action: str,
        recommended_prob: float
    ) -> List[CounterfactualEvaluation]:
        """
        Evaluates EV for all candidate actions to transparently demonstrate counterfactual value.
        """
        results: List[CounterfactualEvaluation] = []

        base_probs: Dict[str, float] = {
            "delayed_retry": 0.45 if category != "bank_decline_hard" else 0.02,
            "smart_timing_retry": 0.68 if category == "insufficient_funds" else (0.50 if category != "bank_decline_hard" else 0.02),
            "payment_method_update_request": 0.60 if category in ("expired_payment_method", "bank_decline_hard") else 0.35,
            "customer_reminder_email": 0.52 if category in ("auth_abandonment", "subscription_halted") else 0.40,
            "customer_reminder_whatsapp": 0.65 if category in ("upi_mandate_failed", "insufficient_funds") else 0.48,
            "incentive_grace_period": 0.70 if ltv > 20000 else 0.50,
            "escalate_to_human_review": 0.85 if amount > 50000 else 0.60,
            "stop_recovery": 0.0,
        }

        base_probs[recommended_action] = recommended_prob

        for action in cls.CANDIDATE_ACTIONS:
            p = base_probs.get(action, 0.30)
            gross, cost, friction, net_ev = RecoveryValueModel.calculate_expected_value(
                action_name=action,
                amount_at_risk_inr=amount,
                recovery_probability=p,
                customer_ltv_inr=ltv
            )

            if action == recommended_action:
                tradeoff = "Selected as optimal trade-off between recovery lift, operational cost, and customer friction."
            elif action == "stop_recovery":
                tradeoff = "Zero cost and zero friction, but forfeits all recoverable revenue."
            elif action == "escalate_to_human_review":
                tradeoff = f"High probability of recovery but incurs significant manual operator cost (₹{cost:,.2f})."
            elif action == "customer_reminder_whatsapp":
                tradeoff = f"High open rates but creates higher customer fatigue/friction penalty (₹{friction:,.2f})."
            elif "retry" in action and category == "bank_decline_hard":
                tradeoff = "Virtually 0% recovery chance due to permanent bank block; would waste cost and damage merchant score."
            else:
                tradeoff = f"Yields net EV of ₹{net_ev:,.2f} vs optimal ₹{gross - cost - friction:,.2f}."

            results.append(CounterfactualEvaluation(
                action_name=action,
                recovery_probability=round(p, 3),
                expected_recovered_inr=round(gross, 2),
                intervention_cost_inr=round(cost, 2),
                friction_penalty_inr=round(friction, 2),
                expected_net_value_inr=round(net_ev, 2),
                tradeoff_summary=tradeoff
            ))

        results.sort(key=lambda x: x.expected_net_value_inr, reverse=True)
        return results
