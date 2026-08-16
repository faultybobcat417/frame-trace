import { describe, expect, it } from 'vitest'

describe('frontend fixture', () => {
  it('preserves the privacy-first product vocabulary', () => {
    const terms = ['PERSONAS', 'MEDIA', 'GRAPH', 'REVIEW', 'IMPORT']
    expect(terms).toContain('REVIEW')
    expect(terms).not.toContain('IDENTIFY')
  })
})
