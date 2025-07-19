// jest.setup.js
import '@testing-library/jest-dom'

// Mock Next.js globals for API routes
import { TextEncoder, TextDecoder } from 'util'

// Polyfill Web API globals
global.TextEncoder = global.TextEncoder || TextEncoder
global.TextDecoder = global.TextDecoder || TextDecoder

// Node.js 18+ has built-in fetch, but some properties might be missing
// Mock URL and Headers for Jest environment
if (typeof global.URL === 'undefined') {
  global.URL = require('url').URL
}
if (typeof global.URLSearchParams === 'undefined') {
  global.URLSearchParams = require('url').URLSearchParams
}

// Mock NextRequest and NextResponse for API route tests
jest.mock('next/server', () => ({
  NextRequest: jest.fn().mockImplementation((url, options = {}) => ({
    url,
    method: options.method || 'GET',
    headers: new Map(),
    nextUrl: {
      searchParams: new URLSearchParams(new URL(url).search)
    },
    json: jest.fn().mockResolvedValue(options.body ? JSON.parse(options.body) : {}),
    text: jest.fn().mockResolvedValue(options.body || ''),
    body: options.body
  })),
  NextResponse: {
    json: jest.fn().mockImplementation((data, init = {}) => ({
      status: init.status || 200,
      json: jest.fn().mockResolvedValue(data),
      data
    }))
  }
}))

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      pathname: '/',
      query: {},
      asPath: '/',
    }
  },
  useSearchParams() {
    return new URLSearchParams()
  },
  usePathname() {
    return '/'
  },
}))

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}

// Suppress console errors in tests
const originalError = console.error
beforeAll(() => {
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Warning: ReactDOM.render') ||
       args[0].includes('Warning: An update to') ||
       args[0].includes('Warning: react-dom.development.js') ||
       args[0].includes('act(...)') ||
       args[0].includes('Unknown event handler property') ||
       args[0].includes('cannot be a descendant of'))
    ) {
      return
    }
    originalError.call(console, ...args)
  }
})

afterAll(() => {
  console.error = originalError
})

// Global test utilities
global.sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))