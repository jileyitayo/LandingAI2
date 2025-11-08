/**
 * Visual Editor Selector Injection Script
 * Enables point-and-click element selection for visual editing
 */

(function() {
    'use strict';
    
    let selectorEnabled = false;
    let overlay = null;
    let tooltip = null;
    let hoveredElement = null;
    
    // Create overlay for highlighting
    function createOverlay() {
        if (overlay) return overlay;
        
        overlay = document.createElement('div');
        overlay.style.cssText = `
            position: absolute;
            pointer-events: none;
            background: rgba(59, 130, 246, 0.3);
            border: 2px solid #3b82f6;
            border-radius: 4px;
            z-index: 999999;
            transition: all 0.1s ease;
            box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.5);
        `;
        document.body.appendChild(overlay);
        return overlay;
    }
    
    // Create tooltip for showing element info
    function createTooltip() {
        if (tooltip) return tooltip;
        
        tooltip = document.createElement('div');
        tooltip.style.cssText = `
            position: absolute;
            pointer-events: none;
            background: #1f2937;
            color: white;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            z-index: 1000000;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2);
            white-space: nowrap;
            border: 1px solid #3b82f6;
            display: none;
        `;
        document.body.appendChild(tooltip);
        return tooltip;
    }
    
    // Remove overlay
    function removeOverlay() {
        if (overlay) {
            overlay.remove();
            overlay = null;
        }
    }
    
    // Remove tooltip
    function removeTooltip() {
        if (tooltip) {
            tooltip.remove();
            tooltip = null;
        }
    }
    
    // Get element type label for tooltip
    function getElementTypeLabel(element) {
        const tagName = element.tagName.toLowerCase();
        const elementType = element.getAttribute('data-element-type');
        
        // If data-element-type exists, use it
        if (elementType) return elementType;
        
        // Otherwise, infer from tag name
        const typeMap = {
            'h1': 'Heading',
            'h2': 'Heading',
            'h3': 'Heading',
            'h4': 'Heading',
            'h5': 'Heading',
            'h6': 'Heading',
            'p': 'Text',
            'span': 'Text',
            'div': 'Container',
            'section': 'Section',
            'header': 'Header',
            'footer': 'Footer',
            'nav': 'Navigation',
            'button': 'Button',
            'a': 'Link',
            'img': 'Image',
            'input': 'Input',
            'textarea': 'Textarea',
            'select': 'Select',
            'ul': 'List',
            'ol': 'List',
            'li': 'List Item',
        };
        
        return typeMap[tagName] || 'Element';
    }
    
    // Update tooltip content and position
    function updateTooltip(element, event) {
        if (!tooltip || !element) return;
        
        const elementName = element.getAttribute('data-element') || element.tagName.toLowerCase();
        const elementType = getElementTypeLabel(element);
        
        tooltip.innerHTML = `<strong>${elementType}</strong> - Click to edit`;
        tooltip.style.display = 'block';
        
        // Position tooltip above the cursor
        const x = event.clientX + window.scrollX;
        const y = event.clientY + window.scrollY;
        
        tooltip.style.left = (x + 10) + 'px';
        tooltip.style.top = (y - 40) + 'px';
    }
    
    // Hide tooltip
    function hideTooltip() {
        if (tooltip) {
            tooltip.style.display = 'none';
        }
    }
    
    // Get element position and size
    function getElementBounds(element) {
        const rect = element.getBoundingClientRect();
        return {
            top: rect.top + window.scrollY,
            left: rect.left + window.scrollX,
            width: rect.width,
            height: rect.height
        };
    }
    
    // Update overlay position
    function updateOverlay(element) {
        if (!overlay || !element) return;
        
        const bounds = getElementBounds(element);
        overlay.style.top = bounds.top + 'px';
        overlay.style.left = bounds.left + 'px';
        overlay.style.width = bounds.width + 'px';
        overlay.style.height = bounds.height + 'px';
        overlay.style.display = 'block';
    }
    
    // Hide overlay
    function hideOverlay() {
        if (overlay) {
            overlay.style.display = 'none';
        }
    }
    
    // Find the nearest component root (element with data-component or data-file attribute)
    function findComponentRoot(element) {
        let current = element;

        // Traverse up the DOM tree to find the component boundary
        while (current && current !== document.body && current !== document.documentElement) {
            // Check if this element has component markers
            if (current.hasAttribute('data-component') || current.hasAttribute('data-file')) {
                return current;
            }
            current = current.parentElement;
        }

        // If no component root found, return the original element
        return element;
    }

    // Extract all data attributes from an element
    function getDataAttributes(element) {
        const dataAttributes = {};
        for (let i = 0; i < element.attributes.length; i++) {
            const attr = element.attributes[i];
            if (attr.name.startsWith('data-')) {
                dataAttributes[attr.name] = attr.value;
            }
        }
        return dataAttributes;
    }

    // Extract relevant HTML attributes for editing (alt, src, href, etc.)
    function getRelevantAttributes(element) {
        const relevantAttrs = {};
        const tagName = element.tagName.toLowerCase();
        
        // Standard attributes to extract based on element type
        const attributesToExtract = [];
        
        if (tagName === 'img') {
            attributesToExtract.push('src', 'alt', 'width', 'height');
        } else if (tagName === 'a') {
            attributesToExtract.push('href', 'target', 'rel');
        } else if (tagName === 'input' || tagName === 'textarea') {
            attributesToExtract.push('type', 'placeholder', 'value', 'name', 'id');
        } else if (tagName === 'button') {
            attributesToExtract.push('type', 'disabled');
        }
        
        // Extract the relevant attributes
        for (let i = 0; i < element.attributes.length; i++) {
            const attr = element.attributes[i];
            if (attributesToExtract.includes(attr.name)) {
                relevantAttrs[attr.name] = attr.value;
            }
        }
        
        return relevantAttrs;
    }

    // Build DOM path selector
    function buildSelectorPath(element) {
        const path = [];
        let current = element;
        while (current && current !== document.body) {
            let selector = current.tagName.toLowerCase();
            if (current.id) {
                selector += '#' + current.id;
            } else if (current.className) {
                const classes = current.className.split(' ').filter(c => c.trim());
                if (classes.length > 0) {
                    selector += '.' + classes.join('.');
                }
            }
            path.unshift(selector);
            current = current.parentElement;
        }
        return path;
    }

    // Extract element data for editing
    function extractElementData(element) {
        // Find the component root (parent with data-component/data-file)
        const componentRoot = findComponentRoot(element);
        const isComponentRoot = componentRoot === element;

        const computedStyles = window.getComputedStyle(element);
        const rect = element.getBoundingClientRect();

        // Get data attributes from both the element and component root
        const elementDataAttrs = getDataAttributes(element);
        const componentDataAttrs = componentRoot !== element ? getDataAttributes(componentRoot) : elementDataAttrs;
        
        // Get relevant HTML attributes (alt, src, href, etc.) for editing
        const relevantAttrs = getRelevantAttributes(element);
        
        // Merge data attributes with relevant HTML attributes
        const allAttributes = { ...elementDataAttrs, ...relevantAttrs };

        // Build selector paths
        const elementPath = buildSelectorPath(element);
        const componentPath = componentRoot !== element ? buildSelectorPath(componentRoot) : elementPath;

        // Get component root position for visual feedback
        const componentRect = componentRoot.getBoundingClientRect();

        // Parse inline styles from style attribute
        const inlineStyles = {};
        if (element.style) {
            // Parse style attribute string into object
            for (let i = 0; i < element.style.length; i++) {
                const propertyName = element.style[i];
                const propertyValue = element.style.getPropertyValue(propertyName);
                if (propertyValue) {
                    // Convert kebab-case to camelCase (e.g., background-color -> backgroundColor)
                    const camelCaseName = propertyName.replace(/-([a-z])/g, (g) => g[1].toUpperCase());
                    inlineStyles[camelCaseName] = propertyValue;
                }
            }
        }

        return {
            // Clicked element info
            tagName: element.tagName.toLowerCase(),
            selector: elementPath.join(' > '),
            path: elementPath,
            position: {
                top: rect.top + window.scrollY,
                left: rect.left + window.scrollX,
                width: rect.width,
                height: rect.height
            },
            inlineStyles: inlineStyles,
            computedStyles: {
                color: computedStyles.color,
                backgroundColor: computedStyles.backgroundColor,
                fontSize: computedStyles.fontSize,
                fontWeight: computedStyles.fontWeight,
                fontFamily: computedStyles.fontFamily,
                padding: computedStyles.padding,
                margin: computedStyles.margin,
                border: computedStyles.border,
                borderRadius: computedStyles.borderRadius,
                display: computedStyles.display,
                position: computedStyles.position,
                width: computedStyles.width,
                height: computedStyles.height
            },
            classList: Array.from(element.classList),
            textContent: element.textContent?.trim() || '',
            innerHTML: element.innerHTML,
            attributes: allAttributes,
            hasChildren: element.children.length > 0,
            childCount: element.children.length,
            outerHTML: element.outerHTML,

            // Visual editor properties (top-level for convenience)
            elementSelector: elementDataAttrs['data-element'] || null,
            componentFile: componentDataAttrs['data-file'] || null,
            elementType: elementDataAttrs['data-element-type'] || null,

            // Component root info (for reliable identification)
            component: {
                tagName: componentRoot.tagName.toLowerCase(),
                selector: componentPath.join(' > '),
                path: componentPath,
                position: {
                    top: componentRect.top + window.scrollY,
                    left: componentRect.left + window.scrollX,
                    width: componentRect.width,
                    height: componentRect.height
                },
                attributes: componentDataAttrs,
                isRoot: isComponentRoot,
                // Extract component name and file from data attributes
                componentName: componentDataAttrs['data-component'] || null,
                componentFile: componentDataAttrs['data-file'] || null,
                elementName: elementDataAttrs['data-element'] || null
            }
        };
    }
    
    // Handle mouse over
    function handleMouseOver(event) {
        if (!selectorEnabled) return;

        event.preventDefault();
        event.stopPropagation();

        let element = event.target;
        if (element === overlay || element === tooltip || element === document.body) return;

        // Skip locked elements - don't show overlay or tooltip
        if (isElementLocked(element)) {
            hideOverlay();
            hideTooltip();
            return;
        }

        // Find the best selectable element (prioritize images)
        element = findBestSelectableElement(element);
        
        // If element is locked or null, don't show overlay
        if (!element || isElementLocked(element)) {
            hideOverlay();
            hideTooltip();
            return;
        }
        
        hoveredElement = element;

        createOverlay();
        createTooltip();
        updateOverlay(element); // Show element boundary
        updateTooltip(element, event); // Show tooltip with element info
    }
    
    // Handle mouse out
    function handleMouseOut(event) {
        if (!selectorEnabled) return;
        
        // Only hide if we're actually leaving the element
        if (event.relatedTarget && hoveredElement && hoveredElement.contains(event.relatedTarget)) {
            return;
        }
        
        hoveredElement = null;
        hideOverlay();
        hideTooltip();
    }
    
    // Check if an element or any of its parents are locked (uneditable)
    function isElementLocked(element) {
        let current = element;
        while (current && current !== document.body && current !== document.documentElement) {
            // Check if element has data-locked="true" or data-editable-text="false"
            if (current.hasAttribute('data-locked') && current.getAttribute('data-locked') === 'true') {
                return true;
            }
            if (current.hasAttribute('data-editable-text') && current.getAttribute('data-editable-text') === 'false') {
                return true;
            }
            current = current.parentElement;
        }
        return false;
    }

    // Find the best element to select when clicking
    // Prioritizes image elements when there are overlapping elements
    // Skips locked (uneditable) elements
    function findBestSelectableElement(clickedElement) {
        // Check if clicked element or any parent is locked - if so, find parent that's not locked
        if (isElementLocked(clickedElement)) {
            let current = clickedElement.parentElement;
            while (current && current !== document.body) {
                if (!isElementLocked(current)) {
                    clickedElement = current;
                    break;
                }
                current = current.parentElement;
            }
            // If all parents are locked, return null to prevent selection
            if (isElementLocked(clickedElement)) {
                return null;
            }
        }

        // If clicked element is already an image with data-element, use it
        if (clickedElement.tagName.toLowerCase() === 'img' &&
            clickedElement.hasAttribute('data-element') &&
            clickedElement.getAttribute('data-element-type') === 'image') {
            return clickedElement;
        }

        // Check if clicked element is inside an image container
        // Traverse up to find an img element with data-element attribute
        let current = clickedElement;
        let imageElement = null;

        while (current && current !== document.body) {
            // Check if this is an image element with data-element
            if (current.tagName.toLowerCase() === 'img' &&
                current.hasAttribute('data-element') &&
                current.getAttribute('data-element-type') === 'image') {
                imageElement = current;
                break;
            }

            // Also check for data-editable-src attribute (indicates editable image)
            if (current.hasAttribute('data-editable-src') &&
                current.tagName.toLowerCase() === 'img') {
                imageElement = current;
                break;
            }

            // Check sibling elements for images (handles overlay divs on top of images)
            if (current.parentElement) {
                const siblings = Array.from(current.parentElement.children);
                for (let sibling of siblings) {
                    if (sibling.tagName.toLowerCase() === 'img' &&
                        sibling.hasAttribute('data-element') &&
                        sibling.getAttribute('data-element-type') === 'image') {
                        imageElement = sibling;
                        break;
                    }

                    // Also check for data-editable-src
                    if (sibling.tagName.toLowerCase() === 'img' &&
                        sibling.hasAttribute('data-editable-src')) {
                        imageElement = sibling;
                        break;
                    }
                }

                if (imageElement) {
                    break;
                }
            }

            current = current.parentElement;
        }

        // If we found an image element, use it
        if (imageElement) {
            return imageElement;
        }

        // Otherwise, return the clicked element
        return clickedElement;
    }
    
    // Handle click
    function handleClick(event) {
        if (!selectorEnabled) return;

        event.preventDefault();
        event.stopPropagation();

        let element = event.target;
        if (element === overlay || element === document.body) return;

        // Skip locked elements - prevent selection
        if (isElementLocked(element)) {
            return;
        }

        // Find the best selectable element (prioritize images)
        element = findBestSelectableElement(element);

        // If element is locked or null, don't select it
        if (!element || isElementLocked(element)) {
            return;
        }

        const elementData = extractElementData(element);

        // Log selection for debugging
        console.log('Component selected:', {
            component: elementData.component.componentName || 'Unknown',
            file: elementData.component.componentFile || 'Unknown',
            element: elementData.component.elementName || elementData.tagName,
            elementType: elementData.elementType
        });

        // Send data to parent window
        window.parent.postMessage({
            type: 'ELEMENT_SELECTED',
            data: elementData
        }, '*');

        // Visual feedback - green flash to indicate successful selection
        if (overlay) {
            overlay.style.background = 'rgba(34, 197, 94, 0.3)';
            overlay.style.borderColor = '#22c55e';
            overlay.style.boxShadow = '0 0 0 3px rgba(34, 197, 94, 0.5)';
            setTimeout(() => {
                if (overlay) {
                    overlay.style.background = 'rgba(59, 130, 246, 0.3)';
                    overlay.style.borderColor = '#3b82f6';
                    overlay.style.boxShadow = '0 0 0 1px rgba(59, 130, 246, 0.5)';
                }
            }, 500);
        }
    }
    
    // Handle right click
    function handleRightClick(event) {
        if (!selectorEnabled) return;
        
        event.preventDefault();
        event.stopPropagation();
        
        let element = event.target;
        if (element === overlay || element === document.body) return;

        // Find the best selectable element (prioritize images)
        element = findBestSelectableElement(element);
        
        const elementData = extractElementData(element);
        
        // Send data to parent window
        window.parent.postMessage({
            type: 'ELEMENT_RIGHT_CLICKED',
            data: elementData,
            x: event.clientX,
            y: event.clientY
        }, '*');
    }
    
    // Enable selector
    function enableSelector() {
        selectorEnabled = true;
        document.body.style.cursor = 'crosshair';
        
        // Add event listeners
        document.addEventListener('mouseover', handleMouseOver, true);
        document.addEventListener('mouseout', handleMouseOut, true);
        document.addEventListener('click', handleClick, true);
        document.addEventListener('contextmenu', handleRightClick, true);
        
        // Create overlay and tooltip
        createOverlay();
        createTooltip();
    }
    
    // Disable selector
    function disableSelector() {
        selectorEnabled = false;
        document.body.style.cursor = '';
        
        // Remove event listeners
        document.removeEventListener('mouseover', handleMouseOver, true);
        document.removeEventListener('mouseout', handleMouseOut, true);
        document.removeEventListener('click', handleClick, true);
        document.removeEventListener('contextmenu', handleRightClick, true);
        
        // Remove overlay and tooltip
        removeOverlay();
        removeTooltip();
        hoveredElement = null;
    }
    
    // Tailwind color values map - for inline style application
    const TAILWIND_COLOR_MAP = {
        slate: { '50': '#f8fafc', '100': '#f1f5f9', '200': '#e2e8f0', '300': '#cbd5e1', '400': '#94a3b8', '500': '#64748b', '600': '#475569', '700': '#334155', '800': '#1e293b', '900': '#0f172a', '950': '#020617' },
        gray: { '50': '#f9fafb', '100': '#f3f4f6', '200': '#e5e7eb', '300': '#d1d5db', '400': '#9ca3af', '500': '#6b7280', '600': '#4b5563', '700': '#374151', '800': '#1f2937', '900': '#111827', '950': '#030712' },
        zinc: { '50': '#fafafa', '100': '#f4f4f5', '200': '#e4e4e7', '300': '#d4d4d8', '400': '#a1a1aa', '500': '#71717a', '600': '#52525b', '700': '#3f3f46', '800': '#27272a', '900': '#18181b', '950': '#09090b' },
        neutral: { '50': '#fafafa', '100': '#f5f5f5', '200': '#e5e5e5', '300': '#d4d4d4', '400': '#a3a3a3', '500': '#737373', '600': '#525252', '700': '#404040', '800': '#262626', '900': '#171717', '950': '#0a0a0a' },
        stone: { '50': '#fafaf9', '100': '#f5f5f4', '200': '#e7e5e4', '300': '#d6d3d1', '400': '#a8a29e', '500': '#78716c', '600': '#57534e', '700': '#44403c', '800': '#292524', '900': '#1c1917', '950': '#0c0a09' },
        red: { '50': '#fef2f2', '100': '#fee2e2', '200': '#fecaca', '300': '#fca5a5', '400': '#f87171', '500': '#ef4444', '600': '#dc2626', '700': '#b91c1c', '800': '#991b1b', '900': '#7f1d1d', '950': '#450a0a' },
        orange: { '50': '#fff7ed', '100': '#ffedd5', '200': '#fed7aa', '300': '#fdba74', '400': '#fb923c', '500': '#f97316', '600': '#ea580c', '700': '#c2410c', '800': '#9a3412', '900': '#7c2d12', '950': '#431407' },
        amber: { '50': '#fffbeb', '100': '#fef3c7', '200': '#fde68a', '300': '#fcd34d', '400': '#fbbf24', '500': '#f59e0b', '600': '#d97706', '700': '#b45309', '800': '#92400e', '900': '#78350f', '950': '#451a03' },
        yellow: { '50': '#fefce8', '100': '#fef9c3', '200': '#fef08a', '300': '#fde047', '400': '#facc15', '500': '#eab308', '600': '#ca8a04', '700': '#a16207', '800': '#854d0e', '900': '#713f12', '950': '#422006' },
        lime: { '50': '#f7fee7', '100': '#ecfccb', '200': '#d9f99d', '300': '#bef264', '400': '#a3e635', '500': '#84cc16', '600': '#65a30d', '700': '#4d7c0f', '800': '#365314', '900': '#1a2e05', '950': '#0f1a03' },
        green: { '50': '#f0fdf4', '100': '#dcfce7', '200': '#bbf7d0', '300': '#86efac', '400': '#4ade80', '500': '#22c55e', '600': '#16a34a', '700': '#15803d', '800': '#166534', '900': '#14532d', '950': '#052e16' },
        emerald: { '50': '#ecfdf5', '100': '#d1fae5', '200': '#a7f3d0', '300': '#6ee7b7', '400': '#34d399', '500': '#10b981', '600': '#059669', '700': '#047857', '800': '#065f46', '900': '#064e3b', '950': '#022c22' },
        teal: { '50': '#f0fdfa', '100': '#ccfbf1', '200': '#99f6e4', '300': '#5eead4', '400': '#2dd4bf', '500': '#14b8a6', '600': '#0d9488', '700': '#0f766e', '800': '#115e59', '900': '#134e4a', '950': '#042f2e' },
        cyan: { '50': '#ecfeff', '100': '#cffafe', '200': '#a5f3fc', '300': '#67e8f9', '400': '#22d3ee', '500': '#06b6d4', '600': '#0891b2', '700': '#0e7490', '800': '#155e75', '900': '#164e63', '950': '#083344' },
        sky: { '50': '#f0f9ff', '100': '#e0f2fe', '200': '#bae6fd', '300': '#7dd3fc', '400': '#38bdf8', '500': '#0ea5e9', '600': '#0284c7', '700': '#0369a1', '800': '#075985', '900': '#0c4a6e', '950': '#082f49' },
        blue: { '50': '#eff6ff', '100': '#dbeafe', '200': '#bfdbfe', '300': '#93c5fd', '400': '#60a5fa', '500': '#3b82f6', '600': '#2563eb', '700': '#1d4ed8', '800': '#1e40af', '900': '#1e3a8a', '950': '#172554' },
        indigo: { '50': '#eef2ff', '100': '#e0e7ff', '200': '#c7d2fe', '300': '#a5b4fc', '400': '#818cf8', '500': '#6366f1', '600': '#4f46e5', '700': '#4338ca', '800': '#3730a3', '900': '#312e81', '950': '#1e1b4b' },
        violet: { '50': '#f5f3ff', '100': '#ede9fe', '200': '#ddd6fe', '300': '#c4b5fd', '400': '#a78bfa', '500': '#8b5cf6', '600': '#7c3aed', '700': '#6d28d9', '800': '#5b21b6', '900': '#4c1d95', '950': '#2e1065' },
        purple: { '50': '#faf5ff', '100': '#f3e8ff', '200': '#e9d5ff', '300': '#d8b4fe', '400': '#c084fc', '500': '#a855f7', '600': '#9333ea', '700': '#7e22ce', '800': '#6b21a8', '900': '#581c87', '950': '#3b0764' },
        fuchsia: { '50': '#fdf4ff', '100': '#fae8ff', '200': '#f5d0fe', '300': '#f0abfc', '400': '#e879f9', '500': '#d946ef', '600': '#c026d3', '700': '#a21caf', '800': '#86198f', '900': '#701a75', '950': '#4a044e' },
        pink: { '50': '#fdf2f8', '100': '#fce7f3', '200': '#fbcfe8', '300': '#f9a8d4', '400': '#f472b6', '500': '#ec4899', '600': '#db2777', '700': '#be185d', '800': '#9f1239', '900': '#831843', '950': '#500724' },
        rose: { '50': '#fff1f2', '100': '#ffe4e6', '200': '#fecdd3', '300': '#fda4af', '400': '#fb7185', '500': '#f43f5e', '600': '#e11d48', '700': '#be123c', '800': '#9f1239', '900': '#881337', '950': '#4c0519' }
    };
    
    // Helper: Get hex color from Tailwind class
    function getHexFromTailwindClass(colorClass) {
        const match = colorClass.match(/^(text|bg|border)-(\w+)-(\d+)$/);
        if (match) {
            const [, prefix, color, shade] = match;
            return TAILWIND_COLOR_MAP[color]?.[shade];
        }
        return null;
    }
    
    // Helper: Update Tailwind class for a property
    function updateTailwindClass(element, property, newClass) {
        const classList = element.className.split(' ').filter(c => c.trim());
        console.log('🎨 Updating Tailwind class:', { property, newClass, currentClasses: classList });
        
        // For color properties, use inline styles instead of classes for guaranteed rendering
        if (property === 'color' || property === 'textColor') {
            // Check if it's a direct hex color
            if (newClass.match(/^#[0-9A-Fa-f]{6}$/)) {
                element.style.color = newClass;
                console.log('✅ Applied custom hex color via inline style:', newClass);
                // Remove any Tailwind color classes
                const pattern = /^text-\w+-\d+$/;
                const filtered = classList.filter(c => !pattern.test(c));
                element.className = filtered.join(' ');
                return true;
            }
            // Otherwise, try to get hex from Tailwind class
            const hexColor = getHexFromTailwindClass(newClass);
            if (hexColor) {
                element.style.color = hexColor;
                console.log('✅ Applied color via inline style:', hexColor);
                // Also update the class for consistency
                const pattern = /^text-\w+-\d+$/;
                const filtered = classList.filter(c => !pattern.test(c));
                filtered.push(newClass);
                element.className = filtered.join(' ');
                return true;
            }
        } else if (property === 'backgroundColor') {
            // Check if it's a direct hex color
            if (newClass.match(/^#[0-9A-Fa-f]{6}$/)) {
                element.style.backgroundColor = newClass;
                console.log('✅ Applied custom hex backgroundColor via inline style:', newClass);
                // Remove any Tailwind color classes
                const pattern = /^bg-\w+-\d+$/;
                const filtered = classList.filter(c => !pattern.test(c));
                element.className = filtered.join(' ');
                return true;
            }
            // Otherwise, try to get hex from Tailwind class
            const hexColor = getHexFromTailwindClass(newClass);
            if (hexColor) {
                element.style.backgroundColor = hexColor;
                console.log('✅ Applied backgroundColor via inline style:', hexColor);
                // Also update the class for consistency
                const pattern = /^bg-\w+-\d+$/;
                const filtered = classList.filter(c => !pattern.test(c));
                filtered.push(newClass);
                element.className = filtered.join(' ');
                return true;
            }
        } else if (property === 'borderColor') {
            // Check if it's a direct hex color
            if (newClass.match(/^#[0-9A-Fa-f]{6}$/)) {
                element.style.borderColor = newClass;
                console.log('✅ Applied custom hex borderColor via inline style:', newClass);
                // Remove any Tailwind color classes
                const pattern = /^border-\w+-\d+$/;
                const filtered = classList.filter(c => !pattern.test(c));
                element.className = filtered.join(' ');
                return true;
            }
            // Otherwise, try to get hex from Tailwind class
            const hexColor = getHexFromTailwindClass(newClass);
            if (hexColor) {
                element.style.borderColor = hexColor;
                console.log('✅ Applied borderColor via inline style:', hexColor);
                // Also update the class for consistency
                const pattern = /^border-\w+-\d+$/;
                const filtered = classList.filter(c => !pattern.test(c));
                filtered.push(newClass);
                element.className = filtered.join(' ');
                return true;
            }
        }
        
        // For non-color properties, use the original class-based approach
        const patterns = {
            'fontSize': /^text-(xs|sm|base|lg|xl|2xl|3xl|4xl|5xl|6xl|7xl|8xl|9xl)$/,
            'fontWeight': /^font-(thin|extralight|light|normal|medium|semibold|bold|extrabold|black)$/,
            'fontFamily': /^font-(sans|serif|mono)$/,
            'textAlign': /^text-(left|center|right|justify)$/,
            'textTransform': /^(normal-case|uppercase|lowercase|capitalize)$/,
            'padding': /^p-\d+(\.\d+)?$/,
            'margin': /^m-\d+(\.\d+)?$/,
        };
        
        const pattern = patterns[property];
        if (pattern) {
            // Remove old classes matching the pattern
            const oldClasses = classList.filter(c => pattern.test(c));
            const filtered = classList.filter(c => !pattern.test(c));
            // Add new class
            filtered.push(newClass);
            element.className = filtered.join(' ');
            console.log('✅ Class updated:', { 
                removed: oldClasses, 
                added: newClass, 
                newClassName: element.className 
            });
            return true;
        }
        console.warn('⚠️ No pattern found for property:', property);
        return false;
    }
    
    // Handle instant property updates (optimistic updates)
    function handlePropertyUpdate(data) {
        const { selector, property, value } = data;
        
        console.log('📨 Received property update:', { selector, property, value });
        
        // Find element by data-element attribute
        const element = document.querySelector(`[data-element="${selector}"]`);
        if (!element) {
            console.warn('❌ Element not found for optimistic update:', selector);
            return false;
        }
        
        console.log('✅ Found element, applying update:', { selector, property, value, element });
        
        try {
            // Handle different property types
            if (property === 'text') {
                // Update text content
                element.textContent = value;
            } else if (property === 'src' || property === 'imageUrl') {
                // Update image source (support both 'src' and 'imageUrl' property names)
                if (element.tagName === 'IMG') {
                    element.src = value;
                }
            } else if (property === 'href') {
                // Update link href
                if (element.tagName === 'A') {
                    element.href = value;
                }
            } else if (property === 'alt') {
                // Update alt text
                if (element.tagName === 'IMG') {
                    element.alt = value;
                }
            } else if (
                property === 'color' || 
                property === 'backgroundColor' || 
                property === 'borderColor' ||
                property === 'fontSize' ||
                property === 'fontWeight' ||
                property === 'fontFamily' ||
                property === 'textAlign' ||
                property === 'textTransform' ||
                property.startsWith('text') || 
                property.startsWith('bg') || 
                property.startsWith('border') ||
                property.startsWith('font') || 
                property.startsWith('padding') || 
                property.startsWith('margin')
            ) {
                // Update Tailwind classes
                const updateSuccess = updateTailwindClass(element, property, value);
                if (updateSuccess) {
                    console.log('✨ Tailwind class updated successfully');
                } else {
                    console.warn('⚠️ Tailwind class update failed');
                }
            } else {
                console.warn('❌ Unsupported property for optimistic update:', property);
                return false;
            }
            
            // Visual feedback - flash the element with a green outline
            const originalOutline = element.style.outline;
            const originalOutlineOffset = element.style.outlineOffset;
            element.style.outline = '2px solid #22c55e';
            element.style.outlineOffset = '2px';
            setTimeout(() => {
                element.style.outline = originalOutline;
                element.style.outlineOffset = originalOutlineOffset;
            }, 400);
            
            console.log('✅ Optimistic update completed');
            return true;
        } catch (error) {
            console.error('Error applying optimistic update:', error);
            return false;
        }
    }
    
    // Listen for messages from parent
    window.addEventListener('message', function(event) {
        if (event.data.type === 'ENABLE_SELECTOR') {
            enableSelector();
        } else if (event.data.type === 'DISABLE_SELECTOR') {
            disableSelector();
        } else if (event.data.type === 'UPDATE_PROPERTY') {
            // Handle instant property update (optimistic UI)
            const success = handlePropertyUpdate(event.data);
            // Notify parent of update result
            window.parent.postMessage({
                type: 'PROPERTY_UPDATE_RESULT',
                success: success,
                selector: event.data.selector,
                property: event.data.property
            }, '*');
        }
    });
    
    // Send ready signal
    window.parent.postMessage({
        type: 'SELECTOR_READY'
    }, '*');
    
    // Handle page visibility changes (only disable when user switches browser tabs)
    document.addEventListener('visibilitychange', function() {
        if (document.hidden && selectorEnabled) {
            // Only disable if the document is truly hidden (user switched tabs)
            // Don't disable just because the iframe lost focus
            console.log('Document hidden - keeping selector enabled');
            // Note: We keep selector enabled so it's ready when user comes back
            // The parent component controls the selector state via messages
        }
    });
    
    // Note: We removed the blur event handler because it was too aggressive
    // It was disabling the selector whenever the iframe lost focus (e.g., clicking outside)
    // Now the parent component fully controls the selector state via postMessage
    
    console.log('Visual Editor Selector loaded and ready');
})();