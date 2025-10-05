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
    '[{"order": 0, "config": {}, "variation": "logo-left", "component_type": "header"}, {"order": 1, "config": {}, "variation": "centered", "component_type": "hero"}, {"order": 2, "config": {}, "variation": "three-column", "component_type": "services"}, {"order": 3, "config": {}, "variation": "banner", "component_type": "cta"}, {"order": 4, "config": {}, "variation": "simple", "component_type": "footer"}]',
    '{"business_name": {"type": "text", "required": true, "placeholder": "Your Startup Name"}, "headline": {"type": "text", "required": true, "placeholder": "Revolutionizing the Future"}, "subheadline": {"type": "text", "required": true, "placeholder": "Building tomorrows solutions today"}, "logo_url": {"type": "image", "required": true, "placeholder": "Logo URL"}, "nav_items": {"type": "array", "default": [{"url": "#home", "label": "Home"}, {"url": "#features", "label": "Features"}, {"url": "#about", "label": "About"}, {"url": "#contact", "label": "Contact"}], "required": true, "itemSchema": {"url": "string", "label": "string"}}, "services": {"type": "array", "default": [], "required": true, "itemSchema": {"icon": "string", "title": "string", "description": "string"}}, "section_title": {"type": "text", "default": "Our Features", "required": true}, "section_description": {"type": "text", "required": false, "placeholder": "What makes us different"}, "cta_text": {"type": "text", "required": true, "placeholder": "Get Started Today"}, "cta_url": {"type": "url", "default": "#contact", "required": false}, "cta_button_text": {"type": "text", "default": "Start Free Trial", "required": true}, "business_email": {"type": "email", "required": true, "placeholder": "hello@startup.com"}, "business_phone": {"type": "phone", "required": false, "placeholder": "+1 (555) 123-4567"}, "copyright_text": {"type": "text", "default": "© 2025 Your Startup. All rights reserved.", "required": true}, "footer_links": {"type": "array", "default": [{"url": "/privacy", "label": "Privacy Policy"}, {"url": "/terms", "label": "Terms of Service"}], "required": false, "itemSchema": {"url": "string", "label": "string"}}}'
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
    '[{"order": 0, "config": {}, "variation": "logo-left", "component_type": "header"}, {"order": 1, "config": {}, "variation": "split", "component_type": "hero"}, {"order": 2, "config": {}, "variation": "grid", "component_type": "portfolio"}, {"order": 3, "config": {}, "variation": "two-column", "component_type": "about"}, {"order": 4, "config": {}, "variation": "form-only", "component_type": "contact"}, {"order": 5, "config": {}, "variation": "simple", "component_type": "footer"}]',
    '{"business_name": {"type": "text", "required": true, "placeholder": "Your Name"}, "headline": {"type": "text", "required": true, "placeholder": "Creative Professional"}, "subheadline": {"type": "text", "required": true, "placeholder": "Bringing ideas to life through design"}, "logo_url": {"type": "image", "required": false, "placeholder": "Profile Image URL"}, "nav_items": {"type": "array", "default": [{"url": "#home", "label": "Home"}, {"url": "#work", "label": "Work"}, {"url": "#about", "label": "About"}, {"url": "#contact", "label": "Contact"}], "required": true, "itemSchema": {"url": "string", "label": "string"}}, "portfolio_items": {"type": "array", "default": [], "required": true, "itemSchema": {"title": "string", "description": "string", "image_url": "string", "project_url": "string"}}, "about_text": {"type": "text", "required": true, "placeholder": "Your story and creative journey"}, "about_image": {"type": "image", "required": true, "placeholder": "About image URL"}, "about_image_alt": {"type": "text", "default": "About me", "required": false}, "business_email": {"type": "email", "required": true, "placeholder": "hello@yourname.com"}, "business_phone": {"type": "phone", "required": false, "placeholder": "+1 (555) 123-4567"}, "whatsapp_number": {"type": "phone", "required": false, "placeholder": "15551234567"}, "form_action": {"type": "url", "default": "/api/contact", "required": false}, "submit_button_text": {"type": "text", "default": "Send Message", "required": true}, "copyright_text": {"type": "text", "default": "© 2025 Your Name. All rights reserved.", "required": true}, "footer_links": {"type": "array", "default": [{"url": "/privacy", "label": "Privacy Policy"}, {"url": "/terms", "label": "Terms of Service"}], "required": false, "itemSchema": {"url": "string", "label": "string"}}}'
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
    '[{"order": 0, "config": {}, "variation": "logo-left", "component_type": "header"}, {"order": 1, "config": {}, "variation": "split", "component_type": "hero"}, {"order": 2, "config": {}, "variation": "three-column", "component_type": "services"}, {"order": 3, "config": {}, "variation": "cards", "component_type": "testimonials"}, {"order": 4, "config": {}, "variation": "banner", "component_type": "cta"}, {"order": 5, "config": {}, "variation": "columns", "component_type": "footer"}]',
    '{"business_name": {"type": "text", "required": true, "placeholder": "Your SaaS Product"}, "headline": {"type": "text", "required": true, "placeholder": "Streamline Your Workflow"}, "subheadline": {"type": "text", "required": true, "placeholder": "The all-in-one solution for modern teams"}, "logo_url": {"type": "image", "required": true, "placeholder": "Product Logo URL"}, "nav_items": {"type": "array", "default": [{"url": "#home", "label": "Home"}, {"url": "#features", "label": "Features"}, {"url": "#pricing", "label": "Pricing"}, {"url": "#contact", "label": "Contact"}], "required": true, "itemSchema": {"url": "string", "label": "string"}}, "services": {"type": "array", "default": [], "required": true, "itemSchema": {"icon": "string", "title": "string", "description": "string"}}, "section_title": {"type": "text", "default": "Key Features", "required": true}, "section_description": {"type": "text", "required": false, "placeholder": "Everything you need to succeed"}, "testimonials": {"type": "array", "default": [], "required": true, "itemSchema": {"quote": "string", "author_name": "string", "author_title": "string"}}, "cta_text": {"type": "text", "required": true, "placeholder": "Start Your Free Trial"}, "cta_url": {"type": "url", "default": "#signup", "required": false}, "cta_button_text": {"type": "text", "default": "Get Started Free", "required": true}, "secondary_cta_url": {"type": "url", "default": "#demo", "required": false}, "secondary_cta_text": {"type": "text", "default": "Watch Demo", "required": false}, "business_email": {"type": "email", "required": true, "placeholder": "support@yourproduct.com"}, "business_phone": {"type": "phone", "required": false, "placeholder": "+1 (555) 123-4567"}, "copyright_text": {"type": "text", "default": "© 2025 Your Product. All rights reserved.", "required": true}, "footer_links": {"type": "array", "default": [{"url": "/privacy", "label": "Privacy Policy"}, {"url": "/terms", "label": "Terms of Service"}, {"url": "/support", "label": "Support"}], "required": false, "itemSchema": {"url": "string", "label": "string"}}}'
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
    '[{"order": 0, "config": {}, "variation": "logo-left", "component_type": "header"}, {"order": 1, "config": {}, "variation": "centered", "component_type": "hero"}, {"order": 2, "config": {}, "variation": "two-column", "component_type": "about"}, {"order": 3, "config": {}, "variation": "four-column", "component_type": "services"}, {"order": 4, "config": {}, "variation": "split-info", "component_type": "contact"}, {"order": 5, "config": {}, "variation": "simple", "component_type": "footer"}]',
    '{"business_name": {"type": "text", "required": true, "placeholder": "Your Restaurant Name"}, "headline": {"type": "text", "required": true, "placeholder": "Welcome to Our Restaurant"}, "subheadline": {"type": "text", "required": true, "placeholder": "Experience fine dining at its best"}, "logo_url": {"type": "image", "required": true, "placeholder": "Restaurant Logo URL"}, "nav_items": {"type": "array", "default": [{"url": "#home", "label": "Home"}, {"url": "#menu", "label": "Menu"}, {"url": "#about", "label": "About"}, {"url": "#contact", "label": "Contact"}], "required": true, "itemSchema": {"url": "string", "label": "string"}}, "about_text": {"type": "text", "required": true, "placeholder": "Our story and mission"}, "about_image": {"type": "image", "required": true, "placeholder": "Restaurant interior image URL"}, "about_image_alt": {"type": "text", "default": "Restaurant interior", "required": false}, "services": {"type": "array", "default": [], "required": true, "itemSchema": {"icon": "string", "title": "string", "description": "string"}}, "section_title": {"type": "text", "default": "Our Menu", "required": true}, "section_description": {"type": "text", "required": false, "placeholder": "Delicious dishes crafted with love"}, "business_email": {"type": "email", "required": true, "placeholder": "info@restaurant.com"}, "business_phone": {"type": "phone", "required": false, "placeholder": "+1 (555) 123-4567"}, "whatsapp_number": {"type": "phone", "required": false, "placeholder": "15551234567"}, "highlights": {"type": "array", "required": false, "itemSchema": {"label": "string", "value": "string"}}, "cta_text": {"type": "text", "required": true, "placeholder": "Ready to dine with us?"}, "cta_url": {"type": "url", "default": "#contact", "required": false}, "cta_button_text": {"type": "text", "default": "Reserve Now", "required": true}, "secondary_cta_url": {"type": "url", "default": "#menu", "required": false}, "secondary_cta_text": {"type": "text", "default": "View Menu", "required": false}, "form_action": {"type": "url", "default": "/api/contact", "required": false}, "submit_button_text": {"type": "text", "default": "Send Message", "required": true}, "copyright_text": {"type": "text", "default": "© 2025 Your Restaurant. All rights reserved.", "required": true}, "footer_links": {"type": "array", "default": [{"url": "/privacy", "label": "Privacy Policy"}, {"url": "/terms", "label": "Terms of Service"}], "required": false, "itemSchema": {"url": "string", "label": "string"}}}'
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
    '[{"order": 0, "config": {}, "variation": "logo-left", "component_type": "header"}, {"order": 1, "config": {}, "variation": "centered", "component_type": "hero"}, {"order": 2, "config": {}, "variation": "two-column", "component_type": "about"}, {"order": 3, "config": {}, "variation": "masonry", "component_type": "portfolio"}, {"order": 4, "config": {}, "variation": "carousel", "component_type": "testimonials"}, {"order": 5, "config": {}, "variation": "split-info", "component_type": "contact"}, {"order": 6, "config": {}, "variation": "columns", "component_type": "footer"}]',
    '{"business_name": {"type": "text", "required": true, "placeholder": "The Artisan Studio"}, "headline": {"type": "text", "required": true, "placeholder": "Crafting Excellence"}, "subheadline": {"type": "text", "required": true, "placeholder": "Where tradition meets innovation"}, "logo_url": {"type": "image", "required": true, "placeholder": "Studio Logo URL"}, "nav_items": {"type": "array", "default": [{"url": "#home", "label": "Home"}, {"url": "#about", "label": "About"}, {"url": "#portfolio", "label": "Portfolio"}, {"url": "#contact", "label": "Contact"}], "required": true, "itemSchema": {"url": "string", "label": "string"}}, "about_text": {"type": "text", "required": true, "placeholder": "Our story of craftsmanship and creativity"}, "about_image": {"type": "image", "required": true, "placeholder": "Studio workspace image URL"}, "about_image_alt": {"type": "text", "default": "Our studio", "required": false}, "portfolio_items": {"type": "array", "default": [], "required": true, "itemSchema": {"title": "string", "description": "string", "image_url": "string", "project_url": "string"}}, "testimonials": {"type": "array", "default": [], "required": true, "itemSchema": {"quote": "string", "author_name": "string", "author_title": "string"}}, "services": {"type": "array", "default": [], "required": true, "itemSchema": {"icon": "string", "title": "string", "description": "string"}}, "section_title": {"type": "text", "default": "Our Work", "required": true}, "section_description": {"type": "text", "required": false, "placeholder": "Showcasing our finest creations"}, "business_email": {"type": "email", "required": true, "placeholder": "hello@theartisan.com"}, "business_phone": {"type": "phone", "required": false, "placeholder": "+1 (555) 123-4567"}, "whatsapp_number": {"type": "phone", "required": false, "placeholder": "15551234567"}, "cta_text": {"type": "text", "required": true, "placeholder": "Lets create something amazing together"}, "cta_url": {"type": "url", "default": "#contact", "required": false}, "cta_button_text": {"type": "text", "default": "Start Your Project", "required": true}, "secondary_cta_url": {"type": "url", "default": "#portfolio", "required": false}, "secondary_cta_text": {"type": "text", "default": "View Our Work", "required": false}, "form_action": {"type": "url", "default": "/api/contact", "required": false}, "submit_button_text": {"type": "text", "default": "Send Message", "required": true}, "copyright_text": {"type": "text", "default": "© 2025 The Artisan. All rights reserved.", "required": true}, "footer_links": {"type": "array", "default": [{"url": "/privacy", "label": "Privacy Policy"}, {"url": "/terms", "label": "Terms of Service"}], "required": false, "itemSchema": {"url": "string", "label": "string"}}}'
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

