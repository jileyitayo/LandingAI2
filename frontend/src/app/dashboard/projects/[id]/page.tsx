'use client';

import { useParams, useRouter } from 'next/navigation';
import { useCallback, useState, useEffect, useRef, useMemo } from 'react';
import { ArrowLeft, Save, Download, Eye, Code, FileText, Settings, AlertCircle, RefreshCw, Home } from 'lucide-react';
import WebsitePreview from '@/components/WebsitePreview';
import PublishButton from '@/components/PublishButton';
import PublishModal from '@/components/PublishModal';
import DeploymentHistory from '@/components/DeploymentHistory';
import FileTree from '@/components/FileTree';
import CodeViewer from '@/components/CodeViewer';
import ReactPreview from '@/components/ReactPreview';
import EditSidebar from '@/components/EditSidebar';
import { useProjectEditor } from '@/hooks/useProjectEditor';
import { Project } from '@/types/project.types';
import { api, ApiError } from '@/lib/api';
import { SelectedElement } from '@/types/chat.types';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
import { PropertyType, PageInfo, PropertyEditResponse } from '@/types/property-edit.types';
import Link from 'next/link';
import { toast } from 'sonner';
import { createClient } from '@/lib/supabase/client';

export default function ProjectEditorPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;
  const supabase = createClient();
  const [showPublishModal, setShowPublishModal] = useState(false);
  const [deploymentUrl, setDeploymentUrl] = useState<string | null>(null);
  const [isPublished, setIsPublished] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  // React project state
  const [reactActiveTab, setReactActiveTab] = useState<'code' | 'preview'>('code');
  const [reactFiles, setReactFiles] = useState<Record<string, string>>({});
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isBuilding, setIsBuilding] = useState(false);
  const [buildError, setBuildError] = useState<string | null>(null);

  // Element selection and editing state
  const [selectedElement, setSelectedElement] = useState<SelectedElement | null>(null);
  const [selectorEnabled, setSelectorEnabled] = useState(false);
  const [isAutoSaving, setIsAutoSaving] = useState(false);

  // Page info for sidebar
  const [pageInfo, setPageInfo] = useState<PageInfo>({
    title: '',
    description: '',
    componentCount: 0,
    elementCount: 0,
  });

  // Check authentication on mount - redirect to login if not authenticated
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const {
          data: { session },
          error,
        } = await supabase.auth.getSession();

        if (error) {
          console.error('Auth check error:', error);
          router.push('/auth/login');
          return;
        }

        if (!session) {
          // No session found, redirect to login
          router.push('/auth/login');
          return;
        }

        // User is authenticated, continue loading
        setIsCheckingAuth(false);
      } catch (error) {
        console.error('Failed to check authentication:', error);
        router.push('/auth/login');
      }
    };

    checkAuth();
  }, [supabase, router]);

  useKeyboardShortcuts({
    onToggleSelector: () => {
      if ((project as any)?.project_type === 'react') {
        setSelectorEnabled(prev => !prev);
      }
    },
    onClearSelection: () => {
      setSelectedElement(null);
      setSelectorEnabled(false);
      pendingRequestElementRef.current = null; // Clear pending request tracking
    },
  });

  // Load project from API
  const loadProject = useCallback(async (id: string): Promise<Project> => {
    try {
      const response = await api.projects.get(id);
      
      // Update deployment status
      setDeploymentUrl(response.deployment_url ?? null);
      setIsPublished(response.published ?? false);
      
      return {
        id: response.id,
        name: response.name,
        html_content : response.html_content || '',
        css_content : response.css_content || '',
        js_content : response.js_content || '',
        project_type: response.project_type || 'react',
        user_id: response.user_id,
        created_at: response.created_at,
        updated_at: response.updated_at,
        deployment_url: response.deployment_url ?? undefined,
        published: response.published ?? undefined,
      };
    } catch (error) {
      // Handle ApiError with status codes for better error messages
      if (error instanceof ApiError) {
        // Extract error detail for more context
        const errorDetail = error.detail?.detail || error.detail?.message || error.message || '';
        const detailLower = typeof errorDetail === 'string' ? errorDetail.toLowerCase() : '';
        
        // Check if 500 error is related to project access issues
        if (error.status === 500) {
          // Check if the error detail suggests project access issues
          if (
            detailLower.includes('project') ||
            detailLower.includes('not found') ||
            detailLower.includes('doesn\'t exist') ||
            detailLower.includes('access') ||
            detailLower.includes('permission')
          ) {
            // Likely a project access issue, treat as project not found or access denied
            if (detailLower.includes('permission') || detailLower.includes('access') || detailLower.includes('forbidden')) {
              throw new Error(`403: You don't have permission to access this project`);
            } else {
              throw new Error(`404: Project not found`);
            }
          }
        }
        
        // Preserve status code in error message for getErrorMessage to detect
        const errorMessage = error.status === 404 
          ? `404: Project not found`
          : error.status === 403
          ? `403: You don't have permission to access this project`
          : error.status === 401
          ? `401: Authentication required`
          : error.status === 500
          ? `500: ${errorDetail || error.message || 'Internal server error'}`
          : `HTTP ${error.status}: ${error.message || 'Failed to load project'}`;
        throw new Error(errorMessage);
      }
      
      // For network errors or other errors, preserve the original error message
      // but check if it might contain status information
      const errorMessage = error instanceof Error ? error.message : String(error);
      
      // If it's a generic "Failed to fetch" or network error, we'll let getErrorMessage handle it
      // But if it contains status codes, preserve them
      if (errorMessage.includes('404') || errorMessage.includes('403') || errorMessage.includes('401')) {
        throw new Error(errorMessage);
      }
      
      // Re-throw with original message
      throw new Error(errorMessage || 'Failed to load project');
    }
  }, []);

  // Save project to API
  const saveProject = useCallback(async (data: { html_content: string; css_content: string; js_content: string }) => {
    try {
      await api.projects.update(projectId, data);
    } catch (error) {
      // console.error('Failed to save project:', error);
      throw error;
    }
  }, [projectId]);

  const {
    project,
    editorState,
    isLoading,
    isSaving,
    error,
    updateCode,
    setActiveTab,
    saveProject: handleSave,
    downloadProject: handleDownload,
  } = useProjectEditor({
    projectId,
    onLoad: loadProject,
    onSave: saveProject,
  });

  const handlePublishSuccess = useCallback((url: string) => {
    setDeploymentUrl(url);
    setIsPublished(true);
    setShowPublishModal(true);
  }, []);

  const handleUnpublishSuccess = useCallback(() => {
    setDeploymentUrl(null);
    setIsPublished(false);
  }, []);

  // Custom download handler for React projects
  const handleReactDownload = useCallback(async () => {
    try {
      const response = await api.projects.download(projectId);

      // Get filename from Content-Disposition header
      const contentDisposition = response.headers.get('Content-Disposition');
      const filename = contentDisposition
        ? contentDisposition.split('filename=')[1]?.replace(/"/g, '')
        : `project-${projectId}.zip`;

      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      // console.error('Failed to download React project:', error);
      // You could add a toast notification here
    }
  }, [projectId]);

  // Load React project files
  const loadReactFiles = useCallback(async () => {
    try {
      const data = await api.generation.getReactProject(projectId);
      setReactFiles(data.files);
      // Auto-select first file
      const firstFile = Object.keys(data.files)[0];
      setSelectedFile(firstFile);
      
      // Compute page info
      const componentFiles = Object.keys(data.files).filter(f => f.startsWith('src/components/') && !f.includes('/ui/'));
      const pageFiles = Object.keys(data.files).filter(f => f.startsWith('src/pages/'));
      
      setPageInfo({
        title: project?.name || 'React Project',
        description: project?.description || 'Edit your React components',
        componentCount: componentFiles.length,
        elementCount: componentFiles.length + pageFiles.length, // Simplified count
      });
    } catch (error) {
      // console.error('Failed to load React files:', error);
    }
  }, [projectId, project]);

  // Build preview
  const buildPreview = useCallback(async () => {
    setIsBuilding(true);
    setBuildError(null);
    try {
      const result = await api.generation.createPreview(projectId);
      // console.log("result", result);
      setPreviewUrl(`http://localhost:8000${result.preview_url}`);
    } catch (error: any) {
      setBuildError(error.message || 'Build failed');
    } finally {
      setIsBuilding(false);
    }
  }, [projectId]);

  // Load React files when project is loaded
  useEffect(() => {
    if ((project as any)?.project_type === 'react') {
      loadReactFiles();
    }
  }, [project, loadReactFiles]);

  // Auto-build preview when switching to preview tab
  // Also refresh preview to pick up any background rebuilds
  useEffect(() => {
    // Only run this logic when tab actually changes (not on every render)
    const tabChanged = previousTabRef.current !== reactActiveTab;
    previousTabRef.current = reactActiveTab;

    if (reactActiveTab === 'preview' && tabChanged) {
      if (!previewUrl && !isBuilding) {
        // No preview exists, build it
        buildPreview();
      } else if (previewUrl) {
        // Preview exists, refresh it to pick up any edits
        // This ensures iframe loads the latest build (from background rebuilds)
        const baseUrl = previewUrl.split('?')[0];
        const timestamp = Date.now();
        setPreviewUrl(`${baseUrl}?_t=${timestamp}`);
      }
    }
  }, [reactActiveTab, previewUrl, isBuilding, buildPreview]);

  // Ref to track pending backend saves
  const pendingSaveRef = useRef<NodeJS.Timeout | null>(null);
  const iframeRef = useRef<HTMLIFrameElement | null>(null);
  // Ref to track previous tab to prevent infinite loop
  const previousTabRef = useRef<'code' | 'preview'>('code');

  // Apply optimistic update to preview iframe (instant feedback)
  const applyOptimisticUpdate = useCallback((selector: string, property: PropertyType | 'src' | 'href' | 'target' | 'rel', value: string | number | boolean) => {
    // console.log('🚀 Applying optimistic update:', { selector, property, value });
    
    // Find the iframe (it's in the ReactPreview component)
    const iframe = document.querySelector('iframe[title="React Preview"]') as HTMLIFrameElement;
    
    if (!iframe || !iframe.contentWindow) {
      // console.warn('❌ Preview iframe not found for optimistic update');
      return false;
    }
    
    // Send update message to iframe
    iframe.contentWindow.postMessage({
      type: 'UPDATE_PROPERTY',
      selector: selector,
      property: property,
      value: value
    }, '*');
    
    // console.log('✅ Sent optimistic update to iframe:', { selector, property, value });
    return true;
  }, []);

  // Track the element selector for the current pending request
  // This helps us ignore responses from stale requests when user switches elements
  const pendingRequestElementRef = useRef<string | null>(null);

  // Track pending image property changes to batch them together
  // This allows us to save both imageUrl and imageAlt in a single API call when both change
  const pendingImagePropertiesRef = useRef<{
    imageUrl?: { value: string | number | boolean; element: SelectedElement };
    imageAlt?: { value: string | number | boolean; element: SelectedElement };
  }>({});

  // Debounced backend save (500ms after last change)
  const debouncedBackendSave = useCallback(async (
    property: PropertyType,
    value: string | number | boolean,
    element: SelectedElement
  ) => {
    // Clear any pending save
    if (pendingSaveRef.current) {
      clearTimeout(pendingSaveRef.current);
    }

    // Track the element selector for this request
    const requestElementSelector = element.elementSelector || null;
    pendingRequestElementRef.current = requestElementSelector;

    // If this is an image property, store it in the pending queue
    // This allows us to batch imageUrl and imageAlt together
    if (property === 'imageUrl' || property === 'imageAlt') {
      pendingImagePropertiesRef.current[property] = { value, element };
    }

    // Schedule new save
    pendingSaveRef.current = setTimeout(async () => {
      // console.log('🔄 Saving to backend (debounced):', { property, value });
      // console.log('📍 Element selector:', element.elementSelector);
      // console.log('📄 Component file:', element.componentFile);
      // console.log('🔍 Full element:', element);
      setIsAutoSaving(true);

      try {
        // Check if we have both imageUrl and imageAlt pending for the same element
        // If so, batch them together in a single API call
        const pendingImageUrl = pendingImagePropertiesRef.current.imageUrl;
        const pendingImageAlt = pendingImagePropertiesRef.current.imageAlt;
        const isImageProperty = property === 'imageUrl' || property === 'imageAlt';
        
        // Determine if we should batch image properties
        const shouldBatchImages = isImageProperty && 
          pendingImageUrl && 
          pendingImageAlt &&
          pendingImageUrl.element.elementSelector === pendingImageAlt.element.elementSelector &&
          pendingImageUrl.element.componentFile === pendingImageAlt.element.componentFile;

        // Store batched values before clearing ref (needed for response handler)
        const batchedImageUrl = shouldBatchImages ? pendingImageUrl.value : undefined;
        const batchedImageAlt = shouldBatchImages ? pendingImageAlt.value : undefined;

        let propertiesToSave: Array<{
          property: string;
          value: string | number | boolean;
          oldValue?: string | number | boolean;
        }>;

        if (shouldBatchImages) {
          // Batch both imageUrl and imageAlt together
          // Check if imageUrl is empty - only include it if it's being removed (was previously set)
          const imageUrlValue = String(pendingImageUrl.value);
          const previousSrc = pendingImageUrl.element.attributes?.src;
          const isImageUrlRemoval = imageUrlValue === '' && previousSrc && previousSrc !== '';
          
          propertiesToSave = [];
          
          // Only include imageUrl if it's not empty OR if it's being removed
          if (imageUrlValue !== '' || isImageUrlRemoval) {
            propertiesToSave.push({
              property: 'src', // imageUrl maps to src
              value: pendingImageUrl.value,
              oldValue: undefined,
            });
          }
          
          // Always include imageAlt (it can be empty)
          propertiesToSave.push({
            property: 'alt', // imageAlt maps to alt
            value: pendingImageAlt.value,
            oldValue: undefined,
          });
          
          // Use the element from either pending property (they're the same)
          element = pendingImageUrl.element;
          
          // Clear the pending image properties after batching
          pendingImagePropertiesRef.current = {};
          
          // Note: We always have at least imageAlt, so propertiesToSave will never be empty
        } else if (isImageProperty) {
          // Single image property - use the pending value or current value
          const pendingValue = property === 'imageUrl' ? pendingImageUrl : pendingImageAlt;
          const actualValue = pendingValue?.value ?? value;
          
          // For imageUrl: skip if empty unless it's being removed
          if (property === 'imageUrl') {
            const imageUrlValue = String(actualValue);
            const previousSrc = element.attributes?.src;
            const isImageUrlRemoval = imageUrlValue === '' && previousSrc && previousSrc !== '';
            
            // Skip empty imageUrl unless it's being removed
            if (imageUrlValue === '' && !isImageUrlRemoval) {
              // Clear from pending queue and skip API call
              delete pendingImagePropertiesRef.current.imageUrl;
              setIsAutoSaving(false);
              return;
            }
          }
          
          // Map frontend property names to backend property names
          // imageUrl -> src, imageAlt -> alt for backend
          const backendProperty = property === 'imageUrl' ? 'src' : 'alt';
          
          propertiesToSave = [{
            property: backendProperty,
            value: actualValue,
            oldValue: undefined,
          }];
          
          // Clear this specific property from pending queue
          if (property === 'imageUrl') {
            delete pendingImagePropertiesRef.current.imageUrl;
          } else {
            delete pendingImagePropertiesRef.current.imageAlt;
          }
        } else {
          // Non-image property - map frontend property names to backend property names
          // linkHref -> href, linkTarget -> target, linkRel -> rel for backend
          const backendProperty = property === 'linkHref' ? 'href'
            : property === 'linkTarget' ? 'target'
            : property === 'linkRel' ? 'rel'
            : property;
          
          propertiesToSave = [{
            property: backendProperty,
            value,
            oldValue: undefined,
          }];
        }
        
        const response = await api.generation.editProperties(projectId, {
          element_selector: element.elementSelector || '',
          component_file: element.componentFile || '',
          properties: propertiesToSave,
          batch: shouldBatchImages, // Set batch to true when batching multiple properties
        });

        // Check if this response is for the currently selected element
        // If user switched elements, ignore this response
        const isStaleRequest = pendingRequestElementRef.current !== requestElementSelector;
        
        if (isStaleRequest) {
          // console.log('⚠️ Ignoring stale response - user switched elements');
          return;
        }

        if (response.success) {
          // console.log('Backend save successful');
          
          // Update the code view with the new code from backend
          // Backend returns the updated code, so we can update it directly
          if (response.new_code && element.componentFile) {
            setReactFiles(prev => ({
              ...prev,
              [element.componentFile!]: response.new_code!
            }));
            // console.log('Code view updated instantly');
          }
          
          // Update selectedElement state to reflect the new attribute value
          // This ensures the input field shows the current value after save
          if (shouldBatchImages && batchedImageUrl !== undefined && batchedImageAlt !== undefined) {
            // Update both imageUrl and imageAlt when batched
            // Only update imageUrl if it was actually saved (not skipped)
            const imageUrlValue = String(batchedImageUrl);
            const previousSrc = element.attributes?.src;
            const isImageUrlRemoval = imageUrlValue === '' && previousSrc && previousSrc !== '';
            const shouldUpdateImageUrl = imageUrlValue !== '' || isImageUrlRemoval;
            
            setSelectedElement(prev => {
              if (!prev) return prev;
              const updatedAttributes = { ...prev.attributes };
              
              // Only update src if it was actually saved
              if (shouldUpdateImageUrl) {
                updatedAttributes.src = imageUrlValue;
              }
              
              // Always update alt
              updatedAttributes.alt = String(batchedImageAlt);
              
              return {
                ...prev,
                attributes: updatedAttributes,
              };
            });
          } else if (property === 'imageUrl') {
            setSelectedElement(prev => {
              if (!prev) return prev;
              return {
                ...prev,
                attributes: {
                  ...prev.attributes,
                  src: String(value)
                }
              };
            });
          } else if (property === 'imageAlt') {
            setSelectedElement(prev => {
              if (!prev) return prev;
              return {
                ...prev,
                attributes: {
                  ...prev.attributes,
                  alt: String(value)
                }
              };
            });
          }
          
          // Check if this was a prop edit - if so, navigate to the prop definition
          if (response.prop_edit_info && response.prop_edit_info.prop_name) {
            const propFile = response.prop_edit_info.source_file;
            if (propFile && propFile !== element.componentFile) {
              // Navigate to the file where the prop is defined
              setSelectedFile(propFile);
              toast.info("Prop Updated", {
                description: `Updated ${response.prop_edit_info.prop_name} in ${propFile}`,
                duration: 3000,
              });
            }
          }
          
          // DON'T reload the preview! The optimistic update already applied the changes.
          // Reloading would cause a flicker and defeat the purpose of optimistic updates.
          // The backend has saved the changes, they'll persist on next full reload.
          
          // No toast notification - the sidebar status indicator is enough!
        } else {
          throw new Error(response.message || 'Save failed');
        }
      } catch (error: any) {
        // Check if this error is for a stale request
        const isStaleRequest = pendingRequestElementRef.current !== requestElementSelector;
        
        if (isStaleRequest) {
          // console.log('⚠️ Ignoring stale error - user switched elements');
          return;
        }

        // console.error('Backend save failed:', error);
        // // Only show toast for errors - more subtle than showing on every save
        // toast.error("Could not save", {
        //   description: "Changes may not persist",
        //   duration: 2000,
        // });
        // Note: Optimistic update is already applied, so preview still looks correct
        // Errors are logged but not shown to user to avoid interrupting their workflow
      } finally {
        // Only clear saving state if this is still the current request
        const isStaleRequest = pendingRequestElementRef.current !== requestElementSelector;
        if (!isStaleRequest) {
          setIsAutoSaving(false);
        }
      }
    }, 500); // Wait 500ms after last change
  }, [projectId, loadReactFiles]);

  // Clear stale request tracking when selected element changes
  // This ensures responses from old requests are ignored when user switches elements
  useEffect(() => {
    const currentSelector = selectedElement?.elementSelector || null;
    
    // If the selected element changed, mark any pending request as stale
    // (The pendingRequestElementRef will be updated when a new request is made)
    if (pendingRequestElementRef.current !== null && pendingRequestElementRef.current !== currentSelector) {
      // console.log('🔄 Element changed, marking pending requests as stale');
      // The ref will be updated when debouncedBackendSave is called for the new element
    }
    
    // Clear pending image properties when element changes
    // This prevents batching properties from different elements
    if (currentSelector !== null) {
      const pendingImageUrl = pendingImagePropertiesRef.current.imageUrl;
      const pendingImageAlt = pendingImagePropertiesRef.current.imageAlt;
      
      // Clear if pending properties are for a different element
      if (pendingImageUrl && pendingImageUrl.element.elementSelector !== currentSelector) {
        delete pendingImagePropertiesRef.current.imageUrl;
      }
      if (pendingImageAlt && pendingImageAlt.element.elementSelector !== currentSelector) {
        delete pendingImagePropertiesRef.current.imageAlt;
      }
    } else {
      // No element selected - clear all pending image properties
      pendingImagePropertiesRef.current = {};
    }
  }, [selectedElement?.elementSelector]);

  // Handle property changes with optimistic updates
  const handlePropertyChange = useCallback((property: PropertyType, value: string | number | boolean) => {
    // console.log('🎯 handlePropertyChange called:', { property, value });
    
    if (!selectedElement) {
      // console.warn('❌ No element selected');
      return;
    }

    // Validate that we have the necessary data
    if (!selectedElement.componentFile || !selectedElement.elementSelector) {
      // console.error('❌ Missing component file or element selector', selectedElement);
      toast.error("Update Failed", {
        description: "Cannot update: missing component information",
        duration: 3000,
      });
      return;
    }

    // Map frontend property names to backend/dom property names
    // imageUrl -> src for backend and DOM updates
    // linkHref -> href, linkTarget -> target, linkRel -> rel for backend and DOM updates
    const backendProperty = property === 'imageUrl' ? 'src' 
      : property === 'linkHref' ? 'href'
      : property === 'linkTarget' ? 'target'
      : property === 'linkRel' ? 'rel'
      : property;
    const previewProperty = property === 'imageUrl' ? 'src' 
      : property === 'linkHref' ? 'href'
      : property === 'linkTarget' ? 'target'
      : property === 'linkRel' ? 'rel'
      : property;

    // console.log('✅ Valid element, proceeding with update:', { 
    //   property, 
    //   backendProperty,
    //   value,
    //   selector: selectedElement.elementSelector 
    // });
    
    // Step 1: Apply optimistic update to preview IMMEDIATELY (< 50ms)
    // Use previewProperty (which maps imageUrl -> src) for the iframe update
    const optimisticSuccess = applyOptimisticUpdate(
      selectedElement.elementSelector,
      previewProperty,
      value
    );
    
    if (optimisticSuccess) {
      // console.log('✅ Optimistic update applied successfully');
    } else {
      // console.warn('⚠️ Optimistic update failed');
    }
    
    // Step 2: Update selectedElement state to reflect the new value
    setSelectedElement(prev => {
      if (!prev) return prev;
      
      const newClassList = [...prev.classList];
      const newInlineStyles = { ...prev.inlineStyles };
      const newAttributes = { ...prev.attributes };
      const valueStr = String(value);
      
      // Handle imageUrl property - update src attribute
      if (property === 'imageUrl') {
        newAttributes.src = valueStr;
        return { ...prev, attributes: newAttributes };
      }
      
      // Handle imageAlt property - update alt attribute
      if (property === 'imageAlt') {
        newAttributes.alt = valueStr;
        return { ...prev, attributes: newAttributes };
      }
      
      // Handle link properties - update href and target attributes
      if (property === 'linkHref') {
        newAttributes.href = valueStr;
        return { ...prev, attributes: newAttributes };
      }
      
      if (property === 'linkTarget') {
        newAttributes.target = valueStr;
        return { ...prev, attributes: newAttributes };
      }
      
      if (property === 'linkRel') {
        newAttributes.rel = valueStr;
        return { ...prev, attributes: newAttributes };
      }
      
      // Handle color properties
      if (property === 'color' || property === 'textColor') {
        // Remove old text-color classes
        const filtered = newClassList.filter(c => !/^text-\w+-\d+$/.test(c));
        
        if (valueStr.startsWith('#')) {
          // Custom hex color - store in inline styles
          newInlineStyles.color = valueStr;
          return { ...prev, classList: filtered, inlineStyles: newInlineStyles };
        } else {
          // Tailwind class - remove inline style and add class
          delete newInlineStyles.color;
          filtered.push(valueStr);
          return { ...prev, classList: filtered, inlineStyles: newInlineStyles };
        }
      } else if (property === 'backgroundColor') {
        // Remove old bg-color classes
        const filtered = newClassList.filter(c => !/^bg-(\w+-\d+|transparent|white|black)$/.test(c));
        
        if (valueStr.startsWith('#')) {
          // Custom hex color - store in inline styles
          newInlineStyles.backgroundColor = valueStr;
          return { ...prev, classList: filtered, inlineStyles: newInlineStyles };
        } else {
          // Tailwind class - remove inline style and add class
          delete newInlineStyles.backgroundColor;
          filtered.push(valueStr);
          return { ...prev, classList: filtered, inlineStyles: newInlineStyles };
        }
      } else if (property === 'borderColor') {
        // Remove old border-color classes
        const filtered = newClassList.filter(c => !/^border-\w+-\d+$/.test(c));
        
        if (valueStr.startsWith('#')) {
          // Custom hex color - store in inline styles
          newInlineStyles.borderColor = valueStr;
          return { ...prev, classList: filtered, inlineStyles: newInlineStyles };
        } else {
          // Tailwind class - remove inline style and add class
          delete newInlineStyles.borderColor;
          filtered.push(valueStr);
          return { ...prev, classList: filtered, inlineStyles: newInlineStyles };
        }
      }
      // Handle typography properties
      else if (property === 'fontSize') {
        // Remove old font-size classes
        const filtered = newClassList.filter(c => !/^text-(xs|sm|base|lg|xl|2xl|3xl|4xl|5xl|6xl|7xl|8xl|9xl)$/.test(c));
        filtered.push(valueStr);
        return { ...prev, classList: filtered };
      } else if (property === 'fontWeight') {
        // Remove old font-weight classes
        const filtered = newClassList.filter(c => !/^font-(thin|extralight|light|normal|medium|semibold|bold|extrabold|black)$/.test(c));
        filtered.push(valueStr);
        return { ...prev, classList: filtered };
      } else if (property === 'fontFamily') {
        // Remove old font-family classes
        const filtered = newClassList.filter(c => !/^font-(sans|serif|mono)$/.test(c));
        filtered.push(valueStr);
        return { ...prev, classList: filtered };
      } else if (property === 'textAlign') {
        // Remove old text-align classes
        const filtered = newClassList.filter(c => !/^text-(left|center|right|justify)$/.test(c));
        filtered.push(valueStr);
        return { ...prev, classList: filtered };
      } else if (property === 'textTransform') {
        // Remove old text-transform classes
        const filtered = newClassList.filter(c => !/^(normal-case|uppercase|lowercase|capitalize)$/.test(c));
        filtered.push(valueStr);
        return { ...prev, classList: filtered };
      }
      
      return prev;
    });
    
    // No toast for optimistic update - the visual change in preview is feedback enough!
    // Toast notifications would be distracting when typing rapidly
    
    // Step 3: Save to backend (debounced - waits 500ms after last change)
    debouncedBackendSave(property, value, selectedElement);
    
  }, [selectedElement, applyOptimisticUpdate, debouncedBackendSave]);

  // Helper function to get user-friendly error message
  // Note: This is a regular function, not a hook, so it can be defined here
  const getErrorMessage = (error: string | null): { title: string; message: string; canRetry: boolean } => {
    if (!error) {
      return {
        title: 'Something went wrong',
        message: 'An unexpected error occurred. Please try again.',
        canRetry: true,
      };
    }

    const errorLower = error.toLowerCase();

    // 404 errors - Project not found (check FIRST before generic errors)
    // Check for explicit status codes and common 404 messages
    if (
      errorLower.includes('404') || 
      errorLower.includes('project not found') || 
      (errorLower.includes('not found') && !errorLower.includes('failed to fetch')) ||
      errorLower.includes('doesn\'t exist') ||
      errorLower.includes('does not exist') ||
      errorLower.match(/\b404\b/) // Exact word match for 404
    ) {
      return {
        title: 'Project Not Found',
        message: 'The project you\'re looking for doesn\'t exist or may have been deleted. Please check the project ID or return to your dashboard.',
        canRetry: false,
      };
    }

    // 403 errors - Access denied / Permission denied (check BEFORE network errors)
    if (
      errorLower.includes('403') || 
      errorLower.includes('forbidden') || 
      errorLower.includes('permission') ||
      errorLower.includes('don\'t have permission') ||
      errorLower.includes('access this project') ||
      errorLower.includes('access denied') ||
      errorLower.match(/\b403\b/) // Exact word match for 403
    ) {
      return {
        title: 'Access Denied',
        message: 'You don\'t have permission to access this project. This project may belong to another user, or you may need to sign in with a different account.',
        canRetry: false,
      };
    }

    // 401 errors - Authentication required
    if (
      errorLower.includes('401') || 
      errorLower.includes('authentication required') || 
      errorLower.includes('unauthorized') ||
      errorLower.match(/\b401\b/) // Exact word match for 401
    ) {
      return {
        title: 'Authentication Required',
        message: 'Please sign in to access this project.',
        canRetry: false,
      };
    }

    // Network errors (only if NOT a status code error)
    // Check for network-related errors that aren't HTTP status codes
    if (
      (errorLower.includes('failed to fetch') || 
       errorLower.includes('network') || 
       errorLower.includes('fetch')) &&
      !errorLower.match(/\b(404|403|401|500)\b/) // Exclude if contains status codes
    ) {
      return {
        title: 'Connection Problem',
        message: 'Unable to connect to the server. Please check your internet connection and try again.',
        canRetry: true,
      };
    }

    // 500 errors - Check if it's related to project access issues
    if (errorLower.includes('500') || errorLower.includes('server error') || errorLower.includes('internal error')) {
      // Check if the error message suggests project access issues
      const isProjectAccessError = 
        errorLower.includes('project') ||
        errorLower.includes('not found') ||
        errorLower.includes('doesn\'t exist') ||
        errorLower.includes('access') ||
        errorLower.includes('permission') ||
        errorLower.includes('can\'t access') ||
        errorLower.includes('cannot access');
      
      if (isProjectAccessError) {
        // Determine if it's a permission issue or not found issue
        if (errorLower.includes('permission') || errorLower.includes('access') || errorLower.includes('forbidden')) {
          return {
            title: 'Access Denied',
            message: 'You don\'t have permission to access this project. This project may belong to another user, or you may need to sign in with a different account.',
            canRetry: false,
          };
        } else {
          return {
            title: 'Project Not Found',
            message: 'The project you\'re looking for doesn\'t exist or may have been deleted. Please check the project ID or return to your dashboard.',
            canRetry: false,
          };
        }
      }
      
      // Generic 500 error
      return {
        title: 'Server Error',
        message: 'Our servers encountered an issue. We\'re working on it. Please try again in a moment.',
        canRetry: true,
      };
    }

    // Timeout errors
    if (errorLower.includes('timeout') || errorLower.includes('timed out')) {
      return {
        title: 'Request Timeout',
        message: 'The request took too long to complete. Please try again.',
        canRetry: true,
      };
    }

    // Default - show original error but with better formatting
    return {
      title: 'Error Loading Project',
      message: error,
      canRetry: true,
    };
  };

  // Retry loading the project
  // IMPORTANT: This hook must be called before any conditional returns
  const handleRetry = useCallback(() => {
    window.location.reload();
  }, []);

  // Conditional returns must come AFTER all hooks
  // Show loading while checking authentication
  if (isCheckingAuth) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="inline-block w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4"></div>
          <p className="text-gray-600">Checking authentication...</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="inline-block w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4"></div>
          <p className="text-gray-600">Loading project...</p>
        </div>
      </div>
    );
  }

  if (error) {
    const errorInfo = getErrorMessage(error);
    
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="max-w-md w-full mx-4">
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            {/* Error Icon */}
            <div className="flex justify-center mb-6">
              <div className={`w-16 h-16 rounded-full flex items-center justify-center ${
                errorInfo.title === 'Project Not Found' || errorInfo.title === 'Access Denied' || errorInfo.title === 'Authentication Required'
                  ? 'bg-orange-100'
                  : 'bg-red-100'
              }`}>
                <AlertCircle className={`w-8 h-8 ${
                  errorInfo.title === 'Project Not Found' || errorInfo.title === 'Access Denied' || errorInfo.title === 'Authentication Required'
                    ? 'text-orange-600'
                    : 'text-red-600'
                }`} />
              </div>
            </div>

            {/* Error Title */}
            <h2 className="text-2xl font-semibold text-gray-900 mb-3">
              {errorInfo.title}
            </h2>

            {/* Error Message */}
            <p className="text-gray-600 mb-8 leading-relaxed">
              {errorInfo.message}
            </p>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              {errorInfo.canRetry && (
                <button
                  onClick={handleRetry}
                  className="flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  <RefreshCw className="w-5 h-5" />
                  Try Again
                </button>
              )}
              <button
                onClick={() => router.push('/dashboard')}
                className="flex items-center justify-center gap-2 px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
              >
                <Home className="w-5 h-5" />
                Back to Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Might delete this later
  const { html_content, css_content, js_content, activeTab, hasUnsavedChanges } = editorState;
  const currentCode = activeTab === 'html_content' ? html_content : activeTab === 'css_content' ? css_content : js_content;

  // Render React project editor
  if (project?.project_type === 'react') {
    return (
      <div className="h-screen flex flex-col bg-gray-900">
        {/* Header */}
        <header className="flex items-center justify-between px-4 py-3 bg-gray-800 border-b border-gray-700">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push('/dashboard')}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
              title="Back to dashboard"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-lg font-semibold text-white">
                {project?.name || 'Untitled Project'}
              </h1>
              <p className="text-sm text-gray-400">React Project</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href={`/dashboard/projects/${projectId}/settings`}
              className="flex items-center gap-2 px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
              title="Project settings"
            >
              <Settings className="w-4 h-4" />
              <span className="hidden sm:inline">Settings</span>
            </Link>
            <button
              onClick={project?.project_type === 'react' ? handleReactDownload : handleDownload}
              className="flex items-center gap-2 px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
              title="Download project"
            >
              <Download className="w-4 h-4" />
              <span className="hidden sm:inline">Download</span>
            </button>
            <PublishButton
              projectId={projectId}
              projectName={project?.name || 'Untitled Project'}
              deploymentUrl={deploymentUrl}
              isPublished={isPublished}
              onPublishSuccess={handlePublishSuccess}
              onUnpublishSuccess={handleUnpublishSuccess}
            />
          </div>
        </header>

        {/* Main Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left Panel - Edit Sidebar (1/4) */}
          <div className="w-1/4 flex flex-col bg-gray-900 border-r border-gray-700">
            <EditSidebar
              selectedElement={selectedElement}
              pageInfo={pageInfo}
              onClearSelection={() => {
                setSelectedElement(null);
                pendingRequestElementRef.current = null; // Clear pending request tracking
              }}
              onPropertyChange={handlePropertyChange}
              isAutoSaving={isAutoSaving}
              projectFiles={reactFiles}
            />
          </div>

          {/* Right Panel - Code/Preview (3/4) */}
          <div className="w-3/4 flex flex-col bg-gray-900">
            {/* Tabs */}
            <div className="flex items-center bg-gray-800 border-b border-gray-700">
              <button
                onClick={() => setReactActiveTab('code')}
                className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                  reactActiveTab === 'code'
                    ? 'border-blue-500 text-white bg-gray-900'
                    : 'border-transparent text-gray-400 hover:text-white hover:bg-gray-700'
                }`}
              >
                <Code className="w-4 h-4" />
                <span className="font-medium">React Code</span>
              </button>
              <button
                onClick={() => setReactActiveTab('preview')}
                className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                  reactActiveTab === 'preview'
                    ? 'border-blue-500 text-white bg-gray-900'
                    : 'border-transparent text-gray-400 hover:text-white hover:bg-gray-700'
                }`}
              >
                <Eye className="w-4 h-4" />
                <span className="font-medium">Preview</span>
              </button>
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-hidden">
              {reactActiveTab === 'code' ? (
                <div className="h-full flex">
                  {/* File Tree (1/4) */}
                  <div className="w-1/4">
                    <FileTree
                      files={reactFiles}
                      selectedFile={selectedFile}
                      onFileSelect={setSelectedFile}
                    />
                  </div>
                  {/* Code Viewer (3/4) */}
                  <div className="w-3/4">
                    <CodeViewer
                      fileName={selectedFile}
                      content={selectedFile ? reactFiles[selectedFile] : null}
                    />
                  </div>
                </div>
              ) : (
                <ReactPreview
                  previewUrl={previewUrl}
                  isBuilding={isBuilding}
                  error={buildError}
                  onRebuild={buildPreview}
                  selectedElement={selectedElement}
                  onElementSelect={setSelectedElement}
                  selectorEnabled={selectorEnabled}
                  onSelectorEnabledChange={setSelectorEnabled}
                />
              )}
            </div>
          </div>
        </div>

        {/* Publish Success Modal */}
        <PublishModal
          isOpen={showPublishModal}
          onClose={() => setShowPublishModal(false)}
          deploymentUrl={deploymentUrl || ''}
          projectName={project?.name || 'Untitled Project'}
        />
      </div>
    );
  }

  // Render HTML/CSS/JS editor (existing code) - might delete this later
  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push('/dashboard')}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
            title="Back to dashboard"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-lg font-semibold text-white">
              {project?.name || 'Untitled Project'}
            </h1>
            {hasUnsavedChanges && (
              <p className="text-sm text-gray-400">Unsaved changes</p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href={`/dashboard/projects/${projectId}/settings`}
            className="flex items-center gap-2 px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
            title="Project settings"
          >
            <Settings className="w-4 h-4" />
            <span className="hidden sm:inline">Settings</span>
          </Link>
          <button
            onClick={handleDownload}
            className="flex items-center gap-2 px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
            title="Download HTML"
          >
            <Download className="w-4 h-4" />
            <span className="hidden sm:inline">Download</span>
          </button>
          <button
            onClick={() => handleSave()}
            disabled={!hasUnsavedChanges || isSaving}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              hasUnsavedChanges && !isSaving
                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                : 'bg-gray-700 text-gray-400 cursor-not-allowed'
            }`}
            title="Save changes"
          >
            <Save className="w-4 h-4" />
            <span className="hidden sm:inline">
              {isSaving ? 'Saving...' : 'Save'}
            </span>
          </button>
          <PublishButton
            projectId={projectId}
            projectName={project?.name || 'Untitled Project'}
            deploymentUrl={deploymentUrl}
            isPublished={isPublished}
            onPublishSuccess={handlePublishSuccess}
            onUnpublishSuccess={handleUnpublishSuccess}
          />
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Editor Panel */}
        <div className="w-1/2 flex flex-col bg-gray-900 border-r border-gray-700">
          {/* Editor Tabs */}
          <div className="flex items-center bg-gray-800 border-b border-gray-700">
            <button
              onClick={() => setActiveTab('html_content')}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                activeTab === 'html_content'
                  ? 'border-blue-500 text-white bg-gray-900'
                  : 'border-transparent text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <FileText className="w-4 h-4" />
              <span className="font-medium">HTML</span>
            </button>
            <button
              onClick={() => setActiveTab('css_content')}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                activeTab === 'css_content'
                  ? 'border-blue-500 text-white bg-gray-900'
                  : 'border-transparent text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Code className="w-4 h-4" />
              <span className="font-medium">CSS</span>
            </button>
            <button
              onClick={() => setActiveTab('js_content')}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                activeTab === 'js_content'
                  ? 'border-blue-500 text-white bg-gray-900'
                  : 'border-transparent text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Code className="w-4 h-4" />
              <span className="font-medium">JavaScript</span>
            </button>
          </div>

          {/* Code Editor */}
          <div className="flex-1 overflow-auto">
            <textarea
              value={currentCode}
              onChange={(e) => updateCode(e.target.value)}
              className="w-full h-full px-4 py-4 bg-gray-900 text-gray-100 font-mono text-sm leading-relaxed resize-none focus:outline-none"
              style={{
                fontFamily: "'Fira Code', 'Consolas', 'Monaco', 'Courier New', monospace",
                tabSize: 2,
              }}
              spellCheck={false}
              placeholder={`Enter ${activeTab.toUpperCase()} code here...`}
            />
          </div>

          {/* Editor Footer */}
          <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-t border-gray-700 text-xs text-gray-400">
            <span>
              {activeTab.toUpperCase()} • {currentCode.split('\n').length} lines
            </span>
            <span>UTF-8</span>
          </div>
        </div>

        {/* Preview Panel */}
        <div className="w-1/2 flex flex-col bg-white">
          <div className="flex items-center justify-between px-4 py-3 bg-gray-800 border-b border-gray-700">
            <div className="flex items-center gap-2 text-white">
              <Eye className="w-4 h-4" />
              <span className="font-medium">Live Preview</span>
            </div>
          </div>
          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="flex-1 overflow-hidden">
              <WebsitePreview
                html={html_content}
                css={css_content}
                js={js_content}
                isLoading={false}
              />
            </div>
            
            {/* Deployment History */}
            {/* <div className="p-4 bg-gray-50 border-t border-gray-200">
              <DeploymentHistory projectId={projectId} />
            </div> */}
          </div>
        </div>
      </div>

      {/* Publish Success Modal */}
      <PublishModal
        isOpen={showPublishModal}
        onClose={() => setShowPublishModal(false)}
        deploymentUrl={deploymentUrl || ''}
        projectName={project?.name || 'Untitled Project'}
      />
    </div>
  );
}

