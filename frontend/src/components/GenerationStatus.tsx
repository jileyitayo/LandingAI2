"use client";

/**
 * GenerationStatus Component
 * 
 * Displays real-time generation progress with animated progress bar,
 * stage-specific icons, and witty messages.
 */

import { useEffect, useState } from "react";
import { Coffee, Building2, Zap, FileText, Save, Sparkles, Loader2 } from "lucide-react";

interface GenerationStatusProps {
  status: string;
  progress?: number;
  stage?: string;
  stageMessage?: string;
  message?: string;
}

// Stage configuration with icons and messages
const STAGE_CONFIG: Record<string, { icon: typeof Coffee; messages: string[]; emoji: string }> = {
  analyzing: {
    icon: Coffee,
    messages: [
      "Brewing your perfect website...",
      "Analyzing your vision...",
      "Decoding your requirements...",
      "Understanding your needs...",
      "Processing your brilliant idea...",
    ],
    emoji: "☕",
  },
  generating_structure: {
    icon: Building2,
    messages: [
      "Architecting your digital masterpiece...",
      "Building the foundation...",
      "Designing the blueprint...",
      "Crafting the structure...",
      "Laying the groundwork...",
    ],
    emoji: "🏗️",
  },
  creating_components: {
    icon: Zap,
    messages: [
      "Summoning React components...",
      "Bringing components to life...",
      "Assembling the building blocks...",
      "Creating interactive elements...",
      "Weaving magic into components...",
    ],
    emoji: "⚛️",
  },
  building_pages: {
    icon: FileText,
    messages: [
      "Crafting beautiful pages...",
      "Building your pages...",
      "Assembling page layouts...",
      "Creating stunning pages...",
      "Putting pages together...",
    ],
    emoji: "📄",
  },
  saving_files: {
    icon: Save,
    messages: [
      "Saving everything safely...",
      "Securing your files...",
      "Storing your project...",
      "Backing up your work...",
      "Preserving your creation...",
    ],
    emoji: "💾",
  },
  finalizing: {
    icon: Sparkles,
    messages: [
      "Adding the finishing touches...",
      "Putting on the final polish...",
      "Almost there, just a moment...",
      "Applying the last details...",
      "Wrapping things up beautifully...",
    ],
    emoji: "✨",
  },
  completed: {
    icon: Sparkles,
    messages: [
      "Generation complete! Your website is ready...",
      "All done! Your website has been generated successfully...",
      "Success! Your website is ready to view and edit...",
      "Complete! Your website generation finished successfully...",
      "Done! Your website is ready for you to explore...",
    ],
    emoji: "🎉",
  },
};

export default function GenerationStatus({
  status,
  progress = 0,
  stage,
  stageMessage,
  message,
}: GenerationStatusProps) {
  const [displayedProgress, setDisplayedProgress] = useState(0);
  const [displayedMessage, setDisplayedMessage] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [selectedMessage, setSelectedMessage] = useState<string>("");

  // Debug logging
  useEffect(() => {
    // console.log('[GenerationStatus] Props updated:', {
    //   status,
    //   progress,
    //   stage,
    //   stageMessage,
    //   message,
    // });
  }, [status, progress, stage, stageMessage, message]);

  // Get current stage config and randomly select a message
  const currentStage = stage ? STAGE_CONFIG[stage] : undefined;
  const IconComponent = currentStage?.icon || Loader2;
  const emoji = currentStage?.emoji || "⚡";
  
  // Select random message when stage changes
  useEffect(() => {
    if (stage && STAGE_CONFIG[stage] && STAGE_CONFIG[stage].messages && STAGE_CONFIG[stage].messages.length > 0) {
      const randomIndex = Math.floor(Math.random() * STAGE_CONFIG[stage].messages.length);
      setSelectedMessage(STAGE_CONFIG[stage].messages[randomIndex]);
    } else {
      setSelectedMessage("");
    }
  }, [stage]);
  
  // Use selected message, fallback to stageMessage prop, then default
  const defaultMessage = selectedMessage || stageMessage || "Generating your website...";

  // Animate progress bar smoothly
  useEffect(() => {
    if (progress !== undefined) {
      const targetProgress = Math.min(Math.max(progress, 0), 100);
      const duration = 500; // Animation duration in ms
      const startProgress = displayedProgress;
      const startTime = Date.now();

      const animate = () => {
        const elapsed = Date.now() - startTime;
        const progressRatio = Math.min(elapsed / duration, 1);
        // Ease-out animation
        const easeOut = 1 - Math.pow(1 - progressRatio, 3);
        const currentProgress = startProgress + (targetProgress - startProgress) * easeOut;

        setDisplayedProgress(currentProgress);

        if (progressRatio < 1) {
          requestAnimationFrame(animate);
        } else {
          setDisplayedProgress(targetProgress);
        }
      };

      requestAnimationFrame(animate);
    }
  }, [progress]);

  // Typewriter effect for messages
  useEffect(() => {
    const messageToDisplay = defaultMessage;
    if (!messageToDisplay) return;

    setDisplayedMessage("");
    setIsTyping(true);

    let currentIndex = 0;
    const typingSpeed = 30; // milliseconds per character

    const typeChar = () => {
      if (currentIndex < messageToDisplay.length) {
        setDisplayedMessage(messageToDisplay.slice(0, currentIndex + 1));
        currentIndex++;
        setTimeout(typeChar, typingSpeed);
      } else {
        setIsTyping(false);
      }
    };

    const timeoutId = setTimeout(typeChar, 100);
    return () => clearTimeout(timeoutId);
  }, [defaultMessage, stage]);

  // Don't render if not generating
  if (status !== "generating") {
    return null;
  }

  return (
    <div className="max-w-4xl mx-auto mb-8">
      <div className="card glow-active p-6">
        {/* Header with icon and emoji */}
        <div className="flex items-start gap-4 mb-4">
          <div className="relative">
            {/* Rotating spinner background */}
            <div className="absolute inset-0 flex items-center justify-center">
              <IconComponent className="w-6 h-6 text-brand animate-spin" />
            </div>
            {/* Main icon */}
            <div className="relative bg-card rounded-full p-3 shadow-glow-sm">
              <IconComponent className="w-6 h-6 text-brand" />
            </div>
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="text-lg font-semibold text-fg">
                {displayedMessage || defaultMessage}
              </h3>
              <span className="text-2xl animate-bounce">{emoji}</span>
              {isTyping && (
                <span className="inline-block w-1 h-5 bg-brand animate-pulse ml-1">|</span>
              )}
            </div>

            {/* Progress bar */}
            <div className="w-full bg-card-muted rounded-full h-3 mb-2 overflow-hidden shadow-inner">
              <div
                className="h-full bg-brand-gradient rounded-full transition-all duration-500 ease-out relative overflow-hidden"
                style={{ width: `${displayedProgress}%` }}
              >
                {/* Shimmer effect */}
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-shimmer"></div>
              </div>
            </div>

            {/* Progress percentage */}
            <div className="flex items-center justify-between text-sm">
              <span className="text-brand font-medium">
                {Math.round(displayedProgress)}% complete
              </span>
              <span className="text-muted">
                {message || "This may take a few minutes"}
              </span>
            </div>
          </div>
        </div>

        {/* Stage indicator dots */}
        {stage && (
          <div className="flex items-center gap-2 mt-4 pt-4 border-t border-border">
            <span className="text-xs font-medium text-muted uppercase tracking-wide">
              Current Stage:
            </span>
            <div className="flex items-center gap-1.5">
              {Object.keys(STAGE_CONFIG).map((stageKey, index) => {
                const isActive = stageKey === stage;
                const isCompleted =
                  Object.keys(STAGE_CONFIG).indexOf(stage) >
                  Object.keys(STAGE_CONFIG).indexOf(stageKey);
                const stageConfig = STAGE_CONFIG[stageKey];
                const stageTitle = stageConfig.messages[0] || stageKey.replace(/_/g, " ");

                return (
                  <div
                    key={stageKey}
                    className={`rounded-full transition-all duration-300 ${
                      isActive
                        ? "glow-dot scale-125"
                        : isCompleted
                        ? "w-2 h-2 bg-brand/60"
                        : "w-2 h-2 bg-border"
                    }`}
                    title={stageTitle}
                  />
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

