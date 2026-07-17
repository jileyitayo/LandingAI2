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
        className="group relative aspect-[3/4] rounded-lg border-2 border-dashed border-border bg-card hover:border-brand/50 hover:bg-card-muted transition-all duration-200 flex flex-col items-center justify-center gap-3"
      >
        <div className="w-12 h-12 rounded-full bg-card-muted flex items-center justify-center group-hover:bg-brand/10 transition-colors">
          <svg
            className="w-6 h-6 text-muted group-hover:text-brand transition-colors"
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
        <span className="text-sm font-medium text-muted group-hover:text-brand transition-colors">
          {name}
        </span>
      </button>
    );
  }

  return (
    <button
      onClick={() => onSelect(id)}
      className="group relative aspect-[3/4] rounded-lg overflow-hidden border border-border bg-card hover:shadow-lg hover:border-brand/40 transition-all duration-200"
    >
      {/* Preview Image */}
      <div className="w-full h-full bg-gradient-to-br from-card-muted to-border relative overflow-hidden">
        {previewImage ? (
          <img
            src={previewImage}
            alt={name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <div className="text-center p-6">
              <div className="w-16 h-16 mx-auto mb-4 rounded-lg bg-gradient-to-br from-brand to-brand-2 flex items-center justify-center">
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
              <p className="text-sm text-muted font-medium">{name}</p>
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
          <span className="px-2 py-1 text-xs font-medium bg-card/90 backdrop-blur-sm text-fg rounded-md shadow-sm">
            {category}
          </span>
        )}

        {/* System/Custom Badge */}
        <span
          className={`px-2 py-1 text-xs font-medium rounded-md shadow-sm ml-auto ${
            isSystemTemplate
              ? "bg-brand/10 text-brand"
              : "bg-brand-2/10 text-brand-2"
          }`}
        >
          {isSystemTemplate ? "System" : "Custom"}
        </span>
      </div>

      {/* Bottom Info Bar */}
      <div className="absolute bottom-0 left-0 right-0 bg-card border-t border-border p-3">
        <h3 className="text-sm font-semibold text-fg truncate">
          {name}
        </h3>
        {description && (
          <p className="text-xs text-muted mt-0.5 truncate">{description}</p>
        )}
      </div>
    </button>
  );
}

