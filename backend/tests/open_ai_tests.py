# -*- coding: utf-8 -*-
system_prompt_template_generator = """
You are a professional UI/UX expert and web designer. Your task is to generate website templates using a predefined component library.

AVAILABLE COMPONENTS:
{
  "header": {
    "centered-logo": {
      "name": "Centered Logo Header",
      "description": "Header with centered logo and navigation menu below",
      "tags": [
        "header",
        "centered",
        "navigation"
      ],
      "config": {
        "sticky": true,
        "alignment": "center",
        "showBorder": true
      },
      "content_bindings": {
        "logo_url": {
          "type": "image",
          "required": true,
          "placeholder": "Logo URL"
        },
        "business_name": {
          "type": "text",
          "required": true,
          "placeholder": "Business Name"
        },
        "nav_items": {
          "type": "array",
          "required": true,
          "itemSchema": {
            "label": "string",
            "url": "string"
          },
          "default": [
            {
              "label": "Home",
              "url": "#home"
            },
            {
              "label": "Services",
              "url": "#services"
            },
            {
              "label": "About",
              "url": "#about"
            },
            {
              "label": "Contact",
              "url": "#contact"
            }
          ]
        }
      }
    },
    "logo-left": {
      "name": "Logo Left Header",
      "description": "Header with logo on left and right-aligned navigation menu",
      "tags": [
        "header",
        "left-aligned",
        "navigation"
      ],
      "config": {
        "sticky": true,
        "alignment": "left",
        "showBorder": true
      },
      "content_bindings": {
        "logo_url": {
          "type": "image",
          "required": true,
          "placeholder": "Logo URL"
        },
        "business_name": {
          "type": "text",
          "required": true,
          "placeholder": "Business Name"
        },
        "nav_items": {
          "type": "array",
          "required": true,
          "itemSchema": {
            "label": "string",
            "url": "string"
          },
          "default": [
            {
              "label": "Home",
              "url": "#home"
            },
            {
              "label": "Services",
              "url": "#services"
            },
            {
              "label": "About",
              "url": "#about"
            },
            {
              "label": "Contact",
              "url": "#contact"
            }
          ]
        }
      }
    }
  },
  "hero": {
    "centered": {
      "name": "Centered Hero",
      "description": "Full-width hero with centered content and optional background",
      "tags": [
        "hero",
        "centered",
        "full-width"
      ],
      "config": {
        "background": {
          "type": "image",
          "overlay": true,
          "overlayOpacity": 0.4
        },
        "contentAlignment": "center",
        "verticalAlignment": "center",
        "minHeight": "100vh",
        "textColor": "light"
      },
      "content_bindings": {
        "headline": {
          "type": "text",
          "required": true,
          "placeholder": "Your Compelling Headline"
        },
        "subheadline": {
          "type": "text",
          "required": true,
          "placeholder": "A brief description of what you offer"
        },
        "cta_text": {
          "type": "text",
          "required": true,
          "default": "Get Started"
        },
        "cta_url": {
          "type": "url",
          "required": false,
          "default": "#contact"
        },
        "secondary_cta_text": {
          "type": "text",
          "required": false,
          "default": "Learn More"
        },
        "secondary_cta_url": {
          "type": "url",
          "required": false,
          "default": "#services"
        },
        "background_image": {
          "type": "image",
          "required": false
        },
        "background_style": {
          "type": "text",
          "required": false,
          "default": "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);"
        }
      }
    },
    "split": {
      "name": "Split Hero",
      "description": "Hero with content on left and image/media on right",
      "tags": [
        "hero",
        "split",
        "two-column"
      ],
      "config": {
        "layout": "split",
        "contentAlignment": "left",
        "imagePosition": "right"
      },
      "content_bindings": {
        "headline": {
          "type": "text",
          "required": true,
          "placeholder": "Your Business Headline"
        },
        "subheadline": {
          "type": "text",
          "required": true,
          "placeholder": "Describe what makes you unique"
        },
        "cta_text": {
          "type": "text",
          "required": true,
          "default": "Get Started"
        },
        "cta_url": {
          "type": "url",
          "required": false,
          "default": "#contact"
        },
        "hero_image": {
          "type": "image",
          "required": true,
          "placeholder": "Hero image URL"
        },
        "hero_image_alt": {
          "type": "text",
          "required": false,
          "default": "Hero image"
        }
      }
    },
    "full-width": {
      "name": "Full Width Hero",
      "description": "Minimalist full-width hero with large typography",
      "tags": [
        "hero",
        "full-width",
        "minimalist"
      ],
      "config": {
        "layout": "full-width",
        "contentAlignment": "center",
        "minHeight": "75vh",
        "style": "minimalist"
      },
      "content_bindings": {
        "headline": {
          "type": "text",
          "required": true,
          "placeholder": "Make it bold and memorable"
        },
        "subheadline": {
          "type": "text",
          "required": true,
          "placeholder": "Supporting text that adds context"
        },
        "cta_text": {
          "type": "text",
          "required": true,
          "default": "Start Now"
        },
        "cta_url": {
          "type": "url",
          "required": false,
          "default": "#contact"
        }
      }
    }
  },
  "services": {
    "three-column": {
      "name": "Three Column Services",
      "description": "Service cards in a 3-column grid layout",
      "tags": [
        "services",
        "grid",
        "three-column"
      ],
      "config": {
        "columns": 3,
        "cardStyle": "elevated",
        "iconStyle": "outlined"
      },
      "content_bindings": {
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
        }
      }
    },
    "two-column": {
      "name": "Two Column Services",
      "description": "Service cards in a 2-column grid with larger cards",
      "tags": [
        "services",
        "grid",
        "two-column"
      ],
      "config": {
        "columns": 2,
        "cardStyle": "bordered",
        "iconStyle": "solid"
      },
      "content_bindings": {
        "section_title": {
          "type": "text",
          "required": true,
          "default": "What We Do"
        },
        "section_description": {
          "type": "text",
          "required": false,
          "placeholder": "Our expertise"
        },
        "services": {
          "type": "array",
          "required": true,
          "itemSchema": {
            "icon": "string",
            "title": "string",
            "description": "string"
          }
        }
      }
    },
    "list": {
      "name": "Services List",
      "description": "Simple list layout for services",
      "tags": [
        "services",
        "list",
        "vertical"
      ],
      "config": {
        "layout": "list",
        "iconPosition": "left"
      },
      "content_bindings": {
        "section_title": {
          "type": "text",
          "required": true,
          "default": "Services"
        },
        "services": {
          "type": "array",
          "required": true,
          "itemSchema": {
            "icon": "string",
            "title": "string",
            "description": "string"
          }
        }
      }
    }
  },
  "about": {
    "two-column": {
      "name": "Two Column About",
      "description": "About section with image on one side and content on the other",
      "tags": [
        "about",
        "two-column",
        "stats"
      ],
      "config": {
        "layout": "two-column",
        "imagePosition": "left"
      },
      "content_bindings": {
        "section_title": {
          "type": "text",
          "required": true,
          "default": "About Us"
        },
        "about_text": {
          "type": "text",
          "required": true,
          "placeholder": "Tell your story"
        },
        "about_image": {
          "type": "image",
          "required": true,
          "placeholder": "About image URL"
        },
        "about_image_alt": {
          "type": "text",
          "required": false,
          "default": "About"
        },
        "highlights": {
          "type": "array",
          "required": false,
          "itemSchema": {
            "value": "string",
            "label": "string"
          }
        }
      }
    },
    "centered": {
      "name": "Centered About",
      "description": "Centered about section with focused content",
      "tags": [
        "about",
        "centered",
        "features"
      ],
      "config": {
        "layout": "centered",
        "textAlign": "center"
      },
      "content_bindings": {
        "section_title": {
          "type": "text",
          "required": true,
          "default": "Our Story"
        },
        "about_text": {
          "type": "text",
          "required": true,
          "placeholder": "Share your journey"
        },
        "features": {
          "type": "array",
          "required": false,
          "itemSchema": {
            "icon": "string",
            "title": "string",
            "description": "string"
          }
        }
      }
    }
  },
  "cta": {
    "banner": {
      "name": "CTA Banner",
      "description": "Full-width banner call-to-action",
      "tags": [
        "cta",
        "banner",
        "full-width"
      ],
      "config": {
        "style": "banner",
        "background": "gradient"
      },
      "content_bindings": {
        "cta_title": {
          "type": "text",
          "required": true,
          "placeholder": "Ready to get started?"
        },
        "cta_text": {
          "type": "text",
          "required": true,
          "placeholder": "Join thousands of satisfied customers"
        },
        "cta_button_text": {
          "type": "text",
          "required": true,
          "default": "Get Started Today"
        },
        "cta_url": {
          "type": "url",
          "required": false,
          "default": "#contact"
        }
      }
    },
    "centered": {
      "name": "Centered CTA",
      "description": "Simple centered call-to-action box",
      "tags": [
        "cta",
        "centered",
        "boxed"
      ],
      "config": {
        "style": "centered",
        "background": "light"
      },
      "content_bindings": {
        "cta_title": {
          "type": "text",
          "required": true,
          "placeholder": "Take the next step"
        },
        "cta_text": {
          "type": "text",
          "required": true,
          "placeholder": "Let's work together"
        },
        "cta_button_text": {
          "type": "text",
          "required": true,
          "default": "Contact Us"
        },
        "cta_url": {
          "type": "url",
          "required": false,
          "default": "#contact"
        },
        "secondary_cta_text": {
          "type": "text",
          "required": false,
          "default": "Learn More"
        },
        "secondary_cta_url": {
          "type": "url",
          "required": false,
          "default": "#about"
        }
      }
    }
  },
  "contact": {
    "form-only": {
      "name": "Contact Form Only",
      "description": "Simple contact form centered on page",
      "tags": [
        "contact",
        "form",
        "simple"
      ],
      "config": {
        "layout": "form-only",
        "formFields": [
          "name",
          "email",
          "message"
        ]
      },
      "content_bindings": {
        "section_title": {
          "type": "text",
          "required": true,
          "default": "Get in Touch"
        },
        "section_description": {
          "type": "text",
          "required": false,
          "placeholder": "We'd love to hear from you"
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
        }
      }
    },
    "split-info": {
      "name": "Split Contact with Info",
      "description": "Contact form on one side, contact information on the other",
      "tags": [
        "contact",
        "split",
        "info",
        "whatsapp"
      ],
      "config": {
        "layout": "split",
        "showWhatsApp": true,
        "formFields": [
          "name",
          "email",
          "message"
        ]
      },
      "content_bindings": {
        "section_title": {
          "type": "text",
          "required": true,
          "default": "Contact Us"
        },
        "section_description": {
          "type": "text",
          "required": false,
          "placeholder": "Reach out to us"
        },
        "business_email": {
          "type": "email",
          "required": true,
          "placeholder": "your@email.com"
        },
        "business_phone": {
          "type": "phone",
          "required": false,
          "placeholder": "+234 xxx xxx xxxx"
        },
        "whatsapp_number": {
          "type": "phone",
          "required": false,
          "placeholder": "234xxxxxxxxxx"
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
        }
      }
    }
  },
  "testimonials": {
    "cards": {
      "name": "Testimonial Cards",
      "description": "Grid of testimonial cards",
      "tags": [
        "testimonials",
        "cards",
        "grid"
      ],
      "config": {
        "layout": "grid",
        "cardStyle": "elevated"
      },
      "content_bindings": {
        "section_title": {
          "type": "text",
          "required": true,
          "default": "What Our Customers Say"
        },
        "section_description": {
          "type": "text",
          "required": false,
          "placeholder": "Testimonials description"
        },
        "testimonials": {
          "type": "array",
          "required": true,
          "itemSchema": {
            "quote": "string",
            "author_name": "string",
            "author_title": "string"
          }
        }
      }
    },
    "simple": {
      "name": "Simple Testimonials",
      "description": "Minimal testimonial list",
      "tags": [
        "testimonials",
        "simple",
        "list"
      ],
      "config": {
        "layout": "list",
        "style": "minimal"
      },
      "content_bindings": {
        "section_title": {
          "type": "text",
          "required": true,
          "default": "Testimonials"
        },
        "testimonials": {
          "type": "array",
          "required": true,
          "itemSchema": {
            "quote": "string",
            "author_name": "string",
            "author_title": "string"
          }
        }
      }
    }
  },
  "footer": {
    "simple": {
      "name": "Simple Footer",
      "description": "Simple centered footer with copyright and links",
      "tags": [
        "footer",
        "simple",
        "centered"
      ],
      "config": {
        "style": "simple",
        "alignment": "center"
      },
      "content_bindings": {
        "copyright_text": {
          "type": "text",
          "required": true,
          "default": "\u00a9 2025 Your Business. All rights reserved."
        },
        "footer_links": {
          "type": "array",
          "required": false,
          "itemSchema": {
            "label": "string",
            "url": "string"
          },
          "default": [
            {
              "label": "Privacy Policy",
              "url": "/privacy"
            },
            {
              "label": "Terms of Service",
              "url": "/terms"
            }
          ]
        }
      }
    },
    "columns": {
      "name": "Column Footer",
      "description": "Multi-column footer with detailed information",
      "tags": [
        "footer",
        "columns",
        "detailed"
      ],
      "config": {
        "style": "columns",
        "columns": 3
      },
      "content_bindings": {
        "business_name": {
          "type": "text",
          "required": true,
          "placeholder": "Business Name"
        },
        "business_description": {
          "type": "text",
          "required": false,
          "placeholder": "Brief description"
        },
        "business_email": {
          "type": "email",
          "required": false,
          "placeholder": "email@business.com"
        },
        "business_phone": {
          "type": "phone",
          "required": false,
          "placeholder": "+234 xxx xxx xxxx"
        },
        "copyright_text": {
          "type": "text",
          "required": true,
          "default": "\u00a9 2025 Your Business. All rights reserved."
        },
        "footer_links": {
          "type": "array",
          "required": false,
          "itemSchema": {
            "label": "string",
            "url": "string"
          },
          "default": [
            {
              "label": "Home",
              "url": "#home"
            },
            {
              "label": "Services",
              "url": "#services"
            },
            {
              "label": "About",
              "url": "#about"
            },
            {
              "label": "Contact",
              "url": "#contact"
            }
          ]
        }
      }
    }
  }
}

YOUR TASK:
1. Analyze the user's business description and requirements
2. Select 4-7 appropriate sections from the component library
3. Choose component variations that match the desired style and business type
4. Customize colors, fonts, and spacing for brand consistency based on the business type
5. CRITICAL: For each selected component in the content_schema, examine its content_bindings and include ALL bindings that have "required": true in your content_schema
6. Generate a cohesive, professional website structure

SECTION SELECTION GUIDELINES:
- Always include: header, hero, footer (required for every website)
- Business-specific sections: services, about, contact, testimonials, cta
- Choose variations based on content density and style preferences based on the business type
- Consider the business type when selecting components

CONTENT BINDING RULES (CRITICAL):
- Examine the "content_bindings" section of EACH component you select
- For EVERY binding that has "required": true, you MUST include it in your content_schema. Do not exclude any required bindings.
- Copy the exact binding name, type, and placeholder
- Include all required bindings or the template will fail validation
- Example: If you select header "logo-left", you MUST include: logo_url, business_name, nav_items
- Example: If you select cta "banner", you MUST include: cta_title, cta_text, cta_button_text, cta_url
- Example: If you select contact "split-info", you MUST include: business_email, business_phone, whatsapp_number

STYLE CONFIGURATION:
- Primary color: Main brand color (hex code)
- Secondary color: Accent color (hex code)
- Text color: Main text color (hex code)
- Heading color: Heading text color (hex code)
- Background color: Main background (hex code)
- Font family: Primary font (web-safe or Google Fonts)
- Spacing: Consistent spacing scale (sm, md, lg, xl, 2xl)

OUTPUT FORMAT (JSON):
{
  "name": "Template Name",
  "description": "Brief description of the template",
  "sections": [
    {
      "component_type": "header",
      "variation": "logo-left",
      "order": 0,
      "config": {}
    },
    ...
  ],
  "style_config": {
    "colors": {
      "primary": "#6366f1",
      "secondary": "#8b5cf6",
      "text": "#1f2937",
      "heading": "#111827",
      "background": "#ffffff",
      "border": "#e5e7eb"
    },
    "typography": {
      "fontFamily": "'Inter', sans-serif",
      "headingFontFamily": "'Inter', sans-serif",
      "fontSize": "16px",
      "lineHeight": "1.5"
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
      "placeholder": "Your Business Name"
    },
    "logo_url": {
      "type": "image",
      "required": true,
      "placeholder": "Logo URL"
    },
    ...
  },
  "meta": {
    "category": "business|portfolio|restaurant|services|general",
    "tags": ["modern", "professional", "warm"]
  }
}

IMPORTANT RULES:
- Only use components and variations that exist in the component library
- CRITICAL: Ensure content_schema includes ALL required bindings from selected components (check "required": true in content_bindings)
- Style colors must be valid hex codes
- Section order must be sequential (0, 1, 2, ...)
- Don't generate raw HTML - use component references only
- Ensure the design is cohesive and professional
"""

user_prompt_template_generator  = """
USER REQUEST:
A photography business with 15 years of experience

STYLE PREFERENCES:
{
  "primaryColor": "#6366f1"
}

Please generate a website template that matches this description.
"""
# import openai
# import os
# from dotenv import load_dotenv
# load_dotenv()
# openai.api_key = os.getenv("OPENAI_API_KEY")

# print("Sending request to OpenAI")
# response = openai.chat.completions.create(
#     model="gpt-4o-mini",
#     messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
# )

# print(response.choices[0].message.content)

content_template_generator  = """
{
  "name": "Photography Business Template",
  "description": "A professional website template for a photography business with elegant design and seamless navigation.",
  "sections": [
    {
      "component_type": "header",
      "variation": "logo-left",
      "order": 0,
      "config": {}
    },
    {
      "component_type": "hero",
      "variation": "split",
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
      "variation": "simple",
      "order": 7,
      "config": {}
    }
  ],
  "style_config": {
    "colors": {
      "primary": "#6366f1",
      "secondary": "#8b5cf6",
      "text": "#1f2937",
      "heading": "#111827",
      "background": "#ffffff",
      "border": "#e5e7eb"
    },
    "typography": {
      "fontFamily": "'Inter', sans-serif",
      "headingFontFamily": "'Inter', sans-serif",
      "fontSize": "16px",
      "lineHeight": "1.5"
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
      "placeholder": "Your Business Name"
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
        {
          "label": "Home",
          "url": "#home"
        },
        {
          "label": "Portfolio",
          "url": "#portfolio"
        },
        {
          "label": "About",
          "url": "#about"
        },
        {
          "label": "Contact",
          "url": "#contact"
        }
      ]
    },
    "headline": {
      "type": "text",
      "required": true,
      "placeholder": "Capturing Moments, Creating Memories"
    },
    "subheadline": {
      "type": "text",
      "required": true,
      "placeholder": "Professional Photography Services for Every Occasion"
    },
    "cta_text": {
      "type": "text",
      "required": true,
      "default": "View Portfolio"
    },
    "cta_url": {
      "type": "url",
      "required": false,
      "default": "#portfolio"
    },
    "hero_image": {
      "type": "image",
      "required": true,
      "placeholder": "Hero image URL"
    },
    "hero_image_alt": {
      "type": "text",
      "required": false,
      "default": "Photography Hero Image"
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
      "default": [
        {
          "icon": "camera",
          "title": "Wedding Photography",
          "description": "Capturing the magic of your special day."
        },
        {
          "icon": "portrait",
          "title": "Portrait Sessions",
          "description": "Beautiful portraits for individuals and families."
        },
        {
          "icon": "event",
          "title": "Event Photography",
          "description": "Professional coverage for events of all sizes."
        }
      ]
    },
    "section_title": {
      "type": "text",
      "required": true,
      "default": "About Us"
    },
    "about_text": {
      "type": "text",
      "required": true,
      "placeholder": "Tell your story"
    },
    "about_image": {
      "type": "image",
      "required": true,
      "placeholder": "About image URL"
    },
    "about_image_alt": {
      "type": "text",
      "required": false,
      "default": "About Us Image"
    },
    "section_title": {
      "type": "text",
      "required": true,
      "default": "What Our Customers Say"
    },
    "testimonials": {
      "type": "array",
      "required": true,
      "itemSchema": {
        "quote": "string",
        "author_name": "string",
        "author_title": "string"
      },
      "default": [
        {
          "quote": "Amazing experience! The photos were stunning.",
          "author_name": "Jane Doe",
          "author_title": "Happy Customer"
        },
        {
          "quote": "Professional and very talented. Highly recommend!",
          "author_name": "John Smith",
          "author_title": "Wedding Planner"
        }
      ]
    },
    "cta_title": {
      "type": "text",
      "required": true,
      "placeholder": "Ready to book your session?"
    },
    "cta_text": {
      "type": "text",
      "required": true,
      "placeholder": "Join hundreds of satisfied customers"
    },
    "cta_button_text": {
      "type": "text",
      "required": true,
      "default": "Get Started Today"
    },
    "cta_url": {
      "type": "url",
      "required": false,
      "default": "#contact"
    },
    "section_title": {
      "type": "text",
      "required": true,
      "default": "Contact Us"
    },
    "business_email": {
      "type": "email",
      "required": true,
      "placeholder": "your@email.com"
    },
    "business_phone": {
      "type": "phone",
      "required": false,
      "placeholder": "+234 xxx xxx xxxx"
    },
    "whatsapp_number": {
      "type": "phone",
      "required": false,
      "placeholder": "234xxxxxxxxxx"
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
    "copyright_text": {
      "type": "text",
      "required": true,
      "default": "© 2025 Your Business. All rights reserved."
    }
  },
  "meta": {
    "category": "services",
    "tags": ["modern", "professional", "photography"]
  }
}
"""


system_prompt_content_generator = """
You are an expert content writer specializing in website copy for African businesses.
Your task is to generate compelling, localized content for a business website based on a template structure.

TEMPLATE STRUCTURE:
The website has the following sections: header, hero, services, about, testimonials, cta, contact, footer

SECTIONS CONFIGURATION:
{
  "sections": [
    {
      "order": 0,
      "config": {},
      "variation": "logo-left",
      "component_type": "header"
    },
    {
      "order": 1,
      "config": {},
      "variation": "split",
      "component_type": "hero"
    },
    {
      "order": 2,
      "config": {},
      "variation": "three-column",
      "component_type": "services"
    },
    {
      "order": 3,
      "config": {},
      "variation": "two-column",
      "component_type": "about"
    },
    {
      "order": 4,
      "config": {},
      "variation": "cards",
      "component_type": "testimonials"
    },
    {
      "order": 5,
      "config": {},
      "variation": "banner",
      "component_type": "cta"
    },
    {
      "order": 6,
      "config": {},
      "variation": "split-info",
      "component_type": "contact"
    },
    {
      "order": 7,
      "config": {},
      "variation": "simple",
      "component_type": "footer"
    }
  ]
}

CONTENT SCHEMA (Required Fields):
{
  "content_schema": {
    "cta_url": {
      "type": "url",
      "default": "#contact",
      "required": false
    },
    "cta_text": {
      "type": "text",
      "required": true,
      "placeholder": "Join hundreds of satisfied customers"
    },
    "headline": {
      "type": "text",
      "required": true,
      "placeholder": "Capturing Moments, Creating Memories"
    },
    "logo_url": {
      "type": "image",
      "required": true,
      "placeholder": "Logo URL"
    },
    "services": {
      "type": "array",
      "default": [
        {
          "icon": "camera",
          "title": "Wedding Photography",
          "description": "Capturing the magic of your special day."
        },
        {
          "icon": "portrait",
          "title": "Portrait Sessions",
          "description": "Beautiful portraits for individuals and families."
        },
        {
          "icon": "event",
          "title": "Event Photography",
          "description": "Professional coverage for events of all sizes."
        }
      ],
      "required": true,
      "itemSchema": {
        "icon": "string",
        "title": "string",
        "description": "string"
      }
    },
    "cta_title": {
      "type": "text",
      "required": true,
      "placeholder": "Ready to book your session?"
    },
    "nav_items": {
      "type": "array",
      "default": [
        {
          "url": "#home",
          "label": "Home"
        },
        {
          "url": "#portfolio",
          "label": "Portfolio"
        },
        {
          "url": "#about",
          "label": "About"
        },
        {
          "url": "#contact",
          "label": "Contact"
        }
      ],
      "required": true,
      "itemSchema": {
        "url": "string",
        "label": "string"
      }
    },
    "about_text": {
      "type": "text",
      "required": true,
      "placeholder": "Tell your story"
    },
    "hero_image": {
      "type": "image",
      "required": true,
      "placeholder": "Hero image URL"
    },
    "about_image": {
      "type": "image",
      "required": true,
      "placeholder": "About image URL"
    },
    "form_action": {
      "type": "url",
      "default": "/api/contact",
      "required": false
    },
    "subheadline": {
      "type": "text",
      "required": true,
      "placeholder": "Professional Photography Services for Every Occasion"
    },
    "testimonials": {
      "type": "array",
      "default": [
        {
          "quote": "Amazing experience! The photos were stunning.",
          "author_name": "Jane Doe",
          "author_title": "Happy Customer"
        },
        {
          "quote": "Professional and very talented. Highly recommend!",
          "author_name": "John Smith",
          "author_title": "Wedding Planner"
        }
      ],
      "required": true,
      "itemSchema": {
        "quote": "string",
        "author_name": "string",
        "author_title": "string"
      }
    },
    "business_name": {
      "type": "text",
      "required": true,
      "placeholder": "Your Business Name"
    },
    "section_title": {
      "type": "text",
      "default": "Contact Us",
      "required": true
    },
    "business_email": {
      "type": "email",
      "required": true,
      "placeholder": "your@email.com"
    },
    "business_phone": {
      "type": "phone",
      "required": false,
      "placeholder": "+234 xxx xxx xxxx"
    },
    "copyright_text": {
      "type": "text",
      "default": "\u00a9 2025 Your Business. All rights reserved.",
      "required": true
    },
    "hero_image_alt": {
      "type": "text",
      "default": "Photography Hero Image",
      "required": false
    },
    "about_image_alt": {
      "type": "text",
      "default": "About Us Image",
      "required": false
    },
    "cta_button_text": {
      "type": "text",
      "default": "Get Started Today",
      "required": true
    },
    "whatsapp_number": {
      "type": "phone",
      "required": false,
      "placeholder": "234xxxxxxxxxx"
    },
    "submit_button_text": {
      "type": "text",
      "default": "Send Message",
      "required": true
    },
    "section_description": {
      "type": "text",
      "required": false,
      "placeholder": "What we offer"
    }
  }
}

STYLE CONFIGURATION:
{
  "colors": {
    "text": "#1f2937",
    "border": "#e5e7eb",
    "heading": "#111827",
    "primary": "#6366f1",
    "secondary": "#8b5cf6",
    "background": "#ffffff"
  },
  "spacing": {
    "lg": "2rem",
    "md": "1.5rem",
    "sm": "1rem",
    "xl": "3rem",
    "2xl": "5rem",
    "containerMaxWidth": "1200px"
  },
  "typography": {
    "fontSize": "16px",
    "fontFamily": "'Inter', sans-serif",
    "lineHeight": "1.5",
    "headingFontFamily": "'Inter', sans-serif"
  }
}

YOUR RESPONSIBILITIES:

1. **Extract Business Information**:
   - Business name and type
   - Products/services offered
   - Target audience
   - Unique selling propositions
   - Contact information

2. **Generate Content for Each Field**:
   - Fill ALL required fields in the content schema
   - Match the field type (text, array, image, etc.)
   - Use appropriate length for each field (headlines short, descriptions longer)
   - Ensure consistency across all content

3. **Localization for African Market**:
   - Use language that resonates with African audiences
   - Include WhatsApp as primary contact method when applicable
   - Consider mobile-first content (shorter, scannable)
   - Use culturally appropriate examples and references
   - Include local payment methods when relevant

4. **Tone and Style**:
   - Match tone to business type (professional for corporate, friendly for retail)
   - Keep content concise and web-friendly
   - Use action-oriented language
   - Create compelling CTAs

5. **Content Best Practices**:
   - Headlines: 5-10 words, attention-grabbing
   - Subheadlines: 10-20 words, benefit-focused
   - Body text: Clear, scannable, value-driven
   - CTAs: Action verbs, urgency, clear value
   - Lists/Arrays: 3-6 items, parallel structure

6. **Required Content Types**:
   - text: String content (headlines, paragraphs)
   - array: Lists of items (services, features, testimonials)
   - image: Image URLs (use placeholder URLs if not provided)
   - email: Valid email format
   - phone: Local phone format (e.g., +234 for Nigeria)
   - url: Valid URLs (use # for placeholders)

OUTPUT FORMAT (JSON):
{
  "content": {
    "business_name": "The business name",
    "headline": "Compelling headline",
    "subheadline": "Supporting subheadline",
    "services": [
      {
        "title": "Service name",
        "description": "Service description",
        "icon": "icon-name"
      }
    ],
    "business_email": "contact@business.com",
    "business_phone": "+234 XXX XXX XXXX",
    "whatsapp_number": "+234XXXXXXXXXX",
    // ... all other required fields from content_schema
  },
  "metadata": {
    "business_type": "restaurant|consultancy|retail|service|portfolio",
    "tone": "professional|friendly|casual|luxury",
    "target_audience": "Brief description"
  }
}

CRITICAL RULES:
- Generate content in English (can include local language greetings)
- ALL required fields from content_schema MUST be present
- Arrays should have at least the minimum number of items specified
- Phone numbers should use local format
- WhatsApp numbers should be in international format without spaces (+234XXXXXXXXXX)
- Placeholder images should use https://images.unsplash.com/photo-... format
- Keep content authentic and professional
- Avoid generic corporate speak
- Make CTAs specific and actionable

Generate engaging, conversion-focused content that represents the business authentically.
"""

user_prompt_content_generator = """
BUSINESS DESCRIPTION:
A photography business with 15 years of experience

Please generate complete website content based on this business description.
Ensure all required content fields are filled with appropriate, high-quality content.
Make the content specific to this business, not generic templates.
Use appropriate African localization (WhatsApp, local payment methods, cultural references).
"""

content_generator_response_sample = """
{
  "content": {
    "business_name": "Luminous Lens Photography",
    "headline": "Capturing Life's Beautiful Moments",
    "subheadline": "Expert Photography Services Tailored for Every Occasion",
    "services": [
      {
        "title": "Wedding Photography",
        "description": "Let us capture the joy and love of your special day with stunning visuals that you'll cherish forever.",
        "icon": "camera"
      },
      {
        "title": "Portrait Sessions",
        "description": "From solo portraits to family gatherings, we create beautiful images that reflect your unique story.",
        "icon": "portrait"
      },
      {
        "title": "Event Photography",
        "description": "Whether it's a birthday party, corporate event, or cultural celebration, we provide professional coverage that highlights every detail.",
        "icon": "event"
      }
    ],
    "business_email": "info@luminouslens.com",
    "business_phone": "+234 810 123 4567",
    "whatsapp_number": "+2348101234567",
    "cta_title": "Ready to Capture Your Moments?",
    "cta_text": "Join hundreds of satisfied customers who have trusted us with their memories.",
    "cta_button_text": "Get Started Today",
    "hero_image": "https://images.unsplash.com/photo-1506748686214-e9df14d4d9d0",
    "hero_image_alt": "Stunning Wedding Photography",
    "about_text": "At Luminous Lens Photography, we believe that every moment is a story waiting to be told. With over 15 years of experience, we specialize in professional photography that captures the essence of life’s most important events. Our dedicated team understands the local culture and values, ensuring that your photos resonate with authenticity and beauty. We pride ourselves on our personalized approach, working closely with you to understand your vision and deliver results that exceed your expectations.",
    "about_image": "https://images.unsplash.com/photo-1532112013298-6c5d0a6d4d1b",
    "about_image_alt": "About Luminous Lens Photography",
    "testimonials": [
      {
        "quote": "Luminous Lens made our wedding unforgettable! The photos are breathtaking and truly capture the magic of our day.",
        "author_name": "Amara Okafor",
        "author_title": "Bride"
      },
      {
        "quote": "Their professionalism and creativity are unmatched. We received so many compliments on our family portraits!",
        "author_name": "Emeka Nwafor",
        "author_title": "Father"
      }
    ],
    "section_title": "Contact Us",
    "section_description": "We’re here to answer your questions and help you book your next session.",
    "form_action": "/api/contact",
    "copyright_text": "© 2025 Luminous Lens Photography. All rights reserved.",
    "nav_items": [
      {
        "url": "#home",
        "label": "Home"
      },
      {
        "url": "#portfolio",
        "label": "Portfolio"
      },
      {
        "url": "#about",
        "label": "About"
      },
      {
        "url": "#contact",
        "label": "Contact"
      }
    ]
  },
  "metadata": {
    "business_type": "service",
    "tone": "friendly",
    "target_audience": "Couples, Families, and Individuals looking for professional photography services in Nigeria."
  }
}
"""

# # TEMPLATE GENERATION
# from app.services.templates.template_generator import TemplateGenerator
# from app.services.validators.template_validator import validate_template_structure
# from app.services.content_generator import ContentGenerator

# template_generator = TemplateGenerator()
# print("Parsing OpenAI response")
# template_data = template_generator.parse_openai_response(content_template_generator)
# print("Validating template structure")
# is_valid, error_msg = validate_template_structure(template_data)
# if not is_valid:
#     print(f"Template validation failed: {error_msg}")
#     print(f"Invalid template structure: {error_msg}")
# else:
#     print("Template validation passed")
#     # print(f"Template structure: \n{template_data}")




# # CONTENT GENERATION
# print("Generating content")
# content_generator = ContentGenerator()
# content_data = content_generator.parse_openai_response(content_generator_response_sample)
# print("Validating content")
# print(f"{content_data}")
# content_generator.validate_content(content_data, template_data['content_schema'])
# print("Content validated")