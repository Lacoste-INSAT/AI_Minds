/**
 * Lightweight test/server mock runtime.
 */

let listening = false;

export const mockServer = {
  listen() {
    listening = true;
  },
  close() {
    listening = false;
  },
  resetHandlers() {
    // Placeholder for compatibility with stricter mock servers.
  },
  isListening() {
    return listening;
  },
};

