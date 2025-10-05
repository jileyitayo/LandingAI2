import { useState, useEffect, useCallback } from 'react';
import { Project, EditorTab, EditorState } from '@/types/project.types';

interface UseProjectEditorOptions {
  projectId: string;
  onSave?: (data: { html_content: string; css_content: string; js_content: string }) => Promise<void>;
  onLoad?: (projectId: string) => Promise<Project>;
}

export function useProjectEditor({ 
  projectId, 
  onSave, 
  onLoad 
}: UseProjectEditorOptions) {
  const [project, setProject] = useState<Project | null>(null);
  const [editorState, setEditorState] = useState<EditorState>({
    html_content: '',
    css_content: '',
    js_content: '',
    activeTab: 'html_content',
    hasUnsavedChanges: false,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load project data
  useEffect(() => {
    const loadProject = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        if (onLoad) {
          const data = await onLoad(projectId);
          setProject(data);
          setEditorState(prev => ({
            ...prev,
            html_content: data.html_content,
            css_content: data.css_content,
            js_content: data.js_content,
          }));
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load project');
        console.error('Failed to load project:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadProject();
  }, [projectId, onLoad]);

  // Track unsaved changes
  useEffect(() => {
    if (!project) return;
    
    const hasChanges = 
      editorState.html_content !== project.html_content ||
      editorState.css_content !== project.css_content ||
      editorState.js_content !== project.js_content;
    
    // Only update if the hasUnsavedChanges value actually changed
    if (hasChanges !== editorState.hasUnsavedChanges) {
      setEditorState(prev => ({
        ...prev,
        hasUnsavedChanges: hasChanges,
      }));
    }
  }, [editorState.html_content, editorState.css_content, editorState.js_content, editorState.hasUnsavedChanges, project]);

  // Update code for active tab
  const updateCode = useCallback((code: string) => {
    setEditorState(prev => ({
      ...prev,
      [prev.activeTab]: code,
    }));
  }, []);

  // Change active tab
  const setActiveTab = useCallback((tab: EditorTab) => {
    setEditorState(prev => ({
      ...prev,
      activeTab: tab,
    }));
  }, []);

  // Save project
  const saveProject = useCallback(async () => {
    if (!editorState.hasUnsavedChanges || isSaving) return;

    try {
      setIsSaving(true);
      setError(null);

      const { html_content, css_content, js_content } = editorState;
      
      if (onSave) {
        await onSave({ html_content, css_content, js_content });
      }

      // Update local project state
      if (project) {
        setProject({
          ...project,
          html_content,
          css_content,  
          js_content,
          updated_at: new Date().toISOString(),
        });
      }

      setEditorState(prev => ({
        ...prev,
        hasUnsavedChanges: false,
      }));

      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save project');
      console.error('Failed to save project:', err);
      return false;
    } finally {
      setIsSaving(false);
    }
  }, [editorState, project, isSaving, onSave]);

  // Download project as HTML file
  const downloadProject = useCallback(() => {
    if (!project) return;

    const fullHTML = `<!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>${project.name}</title>
          <style>
        ${editorState.css_content}
          </style>
        </head>
        <body>
        ${editorState.html_content}
          <script>
        ${editorState.js_content}
          </script>
        </body>
        </html>`;

    const blob = new Blob([fullHTML], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${project.name}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [project, editorState]);

  return {
    project,
    editorState,
    isLoading,
    isSaving,
    error,
    updateCode,
    setActiveTab,
    saveProject,
    downloadProject,
  };
}

