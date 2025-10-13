"""
Lucide Icon Validator
Validates and provides safe lucide-react icons to prevent import errors.
"""

from typing import List, Set

# Curated list of verified lucide-react icons (v0.462.0)
# These icons are guaranteed to exist and work
SAFE_LUCIDE_ICONS: Set[str] = {
    # Navigation & Actions
    "ArrowRight",
    "ArrowLeft",
    "ArrowUp",
    "ArrowDown",
    "ChevronRight",
    "ChevronLeft",
    "ChevronDown",
    "ChevronUp",
    "ChevronsRight",
    "ChevronsLeft",
    "Menu",
    "X",
    "Plus",
    "Minus",
    "Check",
    "CheckCircle2",
    "AlertCircle",
    "Info",
    "ExternalLink",
    
    # Communication
    "Mail",
    "Phone",
    "MessageCircle",
    "Send",
    
    # Location & Business
    "MapPin",
    "Globe",
    "Building",
    "Building2",
    "Home",
    "Store",
    
    # People & Social
    "User",
    "Users",
    "UserCircle",
    "UserPlus",
    "Heart",
    "Share2",
    "ThumbsUp",
    
    # Media & Content
    "Image",
    "Video",
    "Camera",
    "FileText",
    "File",
    "Download",
    "Upload",
    "Eye",
    "EyeOff",
    
    # Time & Calendar
    "Calendar",
    "Clock",
    "Timer",
    
    # Interface
    "Search",
    "Filter",
    "Settings",
    "Edit",
    "Trash2",
    "Save",
    "Copy",
    "Star",
    "Bookmark",
    
    # Shopping & Commerce
    "ShoppingCart",
    "ShoppingBag",
    "CreditCard",
    "DollarSign",
    
    # Tech & Development
    "Code",
    "Terminal",
    "Database",
    "Server",
    "Wifi",
    "WifiOff",
    
    # Status & Indicators
    "Loader2",
    "RefreshCw",
    "TrendingUp",
    "TrendingDown",
    "Activity",
    "BarChart",
    "PieChart",
    
    # Documents & Files
    "Folder",
    "FolderOpen",
    "Package",
    "Briefcase",
    
    # Weather & Nature
    "Sun",
    "Moon",
    "Cloud",
    "CloudRain",
    "Zap",
    
    # UI Elements
    "Circle",
    "Square",
    "MoreHorizontal",
    "MoreVertical",
    "Grid",
    "List",
    "Layout",
    "Maximize2",
    "Minimize2",
    "Lock",
    "Unlock",
    
    # Directional
    "MoveRight",
    "MoveLeft",
    "MoveUp",
    "MoveDown",
}

# Icon categories for suggestions
ICON_CATEGORIES = {
    "navigation": ["ArrowRight", "ArrowLeft", "ChevronRight", "ChevronLeft", "Menu", "ExternalLink"],
    "communication": ["Mail", "Phone", "MessageCircle", "Send"],
    "location": ["MapPin", "Globe", "Building", "Building2", "Home", "Store"],
    "people": ["User", "Users", "UserCircle", "UserPlus"],
    "social": ["Heart", "Share2", "ThumbsUp", "Star"],
    "media": ["Image", "Video", "Camera", "FileText"],
    "time": ["Calendar", "Clock", "Timer"],
    "interface": ["Search", "Filter", "Settings", "Edit", "Trash2", "Save"],
    "commerce": ["ShoppingCart", "ShoppingBag", "CreditCard", "DollarSign"],
    "status": ["Check", "CheckCircle2", "AlertCircle", "Info", "Loader2", "RefreshCw"],
}

def is_valid_icon(icon_name: str) -> bool:
    """
    Check if an icon name is valid (exists in lucide-react)
    
    Args:
        icon_name: Name of the icon to validate
        
    Returns:
        True if icon is safe to use, False otherwise
    """
    return icon_name in SAFE_LUCIDE_ICONS

def get_safe_icons() -> List[str]:
    """
    Get list of all safe lucide-react icons
    
    Returns:
        Sorted list of safe icon names
    """
    return sorted(list(SAFE_LUCIDE_ICONS))

def get_icons_by_category(category: str) -> List[str]:
    """
    Get icons for a specific category
    
    Args:
        category: Category name (navigation, communication, etc.)
        
    Returns:
        List of icon names in that category
    """
    return ICON_CATEGORIES.get(category, [])

def suggest_alternative_icon(requested_icon: str) -> str:
    """
    Suggest an alternative icon if the requested one doesn't exist
    
    Args:
        requested_icon: The icon name that was requested
        
    Returns:
        A safe alternative icon name
    """
    # Common icon substitutions
    substitutions = {
        "Handshake": "Users",
        "HandShake": "Users",
        "People": "Users",
        "Person": "User",
        "Location": "MapPin",
        "Place": "MapPin",
        "Email": "Mail",
        "Envelope": "Mail",
        "Telephone": "Phone",
        "Call": "Phone",
        "Message": "MessageCircle",
        "Chat": "MessageCircle",
        "Shop": "Store",
        "Cart": "ShoppingCart",
        "Basket": "ShoppingBag",
        "Like": "ThumbsUp",
        "Love": "Heart",
        "Favorite": "Star",
        "Time": "Clock",
        "Schedule": "Calendar",
        "Date": "Calendar",
        "Picture": "Image",
        "Photo": "Camera",
        "Document": "FileText",
        "Trash": "Trash2",
        "Delete": "Trash2",
        "Remove": "X",
        "Close": "X",
        "Add": "Plus",
        "Checkmark": "Check",
        "Verified": "CheckCircle2",
        "Warning": "AlertCircle",
        "Alert": "AlertCircle",
        "Information": "Info",
        "Help": "Info",
        "Config": "Settings",
        "Configuration": "Settings",
        "Gear": "Settings",
    }
    
    # Check if we have a direct substitution
    if requested_icon in substitutions:
        return substitutions[requested_icon]
    
    # Default fallback
    return "Circle"

def validate_and_fix_icon(icon_name: str) -> tuple[str, bool]:
    """
    Validate an icon and return a safe alternative if needed
    
    Args:
        icon_name: The icon name to validate
        
    Returns:
        Tuple of (safe_icon_name, was_changed)
    """
    if is_valid_icon(icon_name):
        return icon_name, False
    
    alternative = suggest_alternative_icon(icon_name)
    return alternative, True

def format_icons_for_prompt() -> str:
    """
    Format the safe icons list for use in LLM prompts
    
    Returns:
        Formatted string listing all safe icons by category
    """
    output = ["VERIFIED SAFE LUCIDE-REACT ICONS (ONLY USE THESE):\n"]
    
    for category, icons in ICON_CATEGORIES.items():
        output.append(f"\n{category.upper()}:")
        output.append(", ".join(icons))
    
    output.append("\n\nOTHER AVAILABLE ICONS:")
    other_icons = SAFE_LUCIDE_ICONS - set(icon for icons in ICON_CATEGORIES.values() for icon in icons)
    output.append(", ".join(sorted(other_icons)))
    
    return "\n".join(output)


if __name__ == "__main__":
    # Test the validator
    print("=== Lucide Icon Validator Test ===\n")
    
    test_icons = ["ArrowRight", "Handshake", "Heart", "InvalidIcon", "Mail"]
    
    for icon in test_icons:
        is_valid = is_valid_icon(icon)
        fixed_icon, was_changed = validate_and_fix_icon(icon)
        print(f"{icon}: Valid={is_valid}, Fixed={fixed_icon}, Changed={was_changed}")
    
    print(f"\n Total safe icons: {len(SAFE_LUCIDE_ICONS)}")
    print("\nFormatted for prompt:")
    print(format_icons_for_prompt())

