// Vitest global setup. Loaded once before all test files.
// - extends `expect` with @testing-library/jest-dom matchers
// - registers cleanup() so component trees are torn down between tests
//   (RTL >= 16 doesn't auto-cleanup in vitest like it did in jest)

import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

afterEach(() => {
  cleanup()
})
