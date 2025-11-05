'use client';

import { useState } from 'react';
import { Image as ImageIcon, Upload, Link as LinkIcon } from 'lucide-react';

interface ImageEditorProps {
  imageUrl?: string;
  imageAlt?: string;
  imageFit?: string;
  onImageUrlChange?: (value: string) => void;
  onImageAltChange?: (value: string) => void;
  onImageFitChange?: (value: string) => void;
}

const IMAGE_FIT_OPTIONS = [
  { value: 'object-cover', label: 'Cover' },
  { value: 'object-contain', label: 'Contain' },
  { value: 'object-fill', label: 'Fill' },
  { value: 'object-scale-down', label: 'Scale Down' },
  { value: 'object-none', label: 'None' },
];

export default function ImageEditor({
  imageUrl = '',
  imageAlt = '',
  imageFit = 'object-cover',
  onImageUrlChange,
  onImageAltChange,
  onImageFitChange,
}: ImageEditorProps) {
  const [urlInput, setUrlInput] = useState(imageUrl);

  return (
    <div className="space-y-4">
      {/* Current Image Preview */}
      {imageUrl && (
        <div className="aspect-video bg-gray-800 rounded-lg overflow-hidden border border-gray-700">
          <img
            src={imageUrl}
            alt={imageAlt}
            className={`w-full h-full ${imageFit}`}
          />
        </div>
      )}

      {/* Image URL Input */}
      {onImageUrlChange && (
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-xs font-medium text-gray-400">
            <LinkIcon className="w-3 h-3" />
            Image URL
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              placeholder="https://example.com/image.jpg"
              className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-300 focus:outline-none focus:border-blue-500"
            />
            <button
              onClick={() => onImageUrlChange(urlInput)}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
            >
              Apply
            </button>
          </div>
        </div>
      )}

      {/* Upload Button */}
      <button className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gray-800 hover:bg-gray-750 border border-gray-700 hover:border-gray-600 rounded transition-colors">
        <Upload className="w-4 h-4" />
        <span className="text-sm text-gray-300">Upload Image</span>
      </button>

      {/* Alt Text */}
      {onImageAltChange && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-400">Alt Text (Accessibility)</label>
          <input
            type="text"
            value={imageAlt}
            onChange={(e) => onImageAltChange(e.target.value)}
            placeholder="Describe the image"
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-300 focus:outline-none focus:border-blue-500"
          />
        </div>
      )}

      {/* Image Fit */}
      {onImageFitChange && (
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-xs font-medium text-gray-400">
            <ImageIcon className="w-3 h-3" />
            Object Fit
          </label>
          <div className="grid grid-cols-3 gap-2">
            {IMAGE_FIT_OPTIONS.map((fit) => (
              <button
                key={fit.value}
                onClick={() => onImageFitChange(fit.value)}
                className={`px-3 py-2 text-xs rounded border transition-colors ${
                  imageFit === fit.value
                    ? 'bg-blue-600 border-blue-500 text-white'
                    : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
                }`}
              >
                {fit.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

