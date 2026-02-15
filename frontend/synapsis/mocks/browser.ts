/**
 * Lightweight browser mock runtime.
 * Kept intentionally minimal until MSW adoption is required.
 */

let started = false;

export const mockBrowser = {
  start() {
    started = true;
  },
  stop() {
    started = false;
  },
  isStarted() {
    return started;
  },
};

