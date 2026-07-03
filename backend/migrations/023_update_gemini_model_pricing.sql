-- Migration: Update Gemini Model Pricing
-- Description: Seed pricing for the upgraded Gemini 3.x models
-- Date: 2026-07-03

INSERT INTO ai_model_pricing (model_name, provider, input_cost_per_million, output_cost_per_million) VALUES
  ('gemini-3.5-flash', 'google', 1.500, 9.000),
  ('gemini-3.1-flash-lite', 'google', 0.250, 1.500)
ON CONFLICT (model_name) DO NOTHING;
