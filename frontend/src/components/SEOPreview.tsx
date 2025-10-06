'use client';

interface SEOPreviewProps {
  title: string;
  description: string;
  subdomain: string;
}

export default function SEOPreview({ title, description, subdomain }: SEOPreviewProps) {
  const displayTitle = title || 'Your Website Title';
  const displayDescription = description || 'Your website description will appear here';
  const displayUrl = subdomain ? `${subdomain}.sitesmith.app` : 'yoursite.sitesmith.app';

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-medium text-gray-700">SEO Preview</h3>
      
      {/* Google Search Result Preview */}
      <div className="border border-gray-200 rounded-lg p-4 bg-white">
        <div className="space-y-1">
          {/* URL */}
          <div className="flex items-center space-x-1 text-sm">
            <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
              <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
            </svg>
            <span className="text-green-700">https://{displayUrl}</span>
          </div>
          
          {/* Title */}
          <div className="text-xl text-blue-600 hover:underline cursor-pointer">
            {displayTitle}
          </div>
          
          {/* Description */}
          <div className="text-sm text-gray-600 leading-snug">
            {displayDescription}
          </div>
        </div>
      </div>

      {/* Character counts */}
      <div className="grid grid-cols-2 gap-4 text-xs">
        <div>
          <span className="text-gray-600">Title: </span>
          <span className={title.length > 60 ? 'text-red-600 font-medium' : 'text-gray-900'}>
            {title.length}/60
          </span>
          {title.length > 60 && (
            <span className="block text-red-600 mt-1">Title is too long</span>
          )}
        </div>
        <div>
          <span className="text-gray-600">Description: </span>
          <span className={description.length > 160 ? 'text-red-600 font-medium' : 'text-gray-900'}>
            {description.length}/160
          </span>
          {description.length > 160 && (
            <span className="block text-red-600 mt-1">Description is too long</span>
          )}
        </div>
      </div>

      {/* SEO Tips */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-3 text-sm">
        <div className="flex">
          <svg className="w-5 h-5 text-blue-500 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          <div className="text-blue-800">
            <p className="font-medium mb-1">SEO Tips:</p>
            <ul className="list-disc list-inside space-y-1 text-xs">
              <li>Keep titles under 60 characters for optimal display</li>
              <li>Keep descriptions under 160 characters</li>
              <li>Include relevant keywords naturally</li>
              <li>Make it compelling to increase click-through rates</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

