def open_ai_response_sample():
    return """
    {
        "name": "Modern Restaurant Template",
        "description": "A contemporary restaurant website with elegant design and user-friendly navigation",
        "sections": [
            {
            "component_type": "header",
            "variation": "logo-left",
            "order": 0,
            "config": {}
            },
            {
            "component_type": "hero",
            "variation": "centered",
            "order": 1,
            "config": {}
            },
            {
            "component_type": "services",
            "variation": "three-column",
            "order": 2,
            "config": {}
            },
            {
            "component_type": "about",
            "variation": "two-column",
            "order": 3,
            "config": {}
            },
            {
            "component_type": "testimonials",
            "variation": "cards",
            "order": 4,
            "config": {}
            },
            {
            "component_type": "cta",
            "variation": "banner",
            "order": 5,
            "config": {}
            },
            {
            "component_type": "contact",
            "variation": "split-info",
            "order": 6,
            "config": {}
            },
            {
            "component_type": "footer",
            "variation": "columns",
            "order": 7,
            "config": {}
            }
        ],
        "style_config": {
            "colors": {
            "primary": "#d97706",
            "secondary": "#f59e0b",
            "text": "#1f2937",
            "heading": "#111827",
            "background": "#ffffff",
            "border": "#e5e7eb"
            },
            "typography": {
            "fontFamily": "'Inter', sans-serif",
            "headingFontFamily": "'Playfair Display', serif",
            "fontSize": "16px",
            "lineHeight": "1.6"
            },
            "spacing": {
            "containerMaxWidth": "1200px",
            "sm": "1rem",
            "md": "1.5rem",
            "lg": "2rem",
            "xl": "3rem",
            "2xl": "5rem"
            }
        },
        "content_schema": {
            "business_name": {
            "type": "text",
            "required": true,
            "placeholder": "Your Restaurant Name"
            },
            "logo_url": {
            "type": "image",
            "required": true,
            "placeholder": "Logo URL"
            },
            "nav_items": {
            "type": "array",
            "required": true,
            "itemSchema": {
                "label": "string",
                "url": "string"
            },
            "default": [
                {"label": "Home", "url": "#home"},
                {"label": "Menu", "url": "#menu"},
                {"label": "About", "url": "#about"},
                {"label": "Contact", "url": "#contact"}
            ]
            },
            "headline": {
            "type": "text",
            "required": true,
            "placeholder": "Welcome to Our Restaurant"
            },
            "subheadline": {
            "type": "text",
            "required": true,
            "placeholder": "Experience fine dining at its best"
            },
            "cta_text": {
            "type": "text",
            "required": true,
            "default": "Reserve Table"
            },
            "cta_url": {
            "type": "url",
            "required": false,
            "default": "#contact"
            },
            "secondary_cta_text": {
            "type": "text",
            "required": false,
            "default": "View Menu"
            },
            "secondary_cta_url": {
            "type": "url",
            "required": false,
            "default": "#menu"
            },
            "section_title": {
            "type": "text",
            "required": true,
            "default": "Our Services"
            },
            "section_description": {
            "type": "text",
            "required": false,
            "placeholder": "What we offer"
            },
            "services": {
            "type": "array",
            "required": true,
            "itemSchema": {
                "icon": "string",
                "title": "string",
                "description": "string"
            },
            "default": []
            },
            "about_text": {
            "type": "text",
            "required": true,
            "placeholder": "Our story and mission"
            },
            "about_image": {
            "type": "image",
            "required": true,
            "placeholder": "About image URL"
            },
            "about_image_alt": {
            "type": "text",
            "required": false,
            "default": "About us"
            },
            "highlights": {
            "type": "array",
            "required": false,
            "itemSchema": {
                "value": "string",
                "label": "string"
            }
            },
            "testimonials": {
            "type": "array",
            "required": true,
            "itemSchema": {
                "quote": "string",
                "author_name": "string",
                "author_title": "string"
            },
            "default": []
            },
            "cta_title": {
            "type": "text",
            "required": true,
            "placeholder": "Ready to dine with us?"
            },
            "cta_text": {
            "type": "text",
            "required": true,
            "placeholder": "Book your table today"
            },
            "cta_button_text": {
            "type": "text",
            "required": true,
            "default": "Reserve Now"
            },
            "cta_url": {
            "type": "url",
            "required": false,
            "default": "#contact"
            },
            "business_email": {
            "type": "email",
            "required": true,
            "placeholder": "info@restaurant.com"
            },
            "business_phone": {
            "type": "phone",
            "required": false,
            "placeholder": "+1 (555) 123-4567"
            },
            "whatsapp_number": {
            "type": "phone",
            "required": false,
            "placeholder": "15551234567"
            },
            "submit_button_text": {
            "type": "text",
            "required": true,
            "default": "Send Message"
            },
            "form_action": {
            "type": "url",
            "required": false,
            "default": "/api/contact"
            },
            "business_description": {
            "type": "text",
            "required": false,
            "placeholder": "Brief description"
            },
            "copyright_text": {
            "type": "text",
            "required": true,
            "default": "© 2025 Your Restaurant. All rights reserved."
            },
            "footer_links": {
            "type": "array",
            "required": false,
            "itemSchema": {
                "label": "string",
                "url": "string"
            },
            "default": [
                {"label": "Privacy Policy", "url": "/privacy"},
                {"label": "Terms of Service", "url": "/terms"}
            ]
            }
        },
        "meta": {
            "category": "restaurant",
            "tags": ["modern", "elegant", "fine-dining"]
        }
        }
    """