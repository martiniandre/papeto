// react-aria (pulled in by Gluestack) probes window.screen.orientation in tests; RN's jest env has no window.screen.
if (typeof window !== 'undefined' && !window.screen) {
  window.screen = {};
}
