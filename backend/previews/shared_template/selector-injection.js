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

        // Build selector paths
        const elementPath = buildSelectorPath(element);
        const componentPath = componentRoot !== element ? buildSelectorPath(componentRoot) : elementPath;

        // Get component root position for visual feedback
        const componentRect = componentRoot.getBoundingClientRect();

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
            inlineStyles: {},
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
            attributes: elementDataAttrs,
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

        const element = event.target;
        if (element === overlay || element === tooltip || element === document.body) return;

        // Find the component root to highlight the entire component
        const componentRoot = findComponentRoot(element);
        hoveredElement = componentRoot; // Highlight component, not just element

        createOverlay();
        createTooltip();
        updateOverlay(componentRoot); // Show component boundary
        updateTooltip(componentRoot, event); // Show tooltip with element info
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
    
    // Handle click
    function handleClick(event) {
        if (!selectorEnabled) return;

        event.preventDefault();
        event.stopPropagation();

        const element = event.target;
        if (element === overlay || element === document.body) return;

        const elementData = extractElementData(element);

        // Log selection for debugging
        console.log('Component selected:', {
            component: elementData.component.componentName || 'Unknown',
            file: elementData.component.componentFile || 'Unknown',
            element: elementData.component.elementName || elementData.tagName
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
        
        const element = event.target;
        if (element === overlay || element === document.body) return;
        
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
    
    // Helper: Update Tailwind class for a property
    function updateTailwindClass(element, property, newClass) {
        const classList = element.className.split(' ').filter(c => c.trim());
        
        // Property to class pattern mapping
        const patterns = {
            'textColor': /^text-\w+-\d+$/,
            'backgroundColor': /^bg-\w+-\d+$/,
            'borderColor': /^border-\w+-\d+$/,
            'fontSize': /^text-(xs|sm|base|lg|xl|2xl|3xl|4xl|5xl|6xl|7xl|8xl|9xl)$/,
            'fontWeight': /^font-(thin|extralight|light|normal|medium|semibold|bold|extrabold|black)$/,
            'padding': /^p-\d+(\.\d+)?$/,
            'margin': /^m-\d+(\.\d+)?$/,
        };
        
        const pattern = patterns[property];
        if (pattern) {
            // Remove old classes matching the pattern
            const filtered = classList.filter(c => !pattern.test(c));
            // Add new class
            filtered.push(newClass);
            element.className = filtered.join(' ');
            return true;
        }
        return false;
    }
    
    // Handle instant property updates (optimistic updates)
    function handlePropertyUpdate(data) {
        const { selector, property, value } = data;
        
        // Find element by data-element attribute
        const element = document.querySelector(`[data-element="${selector}"]`);
        if (!element) {
            console.warn('Element not found for optimistic update:', selector);
            return false;
        }
        
        console.log('Applying optimistic update:', { selector, property, value });
        
        try {
            // Handle different property types
            if (property === 'text') {
                // Update text content
                element.textContent = value;
            } else if (property === 'src') {
                // Update image source
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
            } else if (property.startsWith('text') || property.startsWith('bg') || property.startsWith('font') || property.startsWith('padding') || property.startsWith('margin')) {
                // Update Tailwind classes
                updateTailwindClass(element, property, value);
            } else {
                console.warn('Unsupported property for optimistic update:', property);
                return false;
            }
            
            // Visual feedback - flash the element
            const originalOutline = element.style.outline;
            element.style.outline = '2px solid #22c55e';
            setTimeout(() => {
                element.style.outline = originalOutline;
            }, 300);
            
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