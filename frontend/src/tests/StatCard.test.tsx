import React from 'react'
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatCard } from '../components/ui/StatCard'
import { Users } from 'lucide-react'

describe('StatCard component', () => {
  it('renders title, value, and subtext correctly', () => {
    render(
      <StatCard
        title="Total Qualified Leads"
        value="48"
        icon={Users}
        subtext="From active campaigns"
      />
    )

    expect(screen.getByText('Total Qualified Leads')).toBeInTheDocument()
    expect(screen.getByText('48')).toBeInTheDocument()
    expect(screen.getByText('From active campaigns')).toBeInTheDocument()
  })

  it('renders positive trend badge when change is provided', () => {
    render(
      <StatCard
        title="Conversion Rate"
        value="14.2%"
        change="+2.4%"
        isPositive={true}
        icon={Users}
      />
    )

    expect(screen.getByText('+2.4%')).toBeInTheDocument()
  })
})
