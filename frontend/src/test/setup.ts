import "@testing-library/jest-dom";

// jsdom under Node 22+ can leave the global `localStorage` undefined (Node ships
// its own experimental localStorage that shadows jsdom's). Provide a small
// in-memory shim so the API client's token storage works under test.
if (typeof globalThis.localStorage === "undefined") {
  const store = new Map<string, string>();
  const shim: Storage = {
    getItem: (k: string) => (store.has(k) ? (store.get(k) as string) : null),
    setItem: (k: string, v: string) => {
      store.set(k, String(v));
    },
    removeItem: (k: string) => {
      store.delete(k);
    },
    clear: () => {
      store.clear();
    },
    key: (i: number) => Array.from(store.keys())[i] ?? null,
    get length() {
      return store.size;
    },
  };
  globalThis.localStorage = shim;
}

// recharts' ResponsiveContainer relies on ResizeObserver, absent in jsdom.
if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof ResizeObserver;
}
