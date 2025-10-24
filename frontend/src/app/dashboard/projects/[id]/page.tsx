'use client';

import { useParams, useRouter } from 'next/navigation';
import { useCallback, useState, useEffect, useRef } from 'react';
import { ArrowLeft, Save, Download, Eye, Code, FileText, Settings } from 'lucide-react';
import WebsitePreview from '@/components/WebsitePreview';
import PublishButton from '@/components/PublishButton';
import PublishModal from '@/components/PublishModal';
import DeploymentHistory from '@/components/DeploymentHistory';
import FileTree from '@/components/FileTree';
import CodeViewer from '@/components/CodeViewer';
import ReactPreview from '@/components/ReactPreview';
import ChatWindow from '@/components/ChatWindow';
import { useProjectEditor } from '@/hooks/useProjectEditor';
import { Project } from '@/types/project.types';
import { api, ApiError } from '@/lib/api';
import { SelectedElement } from '@/types/chat.types';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
import Link from 'next/link';

export default function ProjectEditorPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;
  const [showPublishModal, setShowPublishModal] = useState(false);
  const [deploymentUrl, setDeploymentUrl] = useState<string | null>(null);
  const [isPublished, setIsPublished] = useState(false);

  // React project state
  const [reactActiveTab, setReactActiveTab] = useState<'code' | 'preview'>('code');
  const [reactFiles, setReactFiles] = useState<Record<string, string>>({});
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isBuilding, setIsBuilding] = useState(false);
  const [buildError, setBuildError] = useState<string | null>(null);

  // Chat and selector state
  const [selectedElement, setSelectedElement] = useState<SelectedElement | null>(null);
  const [selectorEnabled, setSelectorEnabled] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  // Keyboard shortcuts for React editor
  const chatInputRef = useRef<HTMLTextAreaElement>(null);

  useKeyboardShortcuts({
    onToggleSelector: () => {
      if ((project as any)?.project_type === 'react') {
        setSelectorEnabled(prev => !prev);
      }
    },
    onClearSelection: () => {
      setSelectedElement(null);
      setSelectorEnabled(false);
    },
    onFocusChat: () => {
      chatInputRef.current?.focus();
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
      console.error('Failed to load project:', error);
      throw error;
    }
  }, []);

  // Save project to API
  const saveProject = useCallback(async (data: { html_content: string; css_content: string; js_content: string }) => {
    try {
      await api.projects.update(projectId, data);
    } catch (error) {
      console.error('Failed to save project:', error);
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
      console.error('Failed to download React project:', error);
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
    } catch (error) {
      console.error('Failed to load React files:', error);
    }
  }, [projectId]);

  // Build preview
  const buildPreview = useCallback(async () => {
    setIsBuilding(true);
    setBuildError(null);
    try {
      const result = await api.generation.createPreview(projectId);
      console.log("result", result);
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
  useEffect(() => {
    if (reactActiveTab === 'preview' && !previewUrl && !isBuilding) {
      buildPreview();
    }
  }, [reactActiveTab, previewUrl, isBuilding, buildPreview]);

  // Handle edit submission from chat window
  const handleEditSubmit = useCallback(async (prompt: string) => {
    if (!selectedElement) {
      throw new Error('No element selected');
    }

    setIsProcessing(true);
    try {
      const result = await api.generation.editComponent(projectId, {
        selected_element: selectedElement,
        instruction: prompt,
      });

      if (result.success) {
        // Rebuild preview to show changes
        await buildPreview();

        // Clear selection after successful edit
        setSelectedElement(null);
        setSelectorEnabled(false);
      } else {
        throw new Error(result.message || 'Failed to apply changes');
      }
    } catch (error: any) {
      console.error('Edit failed:', error);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, [selectedElement, projectId, buildPreview]);

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
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <p className="text-red-600 text-lg mb-4">{error}</p>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Back to Dashboard
          </button>
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
          {/* Left Panel - Chat Window (1/4) */}
          <div className="w-1/4 flex flex-col bg-gray-900 border-r border-gray-700">
            <ChatWindow
              projectId={projectId}
              selectedElement={selectedElement}
              onSelectedElementChange={setSelectedElement}
              onSelectorModeChange={setSelectorEnabled}
              selectorEnabled={selectorEnabled}
              onEditSubmit={handleEditSubmit}
              isProcessing={isProcessing}
              inputRef={chatInputRef}
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

