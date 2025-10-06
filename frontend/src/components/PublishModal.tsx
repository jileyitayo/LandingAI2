'use client';

import { useState } from 'react';
import { X, ExternalLink, Copy, Check, Twitter, Facebook, Linkedin, Mail, Sparkles, Rocket } from 'lucide-react';

interface PublishModalProps {
  isOpen: boolean;
  onClose: () => void;
  deploymentUrl: string;
  projectName: string;
}

export default function PublishModal({
  isOpen,
  onClose,
  deploymentUrl,
  projectName,
}: PublishModalProps) {
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(deploymentUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleShare = (platform: 'twitter' | 'facebook' | 'linkedin' | 'email') => {
    const text = `Check out my new website: ${projectName}`;
    const url = encodeURIComponent(deploymentUrl);
    
    const shareUrls = {
      twitter: `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${url}`,
      facebook: `https://www.facebook.com/sharer/sharer.php?u=${url}`,
      linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${url}`,
      email: `mailto:?subject=${encodeURIComponent(projectName)}&body=${encodeURIComponent(`${text}\n\n${deploymentUrl}`)}`,
    };

    window.open(shareUrls[platform], '_blank', 'width=600,height=400');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fadeIn">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-gradient-to-br from-white to-blue-50 rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden animate-slideUp">
        {/* Confetti Background Effect */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-10 left-10 w-20 h-20 bg-yellow-400 rounded-full animate-float" style={{ animationDelay: '0s' }} />
          <div className="absolute top-20 right-20 w-16 h-16 bg-pink-400 rounded-full animate-float" style={{ animationDelay: '0.5s' }} />
          <div className="absolute bottom-20 left-20 w-12 h-12 bg-purple-400 rounded-full animate-float" style={{ animationDelay: '1s' }} />
          <div className="absolute bottom-10 right-10 w-14 h-14 bg-green-400 rounded-full animate-float" style={{ animationDelay: '1.5s' }} />
        </div>

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors z-10"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Content */}
        <div className="relative p-8">
          {/* Success Icon */}
          <div className="flex justify-center mb-6">
            <div className="relative">
              <div className="w-24 h-24 bg-gradient-to-br from-green-400 to-emerald-500 rounded-full flex items-center justify-center animate-bounce-in shadow-lg">
                <Rocket className="w-12 h-12 text-white" />
              </div>
              <div className="absolute -top-2 -right-2 w-8 h-8 bg-yellow-400 rounded-full flex items-center justify-center animate-spin-slow">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
            </div>
          </div>

          {/* Title */}
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-2">
            🎉 Congratulations!
          </h2>
          <p className="text-center text-gray-600 mb-6">
            Your website is now live and ready to share with the world!
          </p>

          {/* Project Name */}
          <div className="bg-white rounded-lg p-4 mb-6 shadow-sm border border-gray-200">
            <p className="text-sm text-gray-500 mb-1">Project Name</p>
            <p className="text-lg font-semibold text-gray-900">{projectName}</p>
          </div>

          {/* Deployment URL */}
          <div className="bg-white rounded-lg p-4 mb-6 shadow-sm border border-gray-200">
            <p className="text-sm text-gray-500 mb-2">Your Live URL</p>
            <div className="flex items-center gap-2">
              <a
                href={deploymentUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 text-blue-600 hover:text-blue-700 font-medium truncate transition-colors"
              >
                {deploymentUrl}
              </a>
              <button
                onClick={handleCopyLink}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                title="Copy link"
              >
                {copied ? (
                  <Check className="w-5 h-5 text-green-600" />
                ) : (
                  <Copy className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>

          {/* Preview Button */}
          <a
            href={deploymentUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl mb-6"
          >
            <ExternalLink className="w-5 h-5" />
            <span>View Live Site</span>
          </a>

          {/* Share Section */}
          <div className="border-t border-gray-200 pt-6">
            <p className="text-sm font-medium text-gray-700 mb-3 text-center">
              Share your success
            </p>
            <div className="flex items-center justify-center gap-3">
              <button
                onClick={() => handleShare('twitter')}
                className="p-3 text-white bg-[#1DA1F2] hover:bg-[#1a8cd8] rounded-lg transition-colors"
                title="Share on Twitter"
              >
                <Twitter className="w-5 h-5" />
              </button>
              <button
                onClick={() => handleShare('facebook')}
                className="p-3 text-white bg-[#1877F2] hover:bg-[#165ed4] rounded-lg transition-colors"
                title="Share on Facebook"
              >
                <Facebook className="w-5 h-5" />
              </button>
              <button
                onClick={() => handleShare('linkedin')}
                className="p-3 text-white bg-[#0A66C2] hover:bg-[#084d91] rounded-lg transition-colors"
                title="Share on LinkedIn"
              >
                <Linkedin className="w-5 h-5" />
              </button>
              <button
                onClick={() => handleShare('email')}
                className="p-3 text-white bg-gray-600 hover:bg-gray-700 rounded-lg transition-colors"
                title="Share via Email"
              >
                <Mail className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @keyframes bounceIn {
          0% {
            opacity: 0;
            transform: scale(0.3);
          }
          50% {
            opacity: 1;
            transform: scale(1.05);
          }
          70% {
            transform: scale(0.9);
          }
          100% {
            transform: scale(1);
          }
        }
        @keyframes float {
          0%, 100% {
            transform: translateY(0px);
          }
          50% {
            transform: translateY(-20px);
          }
        }
        @keyframes spinSlow {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }
        .animate-fadeIn {
          animation: fadeIn 0.2s ease-out;
        }
        .animate-slideUp {
          animation: slideUp 0.3s ease-out;
        }
        .animate-bounce-in {
          animation: bounceIn 0.6s ease-out;
        }
        .animate-float {
          animation: float 3s ease-in-out infinite;
        }
        .animate-spin-slow {
          animation: spinSlow 4s linear infinite;
        }
      `}</style>
    </div>
  );
}

