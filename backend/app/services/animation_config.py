"""
Animation Configuration System
Provides animation presets and configurations for different business types.
"""

from typing import Dict, Any, List
from enum import Enum


class AnimationStyle(str, Enum):
    """Animation style categories"""
    QUICK = "quick"  # Fast, snappy (e-commerce, apps)
    SMOOTH = "smooth"  # Smooth, artistic (portfolio, creative)
    SUBTLE = "subtle"  # Minimal, professional (corporate, business)


class AnimationPresets:
    """Animation presets for different business types"""
    
    # Duration configurations by style
    DURATIONS = {
        AnimationStyle.QUICK: {
            "entrance": 0.4,
            "scroll": 0.5,
            "stagger": 0.1,
        },
        AnimationStyle.SMOOTH: {
            "entrance": 0.7,
            "scroll": 0.8,
            "stagger": 0.15,
        },
        AnimationStyle.SUBTLE: {
            "entrance": 0.5,
            "scroll": 0.6,
            "stagger": 0.12,
        },
    }
    
    # Business type to animation style mapping
    BUSINESS_TYPE_STYLES = {
        "e-commerce": AnimationStyle.QUICK,
        "ecommerce": AnimationStyle.QUICK,
        "online store": AnimationStyle.QUICK,
        "shop": AnimationStyle.QUICK,
        "marketplace": AnimationStyle.QUICK,
        
        "portfolio": AnimationStyle.SMOOTH,
        "creative": AnimationStyle.SMOOTH,
        "agency": AnimationStyle.SMOOTH,
        "studio": AnimationStyle.SMOOTH,
        "photography": AnimationStyle.SMOOTH,
        "design": AnimationStyle.SMOOTH,
        "artist": AnimationStyle.SMOOTH,
        
        "corporate": AnimationStyle.SUBTLE,
        "business": AnimationStyle.SUBTLE,
        "consulting": AnimationStyle.SUBTLE,
        "finance": AnimationStyle.SUBTLE,
        "legal": AnimationStyle.SUBTLE,
        "professional": AnimationStyle.SUBTLE,
        "saas": AnimationStyle.SUBTLE,
        "b2b": AnimationStyle.SUBTLE,
    }
    
    @classmethod
    def get_animation_style(cls, business_type: str) -> AnimationStyle:
        """
        Get animation style for a business type.
        
        Args:
            business_type: Business type from analysis
            
        Returns:
            AnimationStyle enum value
        """
        business_type_lower = business_type.lower()
        
        # Check for exact match
        if business_type_lower in cls.BUSINESS_TYPE_STYLES:
            return cls.BUSINESS_TYPE_STYLES[business_type_lower]
        
        # Check for partial match
        for key, style in cls.BUSINESS_TYPE_STYLES.items():
            if key in business_type_lower or business_type_lower in key:
                return style
        
        # Default to subtle for unknown types
        return AnimationStyle.SUBTLE
    
    @classmethod
    def get_durations(cls, business_type: str) -> Dict[str, float]:
        """
        Get animation durations for a business type.
        
        Args:
            business_type: Business type from analysis
            
        Returns:
            Dictionary with entrance, scroll, and stagger durations
        """
        style = cls.get_animation_style(business_type)
        return cls.DURATIONS[style]


def get_animation_config(business_type: str = "business") -> Dict[str, Any]:
    """
    Get complete animation configuration for a business type.
    
    Args:
        business_type: Business type (e.g., "e-commerce", "portfolio", "corporate")
        
    Returns:
        Complete animation configuration dictionary
    """
    durations = AnimationPresets.get_durations(business_type)
    style = AnimationPresets.get_animation_style(business_type)
    
    return {
        "style": style,
        "durations": durations,
        "variants": {
            # Entrance animations (immediate, on mount)
            "fadeIn": {
                "initial": {"opacity": 0, "y": 20},
                "animate": {"opacity": 1, "y": 0},
                "transition": {"duration": durations["entrance"]},
            },
            "slideUp": {
                "initial": {"opacity": 0, "y": 40},
                "animate": {"opacity": 1, "y": 0},
                "transition": {"duration": durations["entrance"], "ease": "easeOut"},
            },
            "slideInFromLeft": {
                "initial": {"opacity": 0, "x": -30},
                "animate": {"opacity": 1, "x": 0},
                "transition": {"duration": durations["entrance"]},
            },
            "slideInFromRight": {
                "initial": {"opacity": 0, "x": 30},
                "animate": {"opacity": 1, "x": 0},
                "transition": {"duration": durations["entrance"]},
            },
            "scaleIn": {
                "initial": {"opacity": 0, "scale": 0.95},
                "animate": {"opacity": 1, "scale": 1},
                "transition": {"duration": durations["entrance"]},
            },
            
            # Scroll animations (triggered on scroll into view)
            "fadeInOnScroll": {
                "initial": {"opacity": 0, "y": 40},
                "whileInView": {"opacity": 1, "y": 0},
                "viewport": {"once": True, "margin": "-100px"},
                "transition": {"duration": durations["scroll"]},
            },
            "scaleOnScroll": {
                "initial": {"opacity": 0, "scale": 0.9},
                "whileInView": {"opacity": 1, "scale": 1},
                "viewport": {"once": True, "margin": "-100px"},
                "transition": {"duration": durations["scroll"]},
            },
            "slideUpOnScroll": {
                "initial": {"opacity": 0, "y": 60},
                "whileInView": {"opacity": 1, "y": 0},
                "viewport": {"once": True, "margin": "-100px"},
                "transition": {"duration": durations["scroll"], "ease": "easeOut"},
            },
        },
        "stagger": {
            "container": {
                "initial": {"opacity": 0},
                "animate": {"opacity": 1},
                "transition": {"staggerChildren": durations["stagger"]},
            },
            "item": {
                "initial": {"opacity": 0, "y": 20},
                "animate": {"opacity": 1, "y": 0},
            },
        },
    }


def get_component_animation_instructions(business_type: str = "business") -> str:
    """
    Get AI prompt instructions for animations based on business type.
    
    Args:
        business_type: Business type from analysis
        
    Returns:
        Formatted instructions for AI to include in component generation
    """
    config = get_animation_config(business_type)
    durations = config["durations"]
    style = config["style"]
    
    return f"""
🎨 ANIMATION INSTRUCTIONS - {style.upper()} STYLE

1. Import Framer Motion:
   ```tsx
   import {{ motion }} from 'framer-motion';
   ```

2. Wrap section root elements with motion components:
   - Use `motion.section`, `motion.div`, `motion.header`, `motion.footer`, etc.
   - Keep all existing className and data attributes

3. Animation Patterns:

   **HERO SECTION (or First section - immediate animation):**
   ```tsx
   <motion.section
     id="hero"
     initial={{{{ opacity: 0, y: 20 }}}}
     animate={{{{ opacity: 1, y: 0 }}}}
     transition={{{{ duration: {durations['entrance']} }}}}
     data-component="Hero"
     data-file="src/components/Hero.tsx"
     className="..."
   >
   ```

   **OTHER SECTIONS (Scroll-triggered):**
   ```tsx
   <motion.section
     id="features"
     initial={{{{ opacity: 0, y: 40 }}}}
     whileInView={{{{ opacity: 1, y: 0 }}}}
     viewport={{{{ once: true, margin: "-100px" }}}}
     transition={{{{ duration: {durations['scroll']} }}}}
     data-component="Features"
     data-file="src/components/Features.tsx"
     className="..."
   >
   ```

   **STAGGERED LISTS/GRIDS:**
   ```tsx
   <motion.div
     initial={{{{ opacity: 0 }}}}
     whileInView={{{{ opacity: 1 }}}}
     viewport={{{{ once: true }}}}
     transition={{{{ staggerChildren: {durations['stagger']} }}}}
   >
     {{items.map((item) => (
       <motion.div
         key={{item.id}}
         initial={{{{ opacity: 0, y: 20 }}}}
         whileInView={{{{ opacity: 1, y: 0 }}}}
         viewport={{{{ once: true }}}}
       >
         {{/* item content */}}
       </motion.div>
     ))}}
   </motion.div>
   ```

4. Animation Rules:
   - Keep animations SUBTLE and PROFESSIONAL
   - Use `viewport={{{{ once: true }}}}` to prevent repeated animations
   - Hero section: Use initial/animate (immediate)
   - All other sections: Use initial/whileInView (scroll-triggered)
   - Add stagger to lists with 3+ items
   - Maintain all data-component and data-file attributes
   - Don't animate UI components (Button, Card, etc.) - only section components

5. Components to Animate:
   ✅ Hero, Features, About, Services, Testimonials, CTA, Contact, Footer
   ❌ Button, Card, Badge, Input (UI components - don't animate)
"""


# Export commonly used functions
__all__ = [
    "AnimationStyle",
    "AnimationPresets",
    "get_animation_config",
    "get_component_animation_instructions",
]

