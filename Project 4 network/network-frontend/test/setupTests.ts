import "@testing-library/jest-dom";
import { cleanup } from "@testing-library/react";
import { afterEach, vi, beforeAll, afterAll } from "vitest";

// Clean up after each test
afterEach(() => {
  cleanup();
});

// Mock window.matchMedia for components that use it
window.matchMedia =
  window.matchMedia ||
  function () {
    return {
      matches: false,
      addListener: function () {},
      removeListener: function () {},
    };
  };

// Mock fetch API for components that use it
globalThis.fetch = vi.fn();

// Suppress console.error noise (optional)
const originalError = console.error;
beforeAll(() => {
  console.error = (...args) => {
    if (/Warning.*not wrapped in act/.test(args[0])) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});
