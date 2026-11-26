import { describe, it, expect, vi } from 'vitest'
import { api, exportLeadsCSVUrl } from '../api/client'

describe('Frontend API Client Contract', () => {
  it('exposes all required API methods and aliases', () => {
    // Business Profile aliases
    expect(typeof api.getProfile).toBe('function')
    expect(typeof api.getBusinessProfile).toBe('function')
    expect(typeof api.saveProfile).toBe('function')
    expect(typeof api.saveBusinessProfile).toBe('function')

    // Content aliases
    expect(typeof api.getContent).toBe('function')
    expect(typeof api.getContentItems).toBe('function')

    // Analytics aliases
    expect(typeof api.getAnalytics).toBe('function')
    expect(typeof api.getAnalyticsOverview).toBe('function')

    // Leads & metrics
    expect(typeof api.getLeads).toBe('function')
    expect(typeof api.importLeadsCSV).toBe('function')
    expect(typeof api.getCampaignMetrics).toBe('function')
    expect(typeof api.importCampaignMetrics).toBe('function')

    // Standalone export helpers
    expect(typeof exportLeadsCSVUrl).toBe('function')
    expect(exportLeadsCSVUrl()).toContain('/leads/export')
  })
})
