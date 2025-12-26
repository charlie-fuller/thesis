'use client';

import { useState } from 'react';
import DesignVelocityCard from './DesignVelocityCard';
import ActivitySummaryCard from './ActivitySummaryCard';
import SystemsThinkingCard from './SystemsThinkingCard';

type TimePeriod = 'week' | 'month' | 'all_time';

export default function PersonalImpactDashboard() {
  const [timePeriod, setTimePeriod] = useState<TimePeriod>('month');

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
              My Impact Dashboard
            </h1>
            <p className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)' }}>
              Track your activity and project progress
            </p>
          </div>

          {/* Time Period Selector */}
          <div className="flex gap-1 p-1 rounded-lg border border-default bg-card">
            <button
              onClick={() => setTimePeriod('week')}
              className={`px-4 py-2 text-sm font-medium rounded transition-colors ${
                timePeriod === 'week'
                  ? 'bg-hover text-primary'
                  : 'text-secondary hover:text-primary hover:bg-hover/50'
              }`}
            >
              Week
            </button>
            <button
              onClick={() => setTimePeriod('month')}
              className={`px-4 py-2 text-sm font-medium rounded transition-colors ${
                timePeriod === 'month'
                  ? 'bg-hover text-primary'
                  : 'text-secondary hover:text-primary hover:bg-hover/50'
              }`}
            >
              Month
            </button>
            <button
              onClick={() => setTimePeriod('all_time')}
              className={`px-4 py-2 text-sm font-medium rounded transition-colors ${
                timePeriod === 'all_time'
                  ? 'bg-hover text-primary'
                  : 'text-secondary hover:text-primary hover:bg-hover/50'
              }`}
            >
              All Time
            </button>
          </div>
        </div>
      </div>

      {/* Dashboard Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Activity Summary */}
        <div className="col-span-1">
          <ActivitySummaryCard timePeriod={timePeriod} />
        </div>

        {/* Design Velocity */}
        <div className="col-span-1">
          <DesignVelocityCard timePeriod={timePeriod} />
        </div>

        {/* Learning Systems Thinking Score */}
        <div className="col-span-1">
          <SystemsThinkingCard timePeriod={timePeriod} />
        </div>
      </div>
    </div>
  );
}
