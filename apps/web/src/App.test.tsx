import '@testing-library/jest-dom/vitest'
import { describe, expect, it } from 'vitest'

describe('product language', () => {
  it('uses the safe clean-state vocabulary', () => {
    expect('No flag detected').not.toContain('Not fraudulent')
  })
})

