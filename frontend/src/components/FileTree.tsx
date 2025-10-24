'use client';

import { useState, useMemo, memo } from 'react';
import { ChevronRight, ChevronDown, File, Folder, FolderOpen } from 'lucide-react';

interface FileTreeProps {
  files: Record<string, string>;
  selectedFile: string | null;
  onFileSelect: (path: string) => void;
}

interface TreeNode {
  name: string;
  type: 'file' | 'folder';
  children?: Record<string, TreeNode>;
  path: string;
}

function FileTree({ files, selectedFile, onFileSelect }: FileTreeProps) {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set(['src']));

  // Parse flat file list into tree structure - memoized to prevent recalculation
  const tree = useMemo(() => {
    const treeStructure: Record<string, TreeNode> = {};

    Object.keys(files).forEach(filePath => {
      const parts = filePath.split('/');
      let current = treeStructure;
      let currentPath = '';

      parts.forEach((part, index) => {
        currentPath = currentPath ? `${currentPath}/${part}` : part;

        if (!current[part]) {
          const isLast = index === parts.length - 1;
          current[part] = {
            name: part,
            type: isLast ? 'file' : 'folder',
            path: currentPath,
            children: isLast ? undefined : {}
          };
        }

        if (current[part].children) {
          current = current[part].children!;
        }
      });
    });

    return treeStructure;
  }, [files]);

  const toggleFolder = (path: string) => {
    setExpandedFolders(prev => {
      const newSet = new Set(prev);
      if (newSet.has(path)) {
        newSet.delete(path);
      } else {
        newSet.add(path);
      }
      return newSet;
    });
  };

  const getFileIcon = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    
    switch (extension) {
      case 'tsx':
      case 'jsx':
        return <File className="w-4 h-4 text-blue-400" />;
      case 'ts':
      case 'js':
        return <File className="w-4 h-4 text-yellow-400" />;
      case 'css':
        return <File className="w-4 h-4 text-pink-400" />;
      case 'json':
        return <File className="w-4 h-4 text-green-400" />;
      case 'html':
        return <File className="w-4 h-4 text-orange-400" />;
      default:
        return <File className="w-4 h-4 text-gray-400" />;
    }
  };

  const renderNode = (node: TreeNode, depth = 0) => {
    const isExpanded = expandedFolders.has(node.path);
    const isSelected = selectedFile === node.path;
    
    if (node.type === 'file') {
      return (
        <div
          key={node.path}
          className={`flex items-center gap-2 px-2 py-1 cursor-pointer hover:bg-gray-700 rounded ${
            isSelected ? 'bg-blue-600 text-white' : 'text-gray-300'
          }`}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
          onClick={() => onFileSelect(node.path)}
        >
          {getFileIcon(node.name)}
          <span className="text-sm">{node.name}</span>
        </div>
      );
    }

    return (
      <div key={node.path}>
        <div
          className="flex items-center gap-2 px-2 py-1 cursor-pointer hover:bg-gray-700 rounded text-gray-300"
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
          onClick={() => toggleFolder(node.path)}
        >
          {isExpanded ? (
            <ChevronDown className="w-4 h-4" />
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
          {isExpanded ? (
            <FolderOpen className="w-4 h-4 text-blue-400" />
          ) : (
            <Folder className="w-4 h-4 text-blue-400" />
          )}
          <span className="text-sm">{node.name}</span>
        </div>
        
        {isExpanded && node.children && (
          <div>
            {Object.values(node.children)
              .sort((a, b) => {
                // Folders first, then files, then alphabetically
                if (a.type !== b.type) {
                  return a.type === 'folder' ? -1 : 1;
                }
                return a.name.localeCompare(b.name);
              })
              .map(child => renderNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="h-full bg-gray-900 border-r border-gray-700 overflow-y-auto">
      <div className="p-2">
        <div className="text-xs text-gray-400 mb-2 font-medium">Project Files</div>
        {Object.values(tree)
          .sort((a, b) => {
            if (a.type !== b.type) {
              return a.type === 'folder' ? -1 : 1;
            }
            return a.name.localeCompare(b.name);
          })
          .map(node => renderNode(node))}
      </div>
    </div>
  );
}

// Export memoized version to prevent unnecessary re-renders
export default memo(FileTree);
