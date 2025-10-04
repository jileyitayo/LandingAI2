-- =====================================================
-- SiteSmith Database Migration - Sample Templates
-- Version: 1.1
-- Created: 2025-10-04
-- Description: Seed database with system templates for AI website generation
-- =====================================================

-- =====================================================
-- SECTION 1: SAMPLE TEMPLATES
-- Insert system templates with basic component structures
-- =====================================================

-- Template 1: Modern Startup Landing
INSERT INTO public.templates (
    name,
    description,
    category,
    tags,
    is_system_template,
    is_active,
    is_public,
    style_config,
    sections_config,
    content_schema
) VALUES (
    'Startup Landing',
    'Modern startup template with hero section and features',
    'business',
    ARRAY['modern', 'professional', 'startup', 'business'],
    true,
    true,
    false,
    '{"colorScheme": {"primary": "#6366f1", "secondary": "#8b5cf6", "accent": "#06b6d4"}, "typography": {"headingFont": "Inter", "bodyFont": "Inter"}, "spacing": "comfortable"}',
    '{"sections": [{"id": "header-1", "type": "header", "order": 1, "variation": "centered-logo"}, {"id": "hero-1", "type": "hero", "order": 2, "variation": "centered"}, {"id": "services-1", "type": "services", "order": 3, "variation": "three-column-grid"}, {"id": "cta-1", "type": "cta", "order": 4, "variation": "centered"}, {"id": "footer-1", "type": "footer", "order": 5, "variation": "simple"}]}',
    '{"required_fields": {"business_name": "string", "tagline": "string", "services": "array", "cta_text": "string"}}'
);

-- Template 2: Minimalist Portfolio
INSERT INTO public.templates (
    name,
    description,
    category,
    tags,
    is_system_template,
    is_active,
    is_public,
    style_config,
    sections_config,
    content_schema
) VALUES (
    'Minimalist',
    'Clean portfolio template for creatives and professionals',
    'portfolio',
    ARRAY['minimal', 'clean', 'portfolio', 'creative'],
    true,
    true,
    false,
    '{"colorScheme": {"primary": "#000000", "secondary": "#4a5568", "accent": "#f59e0b"}, "typography": {"headingFont": "Playfair Display", "bodyFont": "Inter"}, "spacing": "spacious"}',
    '{"sections": [{"id": "header-1", "type": "header", "order": 1, "variation": "logo-left-right-aligned-menu"}, {"id": "hero-1", "type": "hero", "order": 2, "variation": "split"}, {"id": "portfolio-1", "type": "portfolio", "order": 3, "variation": "grid"}, {"id": "about-1", "type": "about", "order": 4, "variation": "two-column"}, {"id": "contact-1", "type": "contact", "order": 5, "variation": "form-only"}, {"id": "footer-1", "type": "footer", "order": 6, "variation": "simple"}]}',
    '{"required_fields": {"name": "string", "profession": "string", "bio": "string", "portfolio_items": "array", "contact_email": "string"}}'
);

-- Template 3: SaaS Product Landing
INSERT INTO public.templates (
    name,
    description,
    category,
    tags,
    is_system_template,
    is_active,
    is_public,
    style_config,
    sections_config,
    content_schema
) VALUES (
    'SaaS Product',
    'Professional SaaS landing page with feature highlights',
    'business',
    ARRAY['saas', 'tech', 'professional', 'modern'],
    true,
    true,
    false,
    '{"colorScheme": {"primary": "#3b82f6", "secondary": "#1e40af", "accent": "#10b981"}, "typography": {"headingFont": "Inter", "bodyFont": "Inter"}, "spacing": "comfortable"}',
    '{"sections": [{"id": "header-1", "type": "header", "order": 1, "variation": "logo-left-right-aligned-menu"}, {"id": "hero-1", "type": "hero", "order": 2, "variation": "split"}, {"id": "services-1", "type": "services", "order": 3, "variation": "three-column-grid"}, {"id": "testimonials-1", "type": "testimonials", "order": 4, "variation": "cards"}, {"id": "cta-1", "type": "cta", "order": 5, "variation": "banner"}, {"id": "footer-1", "type": "footer", "order": 6, "variation": "columns"}]}',
    '{"required_fields": {"product_name": "string", "tagline": "string", "features": "array", "testimonials": "array", "cta_text": "string"}}'
);

-- Template 4: Restaurant & Menu
INSERT INTO public.templates (
    name,
    description,
    category,
    tags,
    is_system_template,
    is_active,
    is_public,
    style_config,
    sections_config,
    content_schema
) VALUES (
    'Restaurant',
    'Restaurant template with menu showcase and reservations',
    'restaurant',
    ARRAY['restaurant', 'food', 'dining', 'menu'],
    true,
    true,
    false,
    '{"colorScheme": {"primary": "#dc2626", "secondary": "#991b1b", "accent": "#f59e0b"}, "typography": {"headingFont": "Playfair Display", "bodyFont": "Inter"}, "spacing": "comfortable"}',
    '{"sections": [{"id": "header-1", "type": "header", "order": 1, "variation": "centered-logo"}, {"id": "hero-1", "type": "hero", "order": 2, "variation": "full-width"}, {"id": "about-1", "type": "about", "order": 3, "variation": "centered"}, {"id": "services-1", "type": "services", "order": 4, "variation": "four-column-grid"}, {"id": "contact-1", "type": "contact", "order": 5, "variation": "split-info"}, {"id": "footer-1", "type": "footer", "order": 6, "variation": "simple"}]}',
    '{"required_fields": {"restaurant_name": "string", "description": "string", "menu_items": "array", "location": "string", "phone": "string", "hours": "string"}}'
);

-- Template 5: Creative Agency / The Artisan
INSERT INTO public.templates (
    name,
    description,
    category,
    tags,
    is_system_template,
    is_active,
    is_public,
    style_config,
    sections_config,
    content_schema
) VALUES (
    'The artisan',
    'Creative agency showcase for artisans and local businesses',
    'services',
    ARRAY['creative', 'agency', 'artisan', 'african', 'local'],
    true,
    true,
    false,
    '{"colorScheme": {"primary": "#7c3aed", "secondary": "#5b21b6", "accent": "#f97316"}, "typography": {"headingFont": "Poppins", "bodyFont": "Inter"}, "spacing": "comfortable"}',
    '{"sections": [{"id": "header-1", "type": "header", "order": 1, "variation": "logo-left-right-aligned-menu"}, {"id": "hero-1", "type": "hero", "order": 2, "variation": "centered"}, {"id": "about-1", "type": "about", "order": 3, "variation": "two-column"}, {"id": "portfolio-1", "type": "portfolio", "order": 4, "variation": "masonry"}, {"id": "testimonials-1", "type": "testimonials", "order": 5, "variation": "carousel"}, {"id": "contact-1", "type": "contact", "order": 6, "variation": "split-info"}, {"id": "footer-1", "type": "footer", "order": 7, "variation": "columns"}]}',
    '{"required_fields": {"business_name": "string", "tagline": "string", "about": "string", "services": "array", "portfolio_items": "array", "whatsapp_number": "string"}}'
);

-- =====================================================
-- END SECTION 1: SAMPLE TEMPLATES
-- =====================================================


-- =====================================================
-- SECTION 2: VERIFICATION
-- Verify templates were inserted correctly
-- =====================================================

-- Check that all templates were inserted
DO $$
DECLARE
    template_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO template_count FROM public.templates WHERE is_system_template = true;
    
    IF template_count = 5 THEN
        RAISE NOTICE 'Successfully inserted 5 system templates';
    ELSE
        RAISE WARNING 'Expected 5 system templates but found %', template_count;
    END IF;
END $$;

-- =====================================================
-- END SECTION 2: VERIFICATION
-- =====================================================


-- =====================================================
-- MIGRATION COMPLETE
-- Templates Added: 5 system templates
-- Categories: business, portfolio, restaurant, services
-- =====================================================

