/**
 * Animation Variants and Utilities
 * Reusable Framer Motion animation configurations
 */

import { Variants } from 'framer-motion';

/**
 * Entrance Animations
 * Used for immediate animations when component mounts
 */
export const fadeIn: Variants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
};

export const slideUp: Variants = {
  initial: { opacity: 0, y: 40 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: 40 },
};

export const slideInFromLeft: Variants = {
  initial: { opacity: 0, x: -30 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -30 },
};

export const slideInFromRight: Variants = {
  initial: { opacity: 0, x: 30 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 30 },
};

export const scaleIn: Variants = {
  initial: { opacity: 0, scale: 0.95 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.95 },
};

/**
 * Scroll Animations
 * Used with whileInView for scroll-triggered animations
 */
export const fadeInOnScroll: Variants = {
  initial: { opacity: 0, y: 40 },
  whileInView: { opacity: 1, y: 0 },
};

export const scaleOnScroll: Variants = {
  initial: { opacity: 0, scale: 0.9 },
  whileInView: { opacity: 1, scale: 1 },
};

export const slideUpOnScroll: Variants = {
  initial: { opacity: 0, y: 60 },
  whileInView: { opacity: 1, y: 0 },
};

/**
 * Stagger Animations
 * Used for lists and grids with staggered child animations
 */
export const staggerContainer: Variants = {
  initial: { opacity: 0 },
  animate: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

export const staggerItem: Variants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
};

/**
 * Transition Configurations
 */
export const transitions = {
  quick: { duration: 0.3, ease: 'easeOut' },
  smooth: { duration: 0.6, ease: 'easeInOut' },
  slow: { duration: 0.8, ease: 'easeInOut' },
  spring: { type: 'spring', stiffness: 100, damping: 15 },
  bounce: { type: 'spring', stiffness: 300, damping: 20 },
};

/**
 * Viewport Configuration
 * Common viewport settings for scroll animations
 */
export const viewportConfig = {
  once: true, // Animate only once
  margin: '-100px', // Trigger 100px before element enters viewport
  amount: 0.3, // Trigger when 30% of element is visible
};

/**
 * Helper function to create custom fade in animation with custom offset
 */
export const createFadeIn = (yOffset = 20, duration = 0.5): Variants => ({
  initial: { opacity: 0, y: yOffset },
  animate: { opacity: 1, y: 0, transition: { duration } },
});

/**
 * Helper function to create custom scroll animation
 */
export const createScrollAnimation = (
  yOffset = 40,
  duration = 0.6
): Variants => ({
  initial: { opacity: 0, y: yOffset },
  whileInView: { opacity: 1, y: 0, transition: { duration } },
});

/**
 * Hover Animations
 * Subtle hover effects for interactive elements
 */
export const hoverScale = {
  whileHover: { scale: 1.05 },
  whileTap: { scale: 0.95 },
};

export const hoverLift = {
  whileHover: { y: -5, transition: { duration: 0.2 } },
};

export const hoverBrightness = {
  whileHover: { filter: 'brightness(1.1)', transition: { duration: 0.2 } },
};

/**
 * Page Transition Animations
 */
export const pageTransition: Variants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
};

/**
 * Modal/Dialog Animations
 */
export const modalBackdrop: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
};

export const modalContent: Variants = {
  initial: { opacity: 0, scale: 0.95, y: 20 },
  animate: { opacity: 1, scale: 1, y: 0 },
  exit: { opacity: 0, scale: 0.95, y: 20 },
};

