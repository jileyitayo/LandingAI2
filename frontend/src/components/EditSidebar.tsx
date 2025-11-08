'use client';

import { useState, useEffect } from 'react';
import { X, ChevronDown, ChevronRight, Info, Palette, Type, Link as LinkIcon, Eye } from 'lucide-react';
import { SelectedElement } from '@/types/chat.types';
import { PageInfo, PropertyType, EditableElement } from '@/types/property-edit.types';
import TextEditor from './property-editors/TextEditor';
import ColorEditor from './property-editors/ColorEditor';
import FontEditor from './property-editors/FontEditor';
import ImageEditor from './property-editors/ImageEditor';
import LinkEditor from './property-editors/LinkEditor';

interface EditSidebarProps {
  selectedElement: SelectedElement | null;
  pageInfo: PageInfo;
  onClearSelection: () => void;
  onPropertyChange: (property: PropertyType, value: string | number | boolean) => void;
  isAutoSaving: boolean;
  // Optional: Project files for route suggestions in LinkEditor
  projectFiles?: Record<string, string>;
}

type PropertySection = 'content' | 'colors' | 'typography' | 'link' | 'image';

export default function EditSidebar({
  selectedElement,
  pageInfo,
  onClearSelection,
  onPropertyChange,
  isAutoSaving,
  projectFiles,
}: EditSidebarProps) {
  const [expandedSections, setExpandedSections] = useState<Set<PropertySection>>(
    new Set(['content', 'colors', 'typography'])
  );
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
  const [lastSavedProperty, setLastSavedProperty] = useState<string | null>(null);

  // Update save status based on isAutoSaving
  useEffect(() => {
    if (isAutoSaving) {
      setSaveStatus('saving');
    } else if (saveStatus === 'saving') {
      setSaveStatus('success');
      // Reset to idle after 2 seconds
      const timer = setTimeout(() => setSaveStatus('idle'), 2000);
      return () => clearTimeout(timer);
    }
  }, [isAutoSaving]);

  // Auto-expand/collapse sections based on selected element type
  useEffect(() => {
    if (!selectedElement) {
      // Reset to default when no element is selected
      setExpandedSections(new Set(['content', 'colors', 'typography']));
      return;
    }

    const tagName = selectedElement.tagName?.toLowerCase();
    const hasTextContent = Boolean(selectedElement.textContent && selectedElement.textContent.trim());
    
    // Text-containing elements (headings, paragraphs, spans, divs, etc.)
    const textElementTags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div', 'li', 'td', 'th', 'label', 'button'];
    
    // Determine which section should be expanded based on element type
    let sectionToExpand: PropertySection | null = null;

    // Image elements - expand image section and collapse others
    if (tagName === 'img') {
      sectionToExpand = 'image';
    }
    // Text elements - expand content section and collapse others
    // Check if it's a text element tag or has text content (excluding images, links, and self-closing tags)
    else if (
      (textElementTags.includes(tagName || '') || hasTextContent) &&
      tagName !== 'img' &&
      tagName !== 'a' &&
      !['hr', 'br', 'video', 'iframe', 'svg', 'input', 'textarea', 'select'].includes(tagName || '')
    ) {
      sectionToExpand = 'content';
    }
    // Link elements - expand link section
    else if (tagName === 'a') {
      sectionToExpand = 'link';
    }

    // If we have a section to expand, expand only that section and collapse others
    if (sectionToExpand) {
      setExpandedSections(new Set([sectionToExpand]));
    }
  }, [selectedElement]);

  // Wrap property change handler to track what's being saved
  const handlePropertyChange = (property: PropertyType, value: string | number | boolean) => {
    setLastSavedProperty(property);
    onPropertyChange(property, value);
  };

  const toggleSection = (section: PropertySection) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(section)) {
        newSet.delete(section);
      } else {
        newSet.add(section);
      }
      return newSet;
    });
  };

  const renderPageInfo = () => (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      <div className="flex items-center gap-2 text-gray-300 mb-4">
        <Info className="w-5 h-5" />
        <h2 className="text-lg font-semibold">Page Information</h2>
      </div>

      {/* Project Title */}
      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <div className="text-xs text-gray-400 mb-1">Title</div>
        <div className="text-white font-medium">{pageInfo.title || 'Untitled Page'}</div>
      </div>

      {/* Description */}
      {pageInfo.description && (
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <div className="text-xs text-gray-400 mb-1">Description</div>
          <div className="text-gray-300 text-sm">{pageInfo.description}</div>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <div className="text-xs text-gray-400 mb-1">Components</div>
          <div className="text-2xl font-bold text-blue-400">{pageInfo.componentCount}</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <div className="text-xs text-gray-400 mb-1">Elements</div>
          <div className="text-2xl font-bold text-green-400">{pageInfo.elementCount}</div>
        </div>
      </div>

      {/* Design Tokens */}
      {pageInfo.designTokens && (
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <div className="text-sm font-medium text-gray-300 mb-3">Design System</div>
          
          {/* Colors */}
          {pageInfo.designTokens.colors && Object.keys(pageInfo.designTokens.colors).length > 0 && (
            <div className="mb-3">
              <div className="text-xs text-gray-400 mb-2">Colors</div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(pageInfo.designTokens.colors).map(([name, color]) => (
                  color && (
                    <div key={name} className="flex items-center gap-1">
                      <div
                        className="w-6 h-6 rounded border border-gray-600"
                        style={{ backgroundColor: color }}
                        title={`${name}: ${color}`}
                      />
                    </div>
                  )
                ))}
              </div>
            </div>
          )}

          {/* Fonts */}
          {pageInfo.designTokens.fonts && Object.keys(pageInfo.designTokens.fonts).length > 0 && (
            <div>
              <div className="text-xs text-gray-400 mb-2">Fonts</div>
              <div className="space-y-1">
                {Object.entries(pageInfo.designTokens.fonts).map(([name, font]) => (
                  font && (
                    <div key={name} className="text-xs text-gray-300">
                      <span className="text-gray-500">{name}:</span> {font}
                    </div>
                  )
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Instructions */}
      <div className="bg-blue-900/20 border border-blue-700/50 rounded-lg p-4">
        <div className="text-sm text-blue-300">
          <div className="font-medium mb-2">💡 Getting Started</div>
          <div className="text-xs text-blue-200 space-y-1">
            <p>• Click any element in the preview to edit it</p>
            <p>• Hover to see element highlights</p>
            <p>• Changes save automatically</p>
          </div>
        </div>
      </div>
    </div>
  );

  const renderPropertySection = (
    section: PropertySection,
    icon: React.ReactNode,
    title: string,
    content: React.ReactNode
  ) => {
    const isExpanded = expandedSections.has(section);

    return (
      <div className="border-b border-gray-700">
        <button
          onClick={() => toggleSection(section)}
          className="w-full flex items-center justify-between p-3 hover:bg-gray-800/50 transition-colors"
        >
          <div className="flex items-center gap-2">
            {icon}
            <span className="text-sm font-medium text-gray-300">{title}</span>
          </div>
          {isExpanded ? (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronRight className="w-4 h-4 text-gray-400" />
          )}
        </button>
        {isExpanded && <div className="p-3 bg-gray-800/30">{content}</div>}
      </div>
    );
  };

  // Helper function to determine which sections to show based on element type
  const getVisibleSections = (element: SelectedElement) => {
    const tagName = element.tagName?.toLowerCase();
    const hasTextContent = Boolean(element.textContent && element.textContent.trim());
    
    // Define which sections are visible for each element type
    const sections = {
      content: true,
      colors: true,
      typography: true,
      image: false,
      link: false,
    };

    // Image elements - only show image section, hide all others
    if (tagName === 'img') {
      sections.image = true;
      sections.content = false;
      sections.colors = false;
      sections.typography = false;
      sections.link = false;
    }
    
    // Link elements
    if (tagName === 'a') {
      sections.link = true;
    }

    // Input/textarea elements
    if (tagName === 'input' || tagName === 'textarea' || tagName === 'select') {
      sections.typography = true;
      sections.content = false; // Use value instead
    }

    // Button elements
    if (tagName === 'button') {
      sections.content = hasTextContent;
      sections.typography = hasTextContent;
    }

    // Self-closing or non-text elements
    if (['hr', 'br', 'video', 'iframe', 'svg'].includes(tagName || '')) {
      sections.content = false;
      sections.typography = false;
    }

    return sections;
  };

  const renderElementEditor = () => {
    if (!selectedElement) return null;

    const elementType = selectedElement.component?.elementName || selectedElement.tagName;
    const componentName = selectedElement.component?.componentName;
    const visibleSections = getVisibleSections(selectedElement);

    return (
      <div className="flex-1 overflow-y-auto">
        {/* Header with element info */}
        <div className="p-4 bg-gradient-to-br from-blue-900/40 to-purple-900/40 border-b border-gray-700">
          <div className="flex items-start justify-between mb-2">
            <div>
              <div className="text-xs text-blue-300 font-medium mb-1">
                {selectedElement.component?.componentName || 'ELEMENT'}
              </div>
              <div className="text-lg font-bold text-white">
                {elementType}
              </div>
              {componentName && (
                <div className="text-xs text-gray-400 mt-1">
                  in {componentName}
                </div>
              )}
            </div>
            <button
              onClick={onClearSelection}
              className="text-gray-400 hover:text-white transition-colors"
              title="Clear selection"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          {selectedElement.textContent && (
            <div className="text-xs text-gray-300 mt-3 p-2 bg-gray-900/50 rounded border border-gray-700">
              <div className="text-gray-500 mb-1">Current text:</div>
              <div className="truncate">{selectedElement.textContent}</div>
            </div>
          )}
        </div>

        {/* Property Sections */}
        <div className="divide-y divide-gray-700">
          {/* Image Section - Show first for image elements */}
          {visibleSections.image && renderPropertySection(
            'image',
            <Eye className="w-4 h-4 text-teal-400" />,
            'Image',
            <ImageEditor
              imageUrl={selectedElement?.attributes?.src || ''}
              imageAlt={selectedElement?.attributes?.alt || ''}
              imageFit={selectedElement?.classList.find(c => c.startsWith('object-')) || 'object-cover'}
              onImageUrlChange={(value) => handlePropertyChange('imageUrl', value)}
              onImageAltChange={(value) => handlePropertyChange('imageAlt', value)}
              onImageFitChange={(value) => handlePropertyChange('imageFit', value)}
            />
          )}

          {/* Link Section - Show first for link elements */}
          {visibleSections.link && renderPropertySection(
            'link',
            <LinkIcon className="w-4 h-4 text-blue-400" />,
            'Link',
            <LinkEditor
              href={selectedElement?.attributes?.href || ''}
              target={selectedElement?.attributes?.target || '_self'}
              rel={selectedElement?.attributes?.rel || ''}
              onHrefChange={(value) => handlePropertyChange('linkHref', value)}
              onTargetChange={(value) => handlePropertyChange('linkTarget', value)}
              onRelChange={(value) => handlePropertyChange('linkRel', value)}
              projectFiles={projectFiles}
            />
          )}

          {/* Content Section */}
          {visibleSections.content && renderPropertySection(
            'content',
            <Type className="w-4 h-4 text-blue-400" />,
            'Content',
            <TextEditor
              value={selectedElement?.textContent || ''}
              onChange={(value) => handlePropertyChange('text', value)}
              placeholder="Enter text content..."
              autoSave={true}
            />
          )}

          {/* Colors Section */}
          {visibleSections.colors && renderPropertySection(
            'colors',
            <Palette className="w-4 h-4 text-pink-400" />,
            'Colors',
            <div className="space-y-4">
              <ColorEditor
                label="Text Color"
                value={
                  // Check for custom hex color from inline styles first
                  (selectedElement?.inlineStyles?.color && 
                   selectedElement.inlineStyles.color.startsWith('#') && 
                   selectedElement.inlineStyles.color) ||
                  // Then check for Tailwind class
                  selectedElement?.classList.find(c => /^text-\w+-\d+$/.test(c)) || 
                  'text-gray-900'
                }
                onChange={(value) => handlePropertyChange('color', value)}
                type="text"
                autoSave={true}
              />
              <ColorEditor
                label="Background"
                value={
                  // Check for custom hex color from inline styles first
                  (selectedElement?.inlineStyles?.backgroundColor && 
                   selectedElement.inlineStyles.backgroundColor.startsWith('#') && 
                   selectedElement.inlineStyles.backgroundColor) ||
                  // Then check for Tailwind class
                  selectedElement?.classList.find(c => /^bg-(\w+-\d+|transparent|white|black)$/.test(c)) || 
                  'bg-transparent'
                }
                onChange={(value) => handlePropertyChange('backgroundColor', value)}
                type="background"
                autoSave={true}
              />
              <ColorEditor
                label="Border Color"
                value={
                  // Check for custom hex color from inline styles first
                  (selectedElement?.inlineStyles?.borderColor && 
                   selectedElement.inlineStyles.borderColor.startsWith('#') && 
                   selectedElement.inlineStyles.borderColor) ||
                  // Then check for Tailwind class
                  selectedElement?.classList.find(c => /^border-\w+-\d+$/.test(c)) || 
                  'border-gray-300'
                }
                onChange={(value) => handlePropertyChange('borderColor', value)}
                type="border"
                autoSave={true}
              />
            </div>
          )}

          {/* Typography Section */}
          {visibleSections.typography && renderPropertySection(
            'typography',
            <Type className="w-4 h-4 text-purple-400" />,
            'Typography',
            <FontEditor
              fontSize={selectedElement?.classList.find(c => c.startsWith('text-') && (c.includes('xl') || c.includes('lg') || c.includes('sm') || c.includes('xs') || c === 'text-base')) || 'text-base'}
              fontWeight={selectedElement?.classList.find(c => c.startsWith('font-')) || 'font-normal'}
              fontFamily={selectedElement?.classList.find(c => c.startsWith('font-')) || 'font-sans'}
              textAlign={selectedElement?.classList.find(c => ['text-left', 'text-center', 'text-right', 'text-justify'].includes(c)) || 'text-left'}
              textTransform={selectedElement?.classList.find(c => ['uppercase', 'lowercase', 'capitalize', 'normal-case'].includes(c)) || 'normal-case'}
              onFontSizeChange={(value) => handlePropertyChange('fontSize', value)}
              onFontWeightChange={(value) => handlePropertyChange('fontWeight', value)}
              onFontFamilyChange={(value) => handlePropertyChange('fontFamily', value)}
              onTextAlignChange={(value) => handlePropertyChange('textAlign', value)}
              onTextTransformChange={(value) => handlePropertyChange('textTransform', value)}
            />
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="w-full h-full flex flex-col bg-gray-900 border-r border-gray-700 relative">
      {/* Removed loading overlay - too intrusive for instant editing */}
      {/* The subtle status indicator in the header is enough */}

      {/* Sidebar Header */}
      <div className="px-4 py-3 bg-gray-800 border-b border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-semibold text-white">
            {selectedElement ? 'Element Properties' : 'Page Info'}
          </h2>
        </div>
        
        {/* Save Status Indicator - Subtle and in corner */}
        <div className="flex items-center gap-2">
          {saveStatus === 'saving' && (
            <div className="flex items-center gap-1.5 px-2 py-1 bg-yellow-500/10 rounded-md border border-yellow-500/20">
              <div className="w-1.5 h-1.5 bg-yellow-500 rounded-full animate-pulse" />
              <span className="text-xs text-yellow-400">Saving</span>
            </div>
          )}
          {saveStatus === 'success' && (
            <div className="flex items-center gap-1.5 px-2 py-1 bg-green-500/10 rounded-md border border-green-500/20">
              <div className="w-1.5 h-1.5 bg-green-500 rounded-full" />
              <span className="text-xs text-green-400">Saved</span>
            </div>
          )}
          {saveStatus === 'error' && (
            <div className="flex items-center gap-1.5 px-2 py-1 bg-red-500/10 rounded-md border border-red-500/20">
              <div className="w-1.5 h-1.5 bg-red-500 rounded-full" />
              <span className="text-xs text-red-400">Error</span>
            </div>
          )}
          {saveStatus === 'idle' && selectedElement && (
            <div className="flex items-center gap-1.5 px-2 py-1 bg-gray-700/50 rounded-md border border-gray-600/20">
              <div className="w-1.5 h-1.5 bg-gray-500 rounded-full" />
              <span className="text-xs text-gray-400">Ready</span>
            </div>
          )}
        </div>
      </div>

      {/* Sidebar Content */}
      {selectedElement ? renderElementEditor() : renderPageInfo()}
    </div>
  );
}

