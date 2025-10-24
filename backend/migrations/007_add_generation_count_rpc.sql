-- =====================================================
-- Update RPC function to use actual project count
-- Version: 2.0
-- Created: 2025-01-XX
-- Description: Modifies increment_generation_count to recalculate actual project count
-- =====================================================

-- =====================================================
-- SECTION 1: UPDATE RPC FUNCTION
-- =====================================================

-- Function to update generation count based on actual project count
CREATE OR REPLACE FUNCTION public.increment_generation_count(user_id_param UUID)
RETURNS void AS $$
DECLARE
    actual_project_count INTEGER;
BEGIN
    -- Count actual projects for the user (excluding soft-deleted)
    SELECT COUNT(*)
    INTO actual_project_count
    FROM public.projects
    WHERE user_id = user_id_param 
    AND deleted_at IS NULL;
    
    -- Update user with actual project count
    UPDATE public.users
    SET 
        current_period_generations = current_period_generations + 1,
        generation_count = COALESCE(actual_project_count, 0),
        updated_at = NOW()
    WHERE id = user_id_param;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Update comment
COMMENT ON FUNCTION public.increment_generation_count IS 'Updates generation_count to reflect actual project count and increments current_period_generations';

-- =====================================================
-- SECTION 2: GRANT PERMISSIONS (Already exists, but keeping for completeness)
-- =====================================================

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION public.increment_generation_count(UUID) TO authenticated;

-- =====================================================
-- MIGRATION COMPLETE
-- Updated: increment_generation_count now uses actual project count
-- =====================================================