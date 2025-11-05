-- Migration: Add Cost Tracking System
-- Description: Creates tables for AI model pricing and generation cost tracking
-- Date: 2025-11-05

-- ============================================================================
-- Table 1: ai_model_pricing
-- Stores current pricing for all AI models used in the system
-- ============================================================================

CREATE TABLE IF NOT EXISTS ai_model_pricing (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  model_name VARCHAR(100) UNIQUE NOT NULL,
  provider VARCHAR(50) NOT NULL,  -- 'openai', 'anthropic', 'google'
  input_cost_per_million DECIMAL(10, 6) NOT NULL,
  output_cost_per_million DECIMAL(10, 6) NOT NULL,
  is_active BOOLEAN DEFAULT true,
  effective_from TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create index for active pricing lookups
CREATE INDEX IF NOT EXISTS idx_model_pricing_active ON ai_model_pricing(model_name, is_active);
CREATE INDEX IF NOT EXISTS idx_model_pricing_provider ON ai_model_pricing(provider);

-- Insert initial pricing data for all models
INSERT INTO ai_model_pricing (model_name, provider, input_cost_per_million, output_cost_per_million) VALUES
  ('gpt-4o-mini', 'openai', 0.150, 0.600),
  ('gpt-4o', 'openai', 2.500, 10.000),
  ('gpt-4.1-mini', 'openai', 0.400, 1.600),
  ('gpt-5-mini', 'openai', 0.250, 2.000),
  ('gpt-5', 'openai', 1.250, 10.000),
  ('o4-mini', 'openai', 1.100, 4.400),
  ('o3-mini', 'openai', 1.100, 4.400),
  ('gemini-2.5-flash', 'google', 0.075, 0.300),
  ('gemini-2.5-pro', 'google', 1.250, 5.000),
  ('claude-sonnet-4-5', 'anthropic', 3.000, 15.000),
  ('claude-3-opus', 'anthropic', 15.000, 75.000),
  ('claude-3-sonnet', 'anthropic', 3.000, 15.000),
  ('claude-3-haiku', 'anthropic', 0.250, 1.250)
ON CONFLICT (model_name) DO NOTHING;

-- ============================================================================
-- Table 2: generation_cost_tracking
-- Tracks costs for each generation with service-level breakdown
-- ============================================================================

CREATE TABLE IF NOT EXISTS generation_cost_tracking (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  
  -- Generation context
  generation_type VARCHAR(50) NOT NULL,  -- 'website', 'edit', 'component'
  endpoint VARCHAR(255),
  
  -- Cost breakdown by service
  business_analysis_cost DECIMAL(10, 6) DEFAULT 0,
  structure_generation_cost DECIMAL(10, 6) DEFAULT 0,
  theme_generation_cost DECIMAL(10, 6) DEFAULT 0,
  page_generation_cost DECIMAL(10, 6) DEFAULT 0,
  validation_cost DECIMAL(10, 6) DEFAULT 0,
  edit_cost DECIMAL(10, 6) DEFAULT 0,
  
  -- Aggregated totals
  total_input_tokens INTEGER NOT NULL DEFAULT 0,
  total_output_tokens INTEGER NOT NULL DEFAULT 0,
  total_tokens INTEGER NOT NULL DEFAULT 0,
  total_cost_usd DECIMAL(10, 6) NOT NULL DEFAULT 0,
  
  -- Model usage details (JSONB for flexibility)
  -- Format: [{"service": "business_analysis", "model": "gemini-2.5-flash", "input_tokens": 1200, "output_tokens": 450, "cost": 0.0012}, ...]
  models_used JSONB DEFAULT '[]'::jsonb,
  
  -- Performance metrics
  generation_time_seconds DECIMAL(8, 2),
  retry_count INTEGER DEFAULT 0,
  
  -- Status tracking
  status VARCHAR(20) DEFAULT 'completed',  -- 'completed', 'failed', 'partial'
  error_message TEXT,
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_cost_tracking_user ON generation_cost_tracking(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cost_tracking_project ON generation_cost_tracking(project_id);
CREATE INDEX IF NOT EXISTS idx_cost_tracking_type ON generation_cost_tracking(generation_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cost_tracking_date ON generation_cost_tracking(created_at DESC);

-- ============================================================================
-- Trigger: Update updated_at timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to ai_model_pricing
DROP TRIGGER IF EXISTS update_ai_model_pricing_updated_at ON ai_model_pricing;
CREATE TRIGGER update_ai_model_pricing_updated_at 
    BEFORE UPDATE ON ai_model_pricing 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to generation_cost_tracking
DROP TRIGGER IF EXISTS update_generation_cost_tracking_updated_at ON generation_cost_tracking;
CREATE TRIGGER update_generation_cost_tracking_updated_at 
    BEFORE UPDATE ON generation_cost_tracking 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Comments for documentation
-- ============================================================================

COMMENT ON TABLE ai_model_pricing IS 'Stores pricing information for AI models used in website generation';
COMMENT ON TABLE generation_cost_tracking IS 'Tracks costs for each website generation with service-level breakdown';

COMMENT ON COLUMN ai_model_pricing.input_cost_per_million IS 'Cost in USD per million input tokens';
COMMENT ON COLUMN ai_model_pricing.output_cost_per_million IS 'Cost in USD per million output tokens';
COMMENT ON COLUMN generation_cost_tracking.models_used IS 'JSONB array of model usage details per service';

