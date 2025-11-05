"""
Cost Calculator Service
Calculates AI usage costs based on token counts and current model pricing.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from decimal import Decimal
from app.utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class CostCalculationError(Exception):
    """Custom exception for cost calculation errors"""
    pass


class ModelPricing:
    """Model pricing information"""
    
    def __init__(
        self,
        model_name: str,
        provider: str,
        input_cost_per_million: Decimal,
        output_cost_per_million: Decimal
    ):
        self.model_name = model_name
        self.provider = provider
        self.input_cost_per_million = input_cost_per_million
        self.output_cost_per_million = output_cost_per_million
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> Decimal:
        """Calculate cost for given token counts"""
        input_cost = Decimal(input_tokens) * self.input_cost_per_million / Decimal(1_000_000)
        output_cost = Decimal(output_tokens) * self.output_cost_per_million / Decimal(1_000_000)
        return input_cost + output_cost


class PricingCache:
    """In-memory cache for model pricing to reduce database queries"""
    
    def __init__(self):
        self._cache: Dict[str, ModelPricing] = {}
        self._last_refresh: Optional[datetime] = None
    
    def get(self, model_name: str) -> Optional[ModelPricing]:
        """Get pricing from cache"""
        return self._cache.get(model_name)
    
    def set(self, model_name: str, pricing: ModelPricing):
        """Set pricing in cache"""
        self._cache[model_name] = pricing
    
    def clear(self):
        """Clear cache"""
        self._cache.clear()
        self._last_refresh = None
    
    def refresh_time(self):
        """Update last refresh time"""
        self._last_refresh = datetime.utcnow()


# Global pricing cache
_pricing_cache = PricingCache()


def get_model_pricing(model_name: str, use_cache: bool = True) -> Optional[ModelPricing]:
    """
    Fetch model pricing from database or cache.
    
    Args:
        model_name: Name of the AI model
        use_cache: Whether to use cached pricing
    
    Returns:
        ModelPricing object or None if not found
    """
    # Check cache first
    if use_cache:
        cached_pricing = _pricing_cache.get(model_name)
        if cached_pricing:
            logger.debug(f"[COST] Using cached pricing for {model_name}")
            return cached_pricing
    
    try:
        supabase = get_supabase_client()
        
        # Fetch from database
        response = supabase.table("ai_model_pricing")\
            .select("*")\
            .eq("model_name", model_name)\
            .eq("is_active", True)\
            .execute()
        
        if not response.data:
            logger.warning(f"[COST] No pricing found for model: {model_name}")
            return None
        
        data = response.data[0]
        pricing = ModelPricing(
            model_name=data["model_name"],
            provider=data["provider"],
            input_cost_per_million=Decimal(str(data["input_cost_per_million"])),
            output_cost_per_million=Decimal(str(data["output_cost_per_million"]))
        )
        
        # Cache the pricing
        _pricing_cache.set(model_name, pricing)
        
        logger.debug(f"[COST] Fetched pricing for {model_name}: ${pricing.input_cost_per_million}/M in, ${pricing.output_cost_per_million}/M out")
        
        return pricing
        
    except Exception as e:
        logger.error(f"[COST] Error fetching pricing for {model_name}: {str(e)}")
        return None


def calculate_cost(
    model_name: str,
    input_tokens: int,
    output_tokens: int
) -> Tuple[Decimal, Optional[str]]:
    """
    Calculate cost for a single AI call.
    
    Args:
        model_name: Name of the AI model
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
    
    Returns:
        Tuple of (cost in USD, error message if any)
    """
    try:
        pricing = get_model_pricing(model_name)
        
        if not pricing:
            error_msg = f"Pricing not found for model: {model_name}"
            logger.warning(f"[COST] {error_msg}")
            return Decimal(0), error_msg
        
        cost = pricing.calculate_cost(input_tokens, output_tokens)
        
        logger.debug(
            f"[COST] Calculated cost for {model_name}: "
            f"{input_tokens} in + {output_tokens} out = ${cost:.6f}"
        )
        
        return cost, None
        
    except Exception as e:
        error_msg = f"Error calculating cost: {str(e)}"
        logger.error(f"[COST] {error_msg}")
        return Decimal(0), error_msg


class CostTracker:
    """
    Tracks AI usage costs across a website generation session.
    Accumulates costs by service and provides breakdown.
    """
    
    def __init__(self, generation_type: str = "website", endpoint: str = None):
        """
        Initialize cost tracker.
        
        Args:
            generation_type: Type of generation ('website', 'edit', 'component')
            endpoint: API endpoint being called
        """
        self.generation_type = generation_type
        self.endpoint = endpoint
        
        # Service-level cost tracking
        self.service_costs: Dict[str, Decimal] = {
            "business_analysis": Decimal(0),
            "structure_generation": Decimal(0),
            "theme_generation": Decimal(0),
            "page_generation": Decimal(0),
            "validation": Decimal(0),
            "edit": Decimal(0)
        }
        
        # Detailed model usage tracking
        self.model_calls: List[Dict[str, Any]] = []
        
        # Aggregate tokens
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        
        # Performance tracking
        self.start_time = datetime.utcnow()
        self.retry_count = 0
        
        # Status
        self.status = "in_progress"
        self.error_message: Optional[str] = None
    
    def track_call(
        self,
        service_name: str,
        model_name: str,
        usage: Dict[str, int],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Decimal:
        """
        Track a single AI call.
        
        Args:
            service_name: Service making the call (e.g., 'business_analysis')
            model_name: AI model used
            usage: Dict with 'prompt_tokens', 'completion_tokens', 'total_tokens'
            metadata: Optional metadata (e.g., page name, component name)
        
        Returns:
            Cost in USD for this call
        """
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", input_tokens + output_tokens)
        
        # Calculate cost
        cost, error = calculate_cost(model_name, input_tokens, output_tokens)
        
        if error:
            logger.warning(f"[COST TRACKER] {error}")
        
        # Update service cost
        service_key = service_name.lower().replace(" ", "_")
        if service_key in self.service_costs:
            self.service_costs[service_key] += cost
        else:
            # For unknown services, add to validation/other
            self.service_costs["validation"] += cost
        
        # Update totals
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        
        # Record detailed call
        call_record = {
            "service": service_name,
            "model": model_name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "ai_total_tokens": total_tokens, # Calculated differently by the AI model provider - especially for Google Gemini
            "actual_total_tokens": input_tokens + output_tokens,
            "cost": float(cost)
        }
        
        if metadata:
            call_record["metadata"] = metadata
        
        self.model_calls.append(call_record)
        
        logger.info(
            f"[COST TRACKER] {service_name} | {model_name} | "
            f"{input_tokens} in + {output_tokens} out = ${cost:.6f}"
        )
        
        return cost
    
    def increment_retries(self):
        """Increment retry count"""
        self.retry_count += 1
    
    def mark_completed(self):
        """Mark tracking as completed"""
        self.status = "completed"
    
    def mark_failed(self, error_message: str):
        """Mark tracking as failed"""
        self.status = "failed"
        self.error_message = error_message
    
    def get_total_cost(self) -> Decimal:
        """Get total cost across all services"""
        return sum(self.service_costs.values())
    
    def get_breakdown(self) -> Dict[str, Any]:
        """
        Get cost breakdown.
        
        Returns:
            Dictionary with cost breakdown by service and totals
        """
        total_cost = self.get_total_cost()
        
        return {
            "total_cost_usd": float(total_cost),
            "breakdown": {
                "business_analysis": float(self.service_costs["business_analysis"]),
                "structure_generation": float(self.service_costs["structure_generation"]),
                "theme_generation": float(self.service_costs["theme_generation"]),
                "page_generation": float(self.service_costs["page_generation"]),
                "validation": float(self.service_costs["validation"]),
                "edit": float(self.service_costs["edit"])
            },
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "models_used": self.model_calls,
            "generation_time_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "retry_count": self.retry_count,
            "status": self.status
        }
    
    async def save_to_database(
        self,
        project_id: str,
        user_id: str,
        supabase_client=None
    ) -> Optional[str]:
        """
        Save cost tracking record to database.
        
        Args:
            project_id: Project ID
            user_id: User ID
            supabase_client: Optional Supabase client instance
        
        Returns:
            Tracking record ID or None if failed
        """
        if supabase_client is None:
            supabase_client = get_supabase_client()
        
        try:
            generation_time = (datetime.utcnow() - self.start_time).total_seconds()
            total_cost = self.get_total_cost()
            
            record_data = {
                "project_id": project_id,
                "user_id": user_id,
                "generation_type": self.generation_type,
                "endpoint": self.endpoint,
                "business_analysis_cost": float(self.service_costs["business_analysis"]),
                "structure_generation_cost": float(self.service_costs["structure_generation"]),
                "theme_generation_cost": float(self.service_costs["theme_generation"]),
                "page_generation_cost": float(self.service_costs["page_generation"]),
                "validation_cost": float(self.service_costs["validation"]),
                "edit_cost": float(self.service_costs["edit"]),
                "total_input_tokens": self.total_input_tokens,
                "total_output_tokens": self.total_output_tokens,
                "total_tokens": self.total_input_tokens + self.total_output_tokens,
                "total_cost_usd": float(total_cost),
                "models_used": self.model_calls,
                "generation_time_seconds": generation_time,
                "retry_count": self.retry_count,
                "status": self.status,
                "error_message": self.error_message
            }
            
            response = supabase_client.table("generation_cost_tracking")\
                .insert(record_data)\
                .execute()
            
            if response.data:
                tracking_id = response.data[0]["id"]
                logger.info(
                    f"[COST TRACKER] ✓ Saved cost tracking: {tracking_id} | "
                    f"Total: ${total_cost:.6f} | Tokens: {self.total_input_tokens + self.total_output_tokens}"
                )
                return tracking_id
            else:
                logger.error("[COST TRACKER] Failed to save cost tracking: No data returned")
                return None
                
        except Exception as e:
            logger.error(f"[COST TRACKER] Error saving cost tracking: {str(e)}")
            return None
    
    def get_summary_string(self) -> str:
        """Get human-readable summary of costs"""
        total_cost = self.get_total_cost()
        return (
            f"Cost Summary: ${total_cost:.4f} | "
            f"Tokens: {self.total_input_tokens + self.total_output_tokens:,} | "
            f"Calls: {len(self.model_calls)}"
        )


def clear_pricing_cache():
    """Clear the pricing cache. Useful when pricing is updated."""
    _pricing_cache.clear()
    logger.info("[COST] Pricing cache cleared")


def get_project_costs(project_id: str, supabase_client=None) -> Optional[Dict[str, Any]]:
    """
    Fetch cost tracking data for a project.
    
    Args:
        project_id: Project ID
        supabase_client: Optional Supabase client instance
    
    Returns:
        Cost tracking data or None if not found
    """
    if supabase_client is None:
        supabase_client = get_supabase_client()
    
    try:
        response = supabase_client.table("generation_cost_tracking")\
            .select("*")\
            .eq("project_id", project_id)\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        
        if not response.data:
            return None
        
        return response.data[0]
        
    except Exception as e:
        logger.error(f"[COST] Error fetching project costs: {str(e)}")
        return None

