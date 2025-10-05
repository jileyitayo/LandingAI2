'use client';

import { useParams, useRouter } from 'next/navigation';
import { useCallback } from 'react';
import { ArrowLeft, Save, Download, Eye, Code, FileText } from 'lucide-react';
import WebsitePreview from '@/components/WebsitePreview';
import { useProjectEditor } from '@/hooks/useProjectEditor';
import { Project } from '@/types/project.types';
import { api } from '@/lib/api';

export default function ProjectEditorPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  // Load project from API
  const loadProject = useCallback(async (id: string): Promise<Project> => {
    try {
      // const response = await api.projects.get(id);
      // return {
      //   id: response.id,
      //   name: response.name,
      //   html_content : response.html_content || '',
      //   css_content : response.css_content || '',
      //   js_content : response.js_content || '',
      //   user_id: response.user_id, // Not needed for editor
      //   created_at: response.created_at, // Not needed for editor
      //   updated_at: response.updated_at, // Not needed for editor 
      // };
      // Mock data for now
    return {
      id,
      name: 'My Website Project',
      html_content: '<div class="container">\n  <h1>Welcome to Your Website</h1>\n  <p>Start editing to see changes in real-time!</p>\n</div>',
      css_content: '.container {\n  max-width: 1200px;\n  margin: 0 auto;\n  padding: 2rem;\n  text-align: center;\n}\n\nh1 {\n  color: #2563eb;\n  font-size: 2.5rem;\n  margin-bottom: 1rem;\n}\n\np {\n  color: #6b7280;\n  font-size: 1.125rem;\n}',
      js_content: '// Add your JavaScript here\nconsole.log("Website loaded successfully!");',
      user_id: 'user-123',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
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

  const { html_content, css_content, js_content, activeTab, hasUnsavedChanges } = editorState;
  const currentCode = activeTab === 'html_content' ? html_content : activeTab === 'css_content' ? css_content : js_content;

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
          <div className="flex-1 overflow-hidden">
            <WebsitePreview
              html={html_content}
              css={css_content}
              js={js_content}
              isLoading={false}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

