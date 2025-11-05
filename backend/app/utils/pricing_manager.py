"""
Pricing Manager Utility
Manages AI model pricing updates and cache invalidation.
"""

import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime
from app.utils.supabase_client import get_supabase_client
from app.services.cost_calculator import clear_pricing_cache

logger = logging.getLogger(__name__)


class PricingManagerError(Exception):
    """Custom exception for pricing manager errors"""
    pass


class PricingManager:
    """Manages AI model pricing in the database"""
    
    def __init__(self, supabase_client=None):
        """Initialize pricing manager"""
        self.supabase = supabase_client or get_supabase_client()
    
    def get_all_pricing(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get all model pricing records.
        
        Args:
            active_only: If True, only return active pricing
        
        Returns:
            List of pricing records
        """
        try:
            query = self.supabase.table("ai_model_pricing").select("*")
            
            if active_only:
                query = query.eq("is_active", True)
            
            response = query.order("provider", desc=False)\
                .order("model_name", desc=False)\
                .execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"[PRICING MGR] Error fetching all pricing: {str(e)}")
            raise PricingManagerError(f"Failed to fetch pricing: {str(e)}")
    
    def get_pricing_by_model(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get pricing for a specific model.
        
        Args:
            model_name: Name of the AI model
        
        Returns:
            Pricing record or None if not found
        """
        try:
            response = self.supabase.table("ai_model_pricing")\
                .select("*")\
                .eq("model_name", model_name)\
                .eq("is_active", True)\
                .execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"[PRICING MGR] Error fetching pricing for {model_name}: {str(e)}")
            return None
    
    def update_pricing(
        self,
        model_name: str,
        input_cost_per_million: Optional[Decimal] = None,
        output_cost_per_million: Optional[Decimal] = None,
        invalidate_cache: bool = True
    ) -> bool:
        """
        Update pricing for an existing model.
        
        Args:
            model_name: Name of the AI model
            input_cost_per_million: New input cost (USD per million tokens)
            output_cost_per_million: New output cost (USD per million tokens)
            invalidate_cache: Whether to clear the pricing cache
        
        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {}
            
            if input_cost_per_million is not None:
                update_data["input_cost_per_million"] = float(input_cost_per_million)
            
            if output_cost_per_million is not None:
                update_data["output_cost_per_million"] = float(output_cost_per_million)
            
            if not update_data:
                logger.warning(f"[PRICING MGR] No pricing data provided for update")
                return False
            
            response = self.supabase.table("ai_model_pricing")\
                .update(update_data)\
                .eq("model_name", model_name)\
                .execute()
            
            if response.data:
                logger.info(
                    f"[PRICING MGR] ✓ Updated pricing for {model_name}: "
                    f"in=${update_data.get('input_cost_per_million', 'unchanged')} "
                    f"out=${update_data.get('output_cost_per_million', 'unchanged')}"
                )
                
                if invalidate_cache:
                    clear_pricing_cache()
                    logger.info("[PRICING MGR] Cache invalidated after pricing update")
                
                return True
            else:
                logger.error(f"[PRICING MGR] Failed to update pricing for {model_name}")
                return False
                
        except Exception as e:
            logger.error(f"[PRICING MGR] Error updating pricing: {str(e)}")
            raise PricingManagerError(f"Failed to update pricing: {str(e)}")
    
    def add_model_pricing(
        self,
        model_name: str,
        provider: str,
        input_cost_per_million: Decimal,
        output_cost_per_million: Decimal,
        invalidate_cache: bool = True
    ) -> bool:
        """
        Add pricing for a new model.
        
        Args:
            model_name: Name of the AI model
            provider: Provider name ('openai', 'anthropic', 'google')
            input_cost_per_million: Input cost (USD per million tokens)
            output_cost_per_million: Output cost (USD per million tokens)
            invalidate_cache: Whether to clear the pricing cache
        
        Returns:
            True if successful, False otherwise
        """
        try:
            pricing_data = {
                "model_name": model_name,
                "provider": provider,
                "input_cost_per_million": float(input_cost_per_million),
                "output_cost_per_million": float(output_cost_per_million),
                "is_active": True,
                "effective_from": datetime.utcnow().isoformat()
            }
            
            response = self.supabase.table("ai_model_pricing")\
                .insert(pricing_data)\
                .execute()
            
            if response.data:
                logger.info(
                    f"[PRICING MGR] ✓ Added pricing for {model_name} ({provider}): "
                    f"in=${input_cost_per_million} out=${output_cost_per_million}"
                )
                
                if invalidate_cache:
                    clear_pricing_cache()
                    logger.info("[PRICING MGR] Cache invalidated after adding pricing")
                
                return True
            else:
                logger.error(f"[PRICING MGR] Failed to add pricing for {model_name}")
                return False
                
        except Exception as e:
            logger.error(f"[PRICING MGR] Error adding pricing: {str(e)}")
            raise PricingManagerError(f"Failed to add pricing: {str(e)}")
    
    def deactivate_model(self, model_name: str, invalidate_cache: bool = True) -> bool:
        """
        Deactivate a model (mark as inactive).
        
        Args:
            model_name: Name of the AI model
            invalidate_cache: Whether to clear the pricing cache
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.supabase.table("ai_model_pricing")\
                .update({"is_active": False})\
                .eq("model_name", model_name)\
                .execute()
            
            if response.data:
                logger.info(f"[PRICING MGR] ✓ Deactivated model: {model_name}")
                
                if invalidate_cache:
                    clear_pricing_cache()
                    logger.info("[PRICING MGR] Cache invalidated after deactivation")
                
                return True
            else:
                logger.error(f"[PRICING MGR] Failed to deactivate model: {model_name}")
                return False
                
        except Exception as e:
            logger.error(f"[PRICING MGR] Error deactivating model: {str(e)}")
            raise PricingManagerError(f"Failed to deactivate model: {str(e)}")
    
    def reactivate_model(self, model_name: str, invalidate_cache: bool = True) -> bool:
        """
        Reactivate a model (mark as active).
        
        Args:
            model_name: Name of the AI model
            invalidate_cache: Whether to clear the pricing cache
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.supabase.table("ai_model_pricing")\
                .update({"is_active": True})\
                .eq("model_name", model_name)\
                .execute()
            
            if response.data:
                logger.info(f"[PRICING MGR] ✓ Reactivated model: {model_name}")
                
                if invalidate_cache:
                    clear_pricing_cache()
                    logger.info("[PRICING MGR] Cache invalidated after reactivation")
                
                return True
            else:
                logger.error(f"[PRICING MGR] Failed to reactivate model: {model_name}")
                return False
                
        except Exception as e:
            logger.error(f"[PRICING MGR] Error reactivating model: {str(e)}")
            raise PricingManagerError(f"Failed to reactivate model: {str(e)}")
    
    def get_pricing_by_provider(self, provider: str) -> List[Dict[str, Any]]:
        """
        Get all pricing for a specific provider.
        
        Args:
            provider: Provider name ('openai', 'anthropic', 'google')
        
        Returns:
            List of pricing records
        """
        try:
            response = self.supabase.table("ai_model_pricing")\
                .select("*")\
                .eq("provider", provider)\
                .eq("is_active", True)\
                .order("model_name", desc=False)\
                .execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"[PRICING MGR] Error fetching pricing for provider {provider}: {str(e)}")
            return []
    
    def bulk_update_provider_pricing(
        self,
        provider: str,
        pricing_updates: List[Dict[str, Any]],
        invalidate_cache: bool = True
    ) -> Dict[str, int]:
        """
        Bulk update pricing for multiple models from a provider.
        
        Args:
            provider: Provider name
            pricing_updates: List of dicts with 'model_name', 'input_cost_per_million', 'output_cost_per_million'
            invalidate_cache: Whether to clear the pricing cache
        
        Returns:
            Dict with counts: {'updated': int, 'failed': int}
        """
        updated_count = 0
        failed_count = 0
        
        for update in pricing_updates:
            model_name = update.get("model_name")
            input_cost = update.get("input_cost_per_million")
            output_cost = update.get("output_cost_per_million")
            
            if not model_name:
                failed_count += 1
                continue
            
            # Check if model exists
            existing = self.get_pricing_by_model(model_name)
            
            if existing:
                # Update existing
                success = self.update_pricing(
                    model_name,
                    Decimal(str(input_cost)) if input_cost is not None else None,
                    Decimal(str(output_cost)) if output_cost is not None else None,
                    invalidate_cache=False  # We'll invalidate once at the end
                )
            else:
                # Add new
                success = self.add_model_pricing(
                    model_name,
                    provider,
                    Decimal(str(input_cost)),
                    Decimal(str(output_cost)),
                    invalidate_cache=False
                )
            
            if success:
                updated_count += 1
            else:
                failed_count += 1
        
        if invalidate_cache and updated_count > 0:
            clear_pricing_cache()
            logger.info(f"[PRICING MGR] Cache invalidated after bulk update")
        
        logger.info(
            f"[PRICING MGR] Bulk update complete for {provider}: "
            f"{updated_count} updated, {failed_count} failed"
        )
        
        return {"updated": updated_count, "failed": failed_count}


# Create singleton instance
pricing_manager = PricingManager()


def refresh_pricing_cache():
    """Force refresh of pricing cache"""
    clear_pricing_cache()
    logger.info("[PRICING MGR] Pricing cache refreshed")

