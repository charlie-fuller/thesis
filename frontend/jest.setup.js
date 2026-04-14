import '@testing-library/jest-dom'

// Set up environment variables for API key auth
process.env.NEXT_PUBLIC_API_KEY = 'test-api-key'
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000'

// Mock react-markdown which uses ESM
jest.mock('react-markdown', () => {
  return function MockReactMarkdown({ children }) {
    return children
  }
})

// Mock remark-gfm
jest.mock('remark-gfm', () => {
  return function remarkGfm() {
    return function transformer() {}
  }
})

// Mock react-syntax-highlighter (ESM issues)
jest.mock('react-syntax-highlighter', () => ({
  Prism: function MockPrism({ children }) {
    return children
  },
  PrismLight: function MockPrismLight({ children }) {
    return children
  }
}))

jest.mock('react-syntax-highlighter/dist/cjs/styles/prism', () => ({
  oneDark: {},
  oneLight: {}
}))

jest.mock('react-syntax-highlighter/dist/esm/styles/prism', () => ({
  default: {},
  oneDark: {},
  oneLight: {}
}))
