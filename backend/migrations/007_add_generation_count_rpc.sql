-- =====================================================
-- Add RPC function for incrementing generation count
-- Version: 1.0
-- Created: 2025-10-04
-- Description: Adds database function for atomic generation count increment
-- =====================================================

-- =====================================================
-- SECTION 1: RPC FUNCTION
-- =====================================================

-- Function to atomically increment generation counts
CREATE OR REPLACE FUNCTION public.increment_generation_count(user_id_param UUID)
RETURNS void AS $$
BEGIN
    UPDATE public.users
    SET 
        current_period_generations = current_period_generations + 1,
        generation_count = generation_count + 1,
        updated_at = NOW()
    WHERE id = user_id_param;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Add comment
COMMENT ON FUNCTION public.increment_generation_count IS 'Atomically increment both current_period_generations and generation_count for a user';

-- =====================================================
-- END SECTION 1: RPC FUNCTION
-- =====================================================


-- =====================================================
-- SECTION 2: GRANT PERMISSIONS
-- =====================================================

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION public.increment_generation_count(UUID) TO authenticated;

-- =====================================================
-- END SECTION 2: GRANT PERMISSIONS
-- =====================================================


-- =====================================================
-- MIGRATION COMPLETE
-- Added: increment_generation_count RPC function
-- =====================================================

