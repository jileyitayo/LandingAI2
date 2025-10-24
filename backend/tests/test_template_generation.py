"""Tests for template generation functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.templates.template_generator import TemplateGenerator, TemplateGenerationError
from app.services.validators.template_validator import (
    validate_template_structure,
    validate_sections_config,
    validate_style_config,
    validate_content_schema,
    validate_content_bindings
)


# ============================================================================
# Template Validator Tests
# ============================================================================

class TestTemplateValidator:
    """Test template validation functions"""
    
    def test_validate_sections_config_valid(self):
        """Test validation of valid sections config"""
        sections = [
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
                "component_type": "footer",
                "variation": "simple",
                "order": 2,
                "config": {}
            }
        ]
        
        is_valid, error = validate_sections_config(sections)
        assert is_valid is True
        assert error is None
    
    def test_validate_sections_config_missing_required(self):
        """Test validation fails when missing required sections"""
        sections = [
            {
                "component_type": "hero",
                "variation": "centered",
                "order": 0,
                "config": {}
            }
        ]
        
        is_valid, error = validate_sections_config(sections)
        assert is_valid is False
        assert "header" in error or "footer" in error
    
    def test_validate_sections_config_invalid_component(self):
        """Test validation fails with invalid component type"""
        sections = [
            {
                "component_type": "invalid_type",
                "variation": "some-variation",
                "order": 0,
                "config": {}
            }
        ]
        
        is_valid, error = validate_sections_config(sections)
        assert is_valid is False
        assert "invalid" in error.lower()
    
    def test_validate_sections_config_empty(self):
        """Test validation fails with empty sections"""
        sections = []
        
        is_valid, error = validate_sections_config(sections)
        assert is_valid is False
        assert "empty" in error.lower()
    
    def test_validate_style_config_valid(self):
        """Test validation of valid style config"""
        style_config = {
            "colors": {
                "primary": "#6366f1",
                "secondary": "#8b5cf6",
                "text": "#1f2937",
                "background": "#ffffff"
            },
            "typography": {
                "fontFamily": "'Inter', sans-serif",
                "fontSize": "16px"
            },
            "spacing": {
                "sm": "1rem",
                "md": "1.5rem",
                "lg": "2rem"
            }
        }
        
        is_valid, error = validate_style_config(style_config)
        assert is_valid is True
        assert error is None
    
    def test_validate_style_config_missing_required_colors(self):
        """Test validation fails when missing required colors"""
        style_config = {
            "colors": {
                "primary": "#6366f1"
                # Missing text and background
            }
        }
        
        is_valid, error = validate_style_config(style_config)
        assert is_valid is False
        assert "color" in error.lower()
    
    def test_validate_style_config_invalid_hex_color(self):
        """Test validation fails with invalid hex color"""
        style_config = {
            "colors": {
                "primary": "not-a-color",
                "text": "#1f2937",
                "background": "#ffffff"
            }
        }
        
        is_valid, error = validate_style_config(style_config)
        assert is_valid is False
        assert "color" in error.lower()
    
    def test_validate_content_schema_valid(self):
        """Test validation of valid content schema"""
        content_schema = {
            "business_name": {
                "type": "text",
                "required": True,
                "placeholder": "Your Business Name"
            },
            "logo_url": {
                "type": "image",
                "required": True
            },
            "services": {
                "type": "array",
                "required": True,
                "itemSchema": {
                    "title": "string",
                    "description": "string"
                }
            }
        }
        
        is_valid, error = validate_content_schema(content_schema)
        assert is_valid is True
        assert error is None
    
    def test_validate_content_schema_empty(self):
        """Test validation fails with empty content schema"""
        content_schema = {}
        
        is_valid, error = validate_content_schema(content_schema)
        assert is_valid is False
        assert "empty" in error.lower()
    
    def test_validate_content_schema_invalid_type(self):
        """Test validation fails with invalid content type"""
        content_schema = {
            "business_name": {
                "type": "invalid_type",
                "required": True
            }
        }
        
        is_valid, error = validate_content_schema(content_schema)
        assert is_valid is False
        assert "type" in error.lower()
    
    def test_validate_template_structure_complete(self):
        """Test validation of complete template structure"""
        template_data = {
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
                    "component_type": "footer",
                    "variation": "simple",
                    "order": 2,
                    "config": {}
                }
            ],
            "style_config": {
                "colors": {
                    "primary": "#6366f1",
                    "text": "#1f2937",
                    "background": "#ffffff"
                }
            },
            "content_schema": {
                "business_name": {
                    "type": "text",
                    "required": True
                },
                "logo_url": {
                    "type": "image",
                    "required": True
                },
                "copyright_text": {
                    "type": "text",
                    "required": True
                }
            }
        }
        
        is_valid, error = validate_template_structure(template_data)
        assert is_valid is True
        assert error is None


# ============================================================================
# Template Generator Tests
# ============================================================================

class TestTemplateGenerator:
    """Test template generator"""
    
    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI API response"""
        return {
            "name": "Modern Restaurant Template",
            "description": "A beautiful template for restaurants",
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
                    "component_type": "footer",
                    "variation": "simple",
                    "order": 3,
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
                    "fontFamily": "'Playfair Display', serif",
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
                    "required": True,
                    "placeholder": "Restaurant Name"
                },
                "logo_url": {
                    "type": "image",
                    "required": True
                },
                "headline": {
                    "type": "text",
                    "required": True
                },
                "subheadline": {
                    "type": "text",
                    "required": True
                },
                "section_title": {
                    "type": "text",
                    "required": True
                },
                "copyright_text": {
                    "type": "text",
                    "required": True
                }
            },
            "meta": {
                "category": "restaurant",
                "tags": ["modern", "warm", "professional"]
            }
        }
    
    @patch('app.services.templates.template_generator.OpenAI')
    def test_generate_template_success(self, mock_openai_class, mock_openai_response):
        """Test successful template generation"""
        # Setup mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = str(mock_openai_response).replace("'", '"')
        
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create generator with mock
        with patch('app.services.templates.template_generator.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            generator = TemplateGenerator()
        
        # Generate template
        prompt = "Create a modern restaurant website with warm colors"
        user_id = "test-user-123"
        
        result = generator.generate_template(prompt, user_id)
        
        # Assertions
        assert result is not None
        assert "sections_config" in result
        assert "style_config" in result
        assert "content_schema" in result
        assert "preview_html" in result
        assert result["created_by"] == user_id
    
    def test_generate_template_no_api_key(self):
        """Test generator initialization fails without API key"""
        with patch('app.services.templates.template_generator.settings') as mock_settings:
            mock_settings.openai_api_key = ""
            
            with pytest.raises(TemplateGenerationError):
                TemplateGenerator()
    
    @patch('app.services.templates.template_generator.OpenAI')
    def test_generate_template_invalid_json(self, mock_openai_class):
        """Test template generation handles invalid JSON response"""
        # Setup mock with invalid JSON
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON {{"
        
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create generator
        with patch('app.services.templates.template_generator.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            generator = TemplateGenerator()
        
        # Test generation
        with pytest.raises(TemplateGenerationError):
            generator.generate_template("test prompt", "user-123")
    
    def test_prepare_component_samples(self):
        """Test preparation of component samples"""
        with patch('app.services.templates.template_generator.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            generator = TemplateGenerator()
        
        samples = generator._prepare_component_samples()
        
        # Check structure
        assert isinstance(samples, dict)
        assert "header" in samples
        assert "hero" in samples
        assert "footer" in samples
        
        # Check header samples
        assert "logo-left" in samples["header"]
        assert "centered-logo" in samples["header"]
    
    def test_build_css_variables(self):
        """Test CSS variables generation"""
        with patch('app.services.templates.template_generator.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            generator = TemplateGenerator()
        
        style_config = {
            "colors": {
                "primary": "#6366f1",
                "text": "#1f2937"
            },
            "typography": {
                "fontFamily": "'Inter', sans-serif"
            }
        }
        
        css_vars = generator._build_css_variables(style_config)
        
        assert "--color-primary: #6366f1" in css_vars
        assert "--color-text: #1f2937" in css_vars
        assert "--font-family: 'Inter', sans-serif" in css_vars


# ============================================================================
# Integration Tests
# ============================================================================

class TestTemplateGenerationIntegration:
    """Integration tests for template generation flow"""
    
    @pytest.mark.asyncio
    @patch('app.services.templates.template_generator.OpenAI')
    async def test_full_generation_flow(self, mock_openai_class):
        """Test complete template generation flow"""
        # This would test the full flow including API endpoint
        # For now, we test the core generation logic
        
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response_data = {
            "name": "Test Template",
            "sections": [
                {"component_type": "header", "variation": "logo-left", "order": 0},
                {"component_type": "hero", "variation": "centered", "order": 1},
                {"component_type": "footer", "variation": "simple", "order": 2}
            ],
            "style_config": {
                "colors": {
                    "primary": "#6366f1",
                    "text": "#1f2937",
                    "background": "#ffffff"
                }
            },
            "content_schema": {
                "business_name": {"type": "text", "required": True},
                "logo_url": {"type": "image", "required": True},
                "copyright_text": {"type": "text", "required": True}
            }
        }
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = str(mock_response_data).replace("'", '"')
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('app.services.templates.template_generator.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            generator = TemplateGenerator()
        
        result = generator.generate_template("test prompt", "user-123")
        
        assert result["sections_config"] is not None
        assert len(result["sections_config"]) == 3
        assert result["style_config"] is not None
        assert result["content_schema"] is not None

