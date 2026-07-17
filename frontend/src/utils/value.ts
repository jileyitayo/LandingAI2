/**
 * Utility functions for values and transformations
 */

/**
 * Generates a shimmer effect SVG for loading placeholders
 * @param w - Width of the shimmer SVG
 * @param h - Height of the shimmer SVG
 * @returns SVG string with shimmer animation
 */
export const shimmer = (w: number, h: number): string => `
<svg width="${w}" height="${h}" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
  <defs>
    <linearGradient id="g">
      <stop stop-color="#7c3aed" offset="20%" />
      <stop stop-color="#a78bfa" offset="50%" />
      <stop stop-color="#7c3aed" offset="70%" />
    </linearGradient>
  </defs>
  <rect width="${w}" height="${h}" fill="#7c3aed" />
  <rect id="r" width="${w}" height="${h}" fill="url(#g)" />
  <animate xlink:href="#r" attributeName="x" from="-${w}" to="${w}" dur="1s" repeatCount="indefinite"  />
</svg>`;

/**
 * Converts a string to base64 encoding
 * Works in both browser and Node.js environments
 * @param str - String to encode
 * @returns Base64 encoded string
 */
export const toBase64 = (str: string): string =>
  typeof window === 'undefined'
    ? Buffer.from(str).toString('base64')
    : window.btoa(str);
