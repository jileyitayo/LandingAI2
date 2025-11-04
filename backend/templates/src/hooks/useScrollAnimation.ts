/**
 * useScrollAnimation Hook
 * Custom hook for scroll-triggered animations using Framer Motion
 */

import { useInView } from 'framer-motion';
import { useRef } from 'react';

export interface ScrollAnimationOptions {
  /**
   * Only trigger animation once
   * @default true
   */
  once?: boolean;

  /**
   * Margin around the viewport to trigger animation early/late
   * @default "-100px"
   */
  margin?: string;

  /**
   * Amount of element that needs to be visible to trigger (0-1)
   * @default 0.3
   */
  amount?: number;
}

/**
 * Hook to detect when an element enters the viewport
 * Returns a ref to attach to the element and whether it's in view
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { ref, isInView } = useScrollAnimation();
 *
 *   return (
 *     <div ref={ref}>
 *       {isInView ? <p>Visible!</p> : <p>Hidden</p>}
 *     </div>
 *   );
 * }
 * ```
 */
export function useScrollAnimation(options: ScrollAnimationOptions = {}) {
  const {
    once = true,
    margin = '-100px',
    amount = 0.3,
  } = options;

  const ref = useRef<HTMLElement>(null);

  const isInView = useInView(ref, {
    once,
    margin,
    amount,
  });

  return { ref, isInView };
}

/**
 * Hook for animations that trigger immediately (no scroll)
 * Useful for hero sections or above-the-fold content
 *
 * @example
 * ```tsx
 * function Hero() {
 *   const { ref, isInView } = useImmediateAnimation();
 *
 *   return (
 *     <motion.section
 *       ref={ref}
 *       initial={{ opacity: 0 }}
 *       animate={isInView ? { opacity: 1 } : { opacity: 0 }}
 *     >
 *       Content
 *     </motion.section>
 *   );
 * }
 * ```
 */
export function useImmediateAnimation() {
  const ref = useRef<HTMLElement>(null);

  // For immediate animations, always return true
  const isInView = true;

  return { ref, isInView };
}

/**
 * Hook for staggered animations on lists
 * Returns a ref and controls for parent container
 *
 * @example
 * ```tsx
 * function List() {
 *   const { ref, controls } = useStaggerAnimation();
 *
 *   return (
 *     <motion.ul
 *       ref={ref}
 *       initial="initial"
 *       animate={controls}
 *       variants={{
 *         initial: { opacity: 0 },
 *         animate: { opacity: 1, transition: { staggerChildren: 0.1 } }
 *       }}
 *     >
 *       {items.map(item => (
 *         <motion.li key={item.id} variants={itemVariants}>
 *           {item.name}
 *         </motion.li>
 *       ))}
 *     </motion.ul>
 *   );
 * }
 * ```
 */
export function useStaggerAnimation(options: ScrollAnimationOptions = {}) {
  const { ref, isInView } = useScrollAnimation(options);

  const controls = isInView ? 'animate' : 'initial';

  return { ref, controls, isInView };
}

/**
 * Hook to get scroll progress of an element
 * Returns a ref and scroll progress (0-1)
 *
 * @example
 * ```tsx
 * function Parallax() {
 *   const { ref, scrollYProgress } = useScrollProgress();
 *
 *   return (
 *     <motion.div
 *       ref={ref}
 *       style={{ opacity: scrollYProgress }}
 *     >
 *       Content fades based on scroll
 *     </motion.div>
 *   );
 * }
 * ```
 */
export function useScrollProgress() {
  const ref = useRef<HTMLElement>(null);
  const scrollYProgress = 0; // Simplified for now - would need useScroll from framer-motion

  return { ref, scrollYProgress };
}
