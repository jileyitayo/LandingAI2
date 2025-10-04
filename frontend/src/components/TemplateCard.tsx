"use client";

/**
 * TemplateCard.tsx
 *
 * This file contains the TemplateCard component, which is used to display a template card in the template generation modal.
 */


interface TemplateCardProps {
  id: string;
  name: string;
  description?: string;
  category?: string;
  previewImage?: string;
  isSystemTemplate?: boolean;
  onSelect: (templateId: string) => void;
  isBlank?: boolean;
}

export function TemplateCard({
  id,
  name,
  description,
  category,
  previewImage,
  isSystemTemplate = true,
  onSelect,
  isBlank = false,
}: TemplateCardProps) {
  if (isBlank) {
    return (
      <button
        onClick={() => onSelect(id)}
        className="group relative aspect-[3/4] rounded-lg border-2 border-dashed border-gray-300 bg-white hover:border-primary-400 hover:bg-gray-50 transition-all duration-200 flex flex-col items-center justify-center gap-3"
      >
        <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center group-hover:bg-primary-50 transition-colors">
          <svg
            className="w-6 h-6 text-gray-400 group-hover:text-primary-500 transition-colors"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
        </div>
        <span className="text-sm font-medium text-gray-600 group-hover:text-primary-700 transition-colors">
          {name}
        </span>
      </button>
    );
  }

  return (
    <button
      onClick={() => onSelect(id)}
      className="group relative aspect-[3/4] rounded-lg overflow-hidden border border-gray-200 bg-white hover:shadow-lg hover:border-primary-300 transition-all duration-200"
    >
      {/* Preview Image */}
      <div className="w-full h-full bg-gradient-to-br from-gray-100 to-gray-200 relative overflow-hidden">
        {previewImage ? (
          <img
            src={previewImage}
            alt={name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <div className="text-center p-6">
              <div className="w-16 h-16 mx-auto mb-4 rounded-lg bg-gradient-to-br from-primary-400 to-secondary-500 flex items-center justify-center">
                <svg
                  className="w-8 h-8 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z"
                  />
                </svg>
              </div>
              <p className="text-sm text-gray-500 font-medium">{name}</p>
            </div>
          </div>
        )}

        {/* Hover Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <div className="absolute bottom-0 left-0 right-0 p-4 text-white">
            <p className="text-sm font-medium">Use Template</p>
          </div>
        </div>
      </div>

      {/* Template Info */}
      <div className="absolute top-3 left-3 right-3 flex items-start justify-between">
        {/* Category Badge */}
        {category && (
          <span className="px-2 py-1 text-xs font-medium bg-white/90 backdrop-blur-sm text-gray-700 rounded-md shadow-sm">
            {category}
          </span>
        )}

        {/* System/Custom Badge */}
        <span
          className={`px-2 py-1 text-xs font-medium rounded-md shadow-sm ml-auto ${
            isSystemTemplate
              ? "bg-blue-100 text-blue-700"
              : "bg-purple-100 text-purple-700"
          }`}
        >
          {isSystemTemplate ? "System" : "Custom"}
        </span>
      </div>

      {/* Bottom Info Bar */}
      <div className="absolute bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-3">
        <h3 className="text-sm font-semibold text-gray-900 truncate">
          {name}
        </h3>
        {description && (
          <p className="text-xs text-gray-500 mt-0.5 truncate">{description}</p>
        )}
      </div>
    </button>
  );
}

