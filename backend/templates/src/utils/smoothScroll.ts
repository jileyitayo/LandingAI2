/**
 * Smooth scroll utility for navigating to page sections
 * Handles hash-based navigation with smooth scrolling behavior
 */

/**
 * Smoothly scrolls to an element with the given ID
 * @param targetId - The ID of the element to scroll to (without the # prefix)
 * @param offset - Optional offset from the top in pixels (default: 80 for fixed headers)
 */
export const scrollToSection = (targetId: string, offset: number = 80): void => {
  const element = document.getElementById(targetId);
  
  if (element) {
    const elementPosition = element.getBoundingClientRect().top;
    const offsetPosition = elementPosition + window.pageYOffset - offset;

    window.scrollTo({
      top: offsetPosition,
      behavior: 'smooth'
    });
  }
};

/**
 * Handles click events for smooth scrolling navigation links
 * @param e - The click event
 * @param href - The href attribute (e.g., "/#features" or "#features")
 * @param onNavigate - Optional callback to execute after initiating scroll (e.g., closing mobile menu)
 */
export const handleSmoothScroll = (
  e: React.MouseEvent<HTMLAnchorElement>,
  href: string,
  onNavigate?: () => void
): void => {
  // Check if this is a hash link (internal navigation)
  if (href.startsWith('#') || href.includes('/#')) {
    e.preventDefault();
    
    // Extract the target ID from the href
    const targetId = href.replace(/^\/?#/, '');
    
    if (targetId) {
      scrollToSection(targetId);
      
      // Update URL hash without scrolling
      if (window.history.pushState) {
        window.history.pushState(null, '', `#${targetId}`);
      } else {
        window.location.hash = targetId;
      }
      
      // Execute callback (e.g., close mobile menu)
      onNavigate?.();
    }
  }
};

/**
 * Initialize smooth scrolling for all hash links on page load
 * Call this in your main component or App.tsx
 */
export const initializeSmoothScroll = (): void => {
  // Handle initial page load with hash
  const handleInitialHash = () => {
    const hash = window.location.hash;
    if (hash) {
      const targetId = hash.replace('#', '');
      // Small delay to ensure page has rendered
      setTimeout(() => {
        scrollToSection(targetId);
      }, 100);
    }
  };

  // Handle browser back/forward navigation
  window.addEventListener('hashchange', () => {
    const hash = window.location.hash;
    if (hash) {
      const targetId = hash.replace('#', '');
      scrollToSection(targetId);
    }
  });

  // Run on load
  if (document.readyState === 'complete') {
    handleInitialHash();
  } else {
    window.addEventListener('load', handleInitialHash);
  }
};

