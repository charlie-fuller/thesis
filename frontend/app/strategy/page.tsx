'use client'

/**
 * Strategy Page
 *
 * Displays company objectives/goals and department KPIs.
 * Helps users understand how opportunities align with strategic priorities.
 */

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import PageHeader from '@/components/PageHeader'
import {
  Target,
  TrendingUp,
  TrendingDown,
  Minus,
  Building2,
  ChevronDown,
  ChevronRight,
  Pencil,
  Save,
  XCircle,
  Plus,
  Loader2,
  BarChart3,
  Users,
  DollarSign,
  Zap,
  Shield,
  Sparkles,
  Scale,
  Briefcase,
} from 'lucide-react'
import { apiGet, apiPost, apiPatch } from '@/lib/api'

// ============================================================================
// TYPES
// ============================================================================

interface CompanyObjective {
  id: string
  title: string
  description: string
  icon: string
  target_metric: string
  current_value: number | null
  target_value: number
  unit: string
  progress_percentage: number
  status: 'on_track' | 'at_risk' | 'behind' | 'achieved'
  priority: number
  updated_at: string
}

interface DepartmentKPI {
  id: string
  department: string
  kpi_name: string
  description: string
  current_value: number | null
  target_value: number
  unit: string
  trend: 'up' | 'down' | 'flat'
  trend_percentage: number
  status: 'green' | 'yellow' | 'red'
  linked_objective_id: string | null
  updated_at: string
}

// ============================================================================
// COMPANY DATA - FY26 Company Goals (Current Measurement)
// Source: FY2026 Company Goals - Revisited
// ============================================================================

const FY26_OBJECTIVES: CompanyObjective[] = [
  {
    id: '1',
    title: 'Market Positioning',
    description: 'Re-establish Contentful as a thought leader and disruptor in the broader DXP category, with a compelling near-term value proposition, and an expansive vision around content operations that co-opts the GenAI value proposition.',
    icon: 'Target',
    target_metric: 'DXP category leadership',
    current_value: null,
    target_value: 100,
    unit: '%',
    progress_percentage: 65,
    status: 'on_track',
    priority: 1,
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: '2',
    title: 'Sales Productivity',
    description: 'Accelerate sales productivity to approach industry benchmarks, exceed pipeline and bookings targets, and support increased S&M investment in H2 to re-accelerate revenue growth in FY27 and FY28.',
    icon: 'TrendingUp',
    target_metric: 'Pipeline vs target',
    current_value: 113,
    target_value: 100,
    unit: '%',
    progress_percentage: 100,
    status: 'achieved',
    priority: 2,
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: '3',
    title: 'Product Innovation',
    description: 'Accelerate velocity of new product and feature introductions that reinforce platform/ecosystem leadership, provide differentiated expansion into DXP category, and capture net new spend categories through GenAI capabilities.',
    icon: 'Sparkles',
    target_metric: 'EXO/GenAI milestones',
    current_value: 5,
    target_value: 8,
    unit: 'milestones',
    progress_percentage: 63,
    status: 'on_track',
    priority: 3,
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: '4',
    title: 'Culture',
    description: 'Create a winning culture based on transparency, empowerment, risk taking and performance. Values: Relentless Customer Focus, Own It, Be Bold, Win Together.',
    icon: 'Users',
    target_metric: 'Employee retention',
    current_value: 92,
    target_value: 98,
    unit: '%',
    progress_percentage: 67,
    status: 'on_track',
    priority: 4,
    updated_at: '2026-01-22T10:00:00Z',
  },
]

// ============================================================================
// COMPANY DATA - FY27 Company Goals (Forward-Looking / Notional)
// Source: FY'27 Company Goals slide
// ============================================================================

const FY27_OBJECTIVES: CompanyObjective[] = [
  {
    id: '1',
    title: 'Market Leadership',
    description: 'Transform perceptions of Contentful from a technical CMS tool for developers into a strategic solution partner for CMOs and CTOs. Create a differentiated narrative around our product vision that capitalizes on emerging AI disruptions and creates an aura of industry leadership.',
    icon: 'Target',
    target_metric: 'CMO/CTO perception shift',
    current_value: null,
    target_value: 100,
    unit: '%',
    progress_percentage: 0,
    status: 'on_track',
    priority: 1,
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: '2',
    title: 'Cost-Efficient GTM Growth',
    description: 'Build upon FY26 productivity improvements to exceed all FY top line targets, achieve a cost-to-book ratio under 2.0, and improve FY26 gross retention metrics.',
    icon: 'TrendingUp',
    target_metric: 'Cost-to-book ratio',
    current_value: null,
    target_value: 2.0,
    unit: 'ratio',
    progress_percentage: 0,
    status: 'on_track',
    priority: 2,
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: '3',
    title: 'Product Innovation',
    description: 'Introduce new platform and AI-powered experience orchestration capabilities that leapfrog the market. Democratize the value of experimentation, p13n, and content analytics. Develop a clear product strategy behind the agentic web.',
    icon: 'Sparkles',
    target_metric: 'EXO/Agentic Web milestones',
    current_value: null,
    target_value: 8,
    unit: 'milestones',
    progress_percentage: 0,
    status: 'on_track',
    priority: 3,
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: '4',
    title: 'Culture',
    description: 'Create a winning culture based on transparency, empowerment, risk taking and performance. Target: 98% employee retention.',
    icon: 'Users',
    target_metric: 'Employee retention',
    current_value: null,
    target_value: 98,
    unit: '%',
    progress_percentage: 0,
    status: 'on_track',
    priority: 4,
    updated_at: '2026-01-22T10:00:00Z',
  },
]

// Key Company Metrics (from All-Hands Dec 2025):
// - ARR: $239M | YoY ARR Growth: 30%
// - Q3 vs Board Plan: 113% | YoY Revenue Growth: 50%
// - Gross Retention: 91-92% (goal: 98%)
// - Employees: ~850 | Cash Balance: $97M
// - Largest Deal: Microsoft at $1.35M
// - Top 100 Accounts: 70 customers + 30 prospects

const MOCK_KPIS: DepartmentKPI[] = [
  // ============================================================================
  // LEGAL DEPARTMENT (Ashley Adams / Margo Smith)
  // Goal: Build "AI confident and agentic legal organization"
  // Supports: Sales Productivity (faster contracts), Product Innovation (GenAI)
  // ============================================================================
  {
    id: 'legal-1',
    department: 'Legal',
    kpi_name: 'Contract Review Cycle Time',
    description: 'Days from contract submission to completion (target: 90% reduction). Critical for enterprise deal velocity.',
    current_value: 19,
    target_value: 2,
    unit: 'days',
    trend: 'down',
    trend_percentage: 10,
    status: 'red',
    linked_objective_id: '2', // Sales Productivity
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: 'legal-2',
    department: 'Legal',
    kpi_name: 'Attorney Strategic Work Time',
    description: 'Time on high-value strategic work vs. admin (industry: 8% baseline). AI to handle routine reviews.',
    current_value: 20,
    target_value: 40,
    unit: '%',
    trend: 'up',
    trend_percentage: 5,
    status: 'yellow',
    linked_objective_id: '3', // Product Innovation (GenAI)
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: 'legal-3',
    department: 'Legal',
    kpi_name: 'Jira Ticket Deflection',
    description: 'Legal help desk tickets resolved via self-service (1,500+ tickets/year baseline). AI agent deployment.',
    current_value: 15,
    target_value: 40,
    unit: '%',
    trend: 'up',
    trend_percentage: 8,
    status: 'yellow',
    linked_objective_id: '3', // Product Innovation (GenAI)
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: 'legal-4',
    department: 'Legal',
    kpi_name: 'Vendor Onboarding Cycle',
    description: 'Time to onboard new vendors through legal review. Blockers for enterprise partnerships.',
    current_value: 6,
    target_value: 2,
    unit: 'months',
    trend: 'flat',
    trend_percentage: 0,
    status: 'red',
    linked_objective_id: '2', // Sales Productivity
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: 'legal-5',
    department: 'Legal',
    kpi_name: 'AI Fluency Score',
    description: 'Legal team demonstrating AI confidence (Shift Happens workshop pilot). Building agentic legal org.',
    current_value: 25,
    target_value: 100,
    unit: '%',
    trend: 'up',
    trend_percentage: 10,
    status: 'yellow',
    linked_objective_id: '4', // Culture
    updated_at: '2026-01-22T10:00:00Z',
  },
  // ============================================================================
  // FINANCE DEPARTMENT (Raul Rivera)
  // Focus: IPO readiness, automation, SOX compliance
  // Supports: Sales Productivity (S&M investment), Product Innovation (GenAI)
  // ============================================================================
  {
    id: 'fin-1',
    department: 'Finance',
    kpi_name: 'Monthly Close Cycle',
    description: 'Days to complete monthly financial close (target: 47% reduction). IPO readiness critical.',
    current_value: 15,
    target_value: 8,
    unit: 'days',
    trend: 'down',
    trend_percentage: 10,
    status: 'yellow',
    linked_objective_id: '2', // Sales Productivity (supports S&M investment)
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: 'fin-2',
    department: 'Finance',
    kpi_name: 'Invoice Processing Time',
    description: 'Minutes per invoice (target: 80% reduction via AI OCR). AP automation pilot.',
    current_value: 15,
    target_value: 3,
    unit: 'min/invoice',
    trend: 'down',
    trend_percentage: 15,
    status: 'yellow',
    linked_objective_id: '3', // Product Innovation (GenAI capabilities)
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: 'fin-3',
    department: 'Finance',
    kpi_name: 'Payroll Corrections',
    description: 'Annual payroll corrections requiring manual intervention. Target: near-zero.',
    current_value: 300,
    target_value: 30,
    unit: '/year',
    trend: 'down',
    trend_percentage: 20,
    status: 'red',
    linked_objective_id: '2', // Sales Productivity (efficiency)
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: 'fin-4',
    department: 'Finance',
    kpi_name: 'Manual Report Generation',
    description: 'Payroll reports requiring manual compilation. FP&A automation opportunity.',
    current_value: 50,
    target_value: 10,
    unit: 'reports',
    trend: 'down',
    trend_percentage: 10,
    status: 'yellow',
    linked_objective_id: '3', // Product Innovation (GenAI)
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: 'fin-5',
    department: 'Finance',
    kpi_name: 'SaaS Spend Visibility',
    description: 'SaaS tools tracked with renewal alerts. Cost control for S&M investment.',
    current_value: 45,
    target_value: 100,
    unit: '%',
    trend: 'up',
    trend_percentage: 15,
    status: 'yellow',
    linked_objective_id: '2', // Sales Productivity
    updated_at: '2026-01-22T10:00:00Z',
  },
  // ============================================================================
  // HR / PEOPLE (Chad Meek, Bella Thomas, Hanna Stacey)
  // Focus: AI-powered talent, employee experience, 98% retention
  // Supports: Culture & Retention, Cost-Efficient GTM Growth
  // ============================================================================
  {
    id: 'hr-1',
    department: 'HR/People',
    kpi_name: 'Job Description Creation Time',
    description: 'Time to create bias-free, compliant JDs. Critical for GTM hiring velocity.',
    current_value: 210,
    target_value: 30,
    unit: 'min',
    trend: 'down',
    trend_percentage: 25,
    status: 'yellow',
    linked_objective_id: '3', // Cost-Efficient GTM Growth
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: 'hr-2',
    department: 'HR/People',
    kpi_name: 'HR Ticket Deflection',
    description: 'Benefits/policy questions resolved via AI chatbot. Building Nelson Harris check-in agent.',
    current_value: 10,
    target_value: 40,
    unit: '%',
    trend: 'up',
    trend_percentage: 5,
    status: 'yellow',
    linked_objective_id: '4', // Product Innovation & AI
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: 'hr-3',
    department: 'HR/People',
    kpi_name: 'Employee Retention Rate',
    description: 'Annual employee retention. Direct company FY27 priority: 98% target.',
    current_value: 92,
    target_value: 98,
    unit: '%',
    trend: 'up',
    trend_percentage: 2,
    status: 'yellow',
    linked_objective_id: '5', // Culture & Retention
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: 'hr-4',
    department: 'HR/People',
    kpi_name: 'Time to Post',
    description: 'Days from hiring manager request to live job posting. Field capacity scaling.',
    current_value: 5,
    target_value: 1,
    unit: 'days',
    trend: 'down',
    trend_percentage: 15,
    status: 'yellow',
    linked_objective_id: '3', // Cost-Efficient GTM Growth
    updated_at: '2026-01-22T10:00:00Z',
  },
  // ============================================================================
  // IT / INFORMATION SERVICES (Danny Leal, Tyler Stitt)
  // Focus: Digital workforce, agent quality, platform adoption
  // Supports: Product Innovation & AI, EXO platform readiness
  // ============================================================================
  {
    id: 'it-1',
    department: 'IT',
    kpi_name: 'AI Agent Success Rate',
    description: 'Built agents reaching production (15/350 baseline). Quality over quantity.',
    current_value: 4,
    target_value: 80,
    unit: '%',
    trend: 'up',
    trend_percentage: 5,
    status: 'red',
    linked_objective_id: '4', // Product Innovation & AI
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: 'it-2',
    department: 'IT',
    kpi_name: 'Production Agents',
    description: 'AI agents deployed to production. Glean platform enablement.',
    current_value: 15,
    target_value: 50,
    unit: 'agents',
    trend: 'up',
    trend_percentage: 10,
    status: 'yellow',
    linked_objective_id: '4', // Product Innovation & AI
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: 'it-3',
    department: 'IT',
    kpi_name: 'Self-Service Resolution Rate',
    description: 'IT issues resolved via self-service. Supports field capacity scaling.',
    current_value: 45,
    target_value: 80,
    unit: '%',
    trend: 'up',
    trend_percentage: 8,
    status: 'yellow',
    linked_objective_id: '3', // Cost-Efficient GTM Growth
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: 'it-4',
    department: 'IT',
    kpi_name: 'Zero Friction Lifecycle',
    description: 'Onboarding/offboarding issues. Employee experience and retention.',
    current_value: 15,
    target_value: 0,
    unit: 'issues/mo',
    trend: 'down',
    trend_percentage: 20,
    status: 'yellow',
    linked_objective_id: '5', // Culture & Retention
    updated_at: '2026-01-22T10:00:00Z',
  },
  // ============================================================================
  // DATA TEAM
  // Focus: Insight 360, data governance, content intelligence layer
  // Supports: Product Innovation & AI (content intelligence), EXO
  // ============================================================================
  {
    id: 'data-1',
    department: 'Data',
    kpi_name: 'Insight 360 Sources Migrated',
    description: 'Priority data sources migrated to Snowflake. Foundation for content intelligence.',
    current_value: 0,
    target_value: 100,
    unit: 'sources',
    trend: 'flat',
    trend_percentage: 0,
    status: 'yellow',
    linked_objective_id: '4', // Product Innovation & AI
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: 'data-2',
    department: 'Data',
    kpi_name: 'Data Governance Council Active',
    description: 'Data Governance Council launched. Enables AI and analytics initiatives.',
    current_value: 0,
    target_value: 1,
    unit: 'council',
    trend: 'flat',
    trend_percentage: 0,
    status: 'yellow',
    linked_objective_id: '4', // Product Innovation & AI
    updated_at: '2026-01-22T10:00:00Z',
  },
  // ============================================================================
  // REVENUE OPERATIONS (Caroline Knetsch)
  // Focus: Sales enablement, self-service, MEDDIC/Command of Message
  // Supports: Enterprise Adoption, Cost-Efficient GTM Growth
  // ============================================================================
  {
    id: 'revops-1',
    department: 'Revenue Ops',
    kpi_name: 'Ticket Escalation Rate',
    description: 'Sales questions requiring human escalation. AI deflection target.',
    current_value: 75,
    target_value: 25,
    unit: '%',
    trend: 'down',
    trend_percentage: 5,
    status: 'red',
    linked_objective_id: '3', // Cost-Efficient GTM Growth
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: 'revops-2',
    department: 'Revenue Ops',
    kpi_name: 'MEDDIC Field Completion',
    description: 'Opportunities with complete MEDDIC data. Value selling framework enablement.',
    current_value: 60,
    target_value: 90,
    unit: '%',
    trend: 'up',
    trend_percentage: 10,
    status: 'yellow',
    linked_objective_id: '1', // Enterprise Adoption
    updated_at: '2026-01-22T10:00:00Z',
  },
  // ============================================================================
  // BUSINESS SYSTEMS
  // Focus: Customer journey, Top 100 account planning, enterprise adoption
  // Supports: Wall-to-Wall Enterprise Adoption (primary)
  // ============================================================================
  {
    id: 'biz-1',
    department: 'Business Systems',
    kpi_name: 'Strategic Account Planning Coverage',
    description: 'Top 100 accounts with standardized plans. Q4 initiative rolled out.',
    current_value: 25,
    target_value: 100,
    unit: '%',
    trend: 'up',
    trend_percentage: 15,
    status: 'yellow',
    linked_objective_id: '1', // Enterprise Adoption
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: 'biz-2',
    department: 'Business Systems',
    kpi_name: 'Products Sold/Usage Visibility',
    description: 'Visibility into customer bought vs. usage. White space identification.',
    current_value: 30,
    target_value: 100,
    unit: '%',
    trend: 'up',
    trend_percentage: 10,
    status: 'red',
    linked_objective_id: '1', // Enterprise Adoption
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: 'biz-3',
    department: 'Business Systems',
    kpi_name: 'Customer Lifecycle Automation',
    description: 'Automated workflows for retention (91-92% → 98% GRR) and expansion.',
    current_value: 20,
    target_value: 70,
    unit: '%',
    trend: 'up',
    trend_percentage: 5,
    status: 'yellow',
    linked_objective_id: '1', // Enterprise Adoption
    updated_at: '2026-01-22T10:00:00Z',
  },
  // ============================================================================
  // PSA/PM TEAM
  // Focus: Project governance, EXO readiness, cross-functional programs
  // Supports: EXO initiative, Culture (stakeholder alignment)
  // ============================================================================
  {
    id: 'psa-1',
    department: 'PSA/PM',
    kpi_name: 'BRD Completion Rate',
    description: 'Projects with complete BRDs. EXO cross-functional workstreams.',
    current_value: 60,
    target_value: 100,
    unit: '%',
    trend: 'up',
    trend_percentage: 20,
    status: 'yellow',
    linked_objective_id: '2', // EXO
    updated_at: '2026-01-22T10:00:00Z',
  },
  {
    id: 'psa-2',
    department: 'PSA/PM',
    kpi_name: 'Executive Sponsor Alignment',
    description: 'Projects with exec sponsor. Top 15 accounts get ELT sponsorship.',
    current_value: 75,
    target_value: 100,
    unit: '%',
    trend: 'up',
    trend_percentage: 10,
    status: 'yellow',
    linked_objective_id: '1', // Enterprise Adoption
    updated_at: '2026-01-22T10:00:00Z',
  },
]

// ============================================================================
// HELPER COMPONENTS
// ============================================================================

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  Sparkles,
  DollarSign,
  Users,
  Building2,
  Shield,
  Zap,
  BarChart3,
  Target,
  TrendingUp,
  Scale,
  Briefcase,
}

function ObjectiveIcon({ name, className }: { name: string; className?: string }) {
  const Icon = ICON_MAP[name] || Target
  return <Icon className={className} />
}

function StatusBadge({ status }: { status: CompanyObjective['status'] }) {
  const config = {
    on_track: { label: 'On Track', color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' },
    at_risk: { label: 'At Risk', color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' },
    behind: { label: 'Behind', color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' },
    achieved: { label: 'Achieved', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
  }
  const { label, color } = config[status]
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${color}`}>
      {label}
    </span>
  )
}

function KPIStatusDot({ status }: { status: DepartmentKPI['status'] }) {
  const colors = {
    green: 'bg-green-500',
    yellow: 'bg-amber-500',
    red: 'bg-red-500',
  }
  return <span className={`w-2.5 h-2.5 rounded-full ${colors[status]}`} />
}

function TrendIndicator({ trend, percentage }: { trend: DepartmentKPI['trend']; percentage: number }) {
  if (trend === 'up') {
    return (
      <span className="flex items-center gap-0.5 text-green-600 dark:text-green-400 text-xs">
        <TrendingUp className="w-3 h-3" />
        {percentage}%
      </span>
    )
  }
  if (trend === 'down') {
    return (
      <span className="flex items-center gap-0.5 text-red-600 dark:text-red-400 text-xs">
        <TrendingDown className="w-3 h-3" />
        {percentage}%
      </span>
    )
  }
  return (
    <span className="flex items-center gap-0.5 text-muted text-xs">
      <Minus className="w-3 h-3" />
      {percentage}%
    </span>
  )
}

function ProgressBar({ percentage, status }: { percentage: number; status: CompanyObjective['status'] }) {
  const colors = {
    on_track: 'bg-green-500',
    at_risk: 'bg-amber-500',
    behind: 'bg-red-500',
    achieved: 'bg-blue-500',
  }
  return (
    <div className="h-2 bg-surface rounded-full overflow-hidden">
      <div
        className={`h-full rounded-full transition-all ${colors[status]}`}
        style={{ width: `${Math.min(percentage, 100)}%` }}
      />
    </div>
  )
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function StrategyPage() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<'fy26' | 'fy27'>('fy26')
  const [kpis, setKpis] = useState<DepartmentKPI[]>(MOCK_KPIS)
  const [loading, setLoading] = useState(false)
  const [expandedDepartments, setExpandedDepartments] = useState<Set<string>>(new Set(['Legal', 'Finance', 'HR/People']))

  // Select objectives based on active tab
  const objectives = activeTab === 'fy26' ? FY26_OBJECTIVES : FY27_OBJECTIVES

  // Group KPIs by department
  const kpisByDepartment = kpis.reduce((acc, kpi) => {
    if (!acc[kpi.department]) {
      acc[kpi.department] = []
    }
    acc[kpi.department].push(kpi)
    return acc
  }, {} as Record<string, DepartmentKPI[]>)

  const departments = Object.keys(kpisByDepartment).sort()

  const toggleDepartment = (dept: string) => {
    setExpandedDepartments(prev => {
      const next = new Set(prev)
      if (next.has(dept)) {
        next.delete(dept)
      } else {
        next.add(dept)
      }
      return next
    })
  }

  // Calculate summary stats
  const objectiveSummary = {
    total: objectives.length,
    onTrack: objectives.filter(o => o.status === 'on_track').length,
    atRisk: objectives.filter(o => o.status === 'at_risk').length,
    behind: objectives.filter(o => o.status === 'behind').length,
    achieved: objectives.filter(o => o.status === 'achieved').length,
    avgProgress: Math.round(objectives.reduce((sum, o) => sum + o.progress_percentage, 0) / objectives.length),
  }

  const kpiSummary = {
    total: kpis.length,
    green: kpis.filter(k => k.status === 'green').length,
    yellow: kpis.filter(k => k.status === 'yellow').length,
    red: kpis.filter(k => k.status === 'red').length,
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-muted" />
      </div>
    )
  }

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <PageHeader />

      <main className="flex-1 overflow-auto">
        <div className="max-w-7xl mx-auto px-6 py-8">
          {/* Page Title */}
          <div className="mb-8">
            <h1 className="heading-1">Strategic Alignment</h1>
            <p className="text-muted mt-1">
              Company objectives and G&A department KPIs. Use these to align AI opportunities with
              strategic priorities and demonstrate impact in career reviews with Compass.
            </p>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <div className="bg-card border border-default rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted">
                  {activeTab === 'fy26' ? 'FY26 Progress' : 'FY27 Targets'}
                </span>
                <Target className="w-5 h-5 text-blue-500" />
              </div>
              <div className="mt-2">
                {activeTab === 'fy26' ? (
                  <>
                    <span className="text-2xl font-bold text-primary">{objectiveSummary.avgProgress}%</span>
                    <span className="text-sm text-muted ml-2">avg completion</span>
                  </>
                ) : (
                  <>
                    <span className="text-2xl font-bold text-primary">{objectives.length}</span>
                    <span className="text-sm text-muted ml-2">strategic goals</span>
                  </>
                )}
              </div>
              <div className="mt-2 flex gap-2 text-xs">
                {activeTab === 'fy26' ? (
                  <>
                    <span className="text-green-600">{objectiveSummary.onTrack} on track</span>
                    <span className="text-amber-600">{objectiveSummary.atRisk} at risk</span>
                    <span className="text-red-600">{objectiveSummary.behind} behind</span>
                  </>
                ) : (
                  <span className="text-secondary">Planning targets for next fiscal year</span>
                )}
              </div>
            </div>

            <div className="bg-card border border-default rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted">KPI Health</span>
                <BarChart3 className="w-5 h-5 text-green-500" />
              </div>
              <div className="mt-2">
                <span className="text-2xl font-bold text-primary">{kpiSummary.total}</span>
                <span className="text-sm text-muted ml-2">tracked KPIs</span>
              </div>
              <div className="mt-2 flex gap-2 text-xs">
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-green-500" />
                  {kpiSummary.green} green
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-amber-500" />
                  {kpiSummary.yellow} yellow
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-red-500" />
                  {kpiSummary.red} red
                </span>
              </div>
            </div>

            <div className="bg-card border border-default rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted">Departments</span>
                <Building2 className="w-5 h-5 text-purple-500" />
              </div>
              <div className="mt-2">
                <span className="text-2xl font-bold text-primary">{departments.length}</span>
                <span className="text-sm text-muted ml-2">with AI KPIs</span>
              </div>
              <div className="mt-2 text-xs text-muted">
                {departments.slice(0, 3).join(', ')}{departments.length > 3 ? ` +${departments.length - 3} more` : ''}
              </div>
            </div>

            <div className="bg-card border border-default rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted">AI Initiatives</span>
                <Sparkles className="w-5 h-5 text-amber-500" />
              </div>
              <div className="mt-2">
                <span className="text-2xl font-bold text-primary">
                  {objectives.find(o => o.id === '1')?.current_value || 0}
                </span>
                <span className="text-sm text-muted ml-2">
                  / {objectives.find(o => o.id === '1')?.target_value || 0} processes
                </span>
              </div>
              <div className="mt-2 text-xs text-muted">
                AI-powered process target
              </div>
            </div>
          </div>

          {/* Company Objectives Section */}
          <section className="mb-10">
            <div className="flex items-center justify-between mb-4">
              <h2 className="heading-3 flex items-center gap-2">
                <Target className="w-5 h-5 text-blue-500" />
                Company Objectives
              </h2>
              <span className="text-sm text-muted">{objectives.length} strategic goals</span>
            </div>

            {/* Fiscal Year Tabs */}
            <div className="flex items-center gap-2 mb-4">
              <button
                onClick={() => setActiveTab('fy26')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === 'fy26'
                    ? 'bg-primary text-white'
                    : 'bg-card border border-default text-secondary hover:bg-hover'
                }`}
              >
                FY26 Goals
                <span className="ml-1.5 text-xs opacity-75">(Current)</span>
              </button>
              <button
                onClick={() => setActiveTab('fy27')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === 'fy27'
                    ? 'bg-primary text-white'
                    : 'bg-card border border-default text-secondary hover:bg-hover'
                }`}
              >
                FY27 Goals
                <span className="ml-1.5 text-xs opacity-75">(Notional)</span>
              </button>
              {activeTab === 'fy27' && (
                <span className="ml-2 text-xs text-amber-600 bg-amber-100 dark:bg-amber-900/30 dark:text-amber-400 px-2 py-1 rounded">
                  Forward-looking targets - measure progress against FY26
                </span>
              )}
            </div>

            <div className="space-y-4">
              {objectives
                .sort((a, b) => a.priority - b.priority)
                .map((objective) => (
                  <div
                    key={objective.id}
                    className="bg-card border border-default rounded-lg p-5 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start gap-4">
                      {/* Icon */}
                      <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-surface flex items-center justify-center">
                        <ObjectiveIcon name={objective.icon} className="w-6 h-6 text-accent" />
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <h3 className="text-base font-semibold text-primary">
                              {objective.priority}. {objective.title}
                            </h3>
                            <p className="text-sm text-muted mt-1">{objective.description}</p>
                          </div>
                          {activeTab === 'fy26' ? (
                            <StatusBadge status={objective.status} />
                          ) : (
                            <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-surface text-secondary">
                              Planning
                            </span>
                          )}
                        </div>

                        {/* Progress */}
                        <div className="mt-4">
                          <div className="flex items-center justify-between text-sm mb-1">
                            <span className="text-muted">{objective.target_metric}</span>
                            <span className="font-medium text-primary">
                              {activeTab === 'fy26' ? (
                                <>
                                  {objective.current_value !== null ? objective.current_value : '—'}{objective.unit} / {objective.target_value}{objective.unit}
                                </>
                              ) : (
                                <>Target: {objective.target_value}{objective.unit}</>
                              )}
                            </span>
                          </div>
                          {activeTab === 'fy26' ? (
                            <>
                              <ProgressBar percentage={objective.progress_percentage} status={objective.status} />
                              <div className="flex items-center justify-between mt-1">
                                <span className="text-xs text-muted">{objective.progress_percentage}% complete</span>
                                <span className="text-xs text-muted">
                                  Updated {new Date(objective.updated_at).toLocaleDateString()}
                                </span>
                              </div>
                            </>
                          ) : (
                            <div className="h-2 bg-surface rounded-full overflow-hidden">
                              <div className="h-full w-0 rounded-full bg-border" />
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          </section>

          {/* Department KPIs Section */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="heading-3 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-green-500" />
                Department KPIs
              </h2>
              <span className="text-sm text-muted">{kpis.length} metrics across {departments.length} departments</span>
            </div>

            <div className="space-y-3">
              {departments.map((department) => {
                const deptKpis = kpisByDepartment[department]
                const isExpanded = expandedDepartments.has(department)
                const deptHealth = {
                  green: deptKpis.filter(k => k.status === 'green').length,
                  yellow: deptKpis.filter(k => k.status === 'yellow').length,
                  red: deptKpis.filter(k => k.status === 'red').length,
                }

                return (
                  <div key={department} className="bg-card border border-default rounded-lg overflow-hidden">
                    {/* Department Header */}
                    <button
                      onClick={() => toggleDepartment(department)}
                      className="w-full flex items-center justify-between p-4 hover:bg-hover transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        {isExpanded ? (
                          <ChevronDown className="w-5 h-5 text-muted" />
                        ) : (
                          <ChevronRight className="w-5 h-5 text-muted" />
                        )}
                        <Building2 className="w-5 h-5 text-purple-500" />
                        <span className="font-medium text-primary">{department}</span>
                        <span className="text-sm text-muted">({deptKpis.length} KPIs)</span>
                      </div>
                      <div className="flex items-center gap-3">
                        {deptHealth.green > 0 && (
                          <span className="flex items-center gap-1 text-xs text-green-600">
                            <span className="w-2 h-2 rounded-full bg-green-500" />
                            {deptHealth.green}
                          </span>
                        )}
                        {deptHealth.yellow > 0 && (
                          <span className="flex items-center gap-1 text-xs text-amber-600">
                            <span className="w-2 h-2 rounded-full bg-amber-500" />
                            {deptHealth.yellow}
                          </span>
                        )}
                        {deptHealth.red > 0 && (
                          <span className="flex items-center gap-1 text-xs text-red-600">
                            <span className="w-2 h-2 rounded-full bg-red-500" />
                            {deptHealth.red}
                          </span>
                        )}
                      </div>
                    </button>

                    {/* KPI List */}
                    {isExpanded && (
                      <div className="border-t border-default">
                        <table className="w-full">
                          <thead>
                            <tr className="bg-hover/50 text-xs text-muted uppercase">
                              <th className="text-left px-4 py-2 font-medium">KPI</th>
                              <th className="text-right px-4 py-2 font-medium">Current</th>
                              <th className="text-right px-4 py-2 font-medium">Target</th>
                              <th className="text-center px-4 py-2 font-medium">Trend</th>
                              <th className="text-center px-4 py-2 font-medium">Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {deptKpis.map((kpi) => (
                              <tr key={kpi.id} className="border-t border-default hover:bg-hover/30">
                                <td className="px-4 py-3">
                                  <div>
                                    <span className="text-sm font-medium text-primary">{kpi.kpi_name}</span>
                                    <p className="text-xs text-muted mt-0.5">{kpi.description}</p>
                                  </div>
                                </td>
                                <td className="text-right px-4 py-3">
                                  <span className="text-sm font-medium text-primary">
                                    {kpi.current_value !== null ? kpi.current_value : '—'} {kpi.unit}
                                  </span>
                                </td>
                                <td className="text-right px-4 py-3">
                                  <span className="text-sm text-muted">
                                    {kpi.target_value} {kpi.unit}
                                  </span>
                                </td>
                                <td className="text-center px-4 py-3">
                                  <TrendIndicator trend={kpi.trend} percentage={kpi.trend_percentage} />
                                </td>
                                <td className="text-center px-4 py-3">
                                  <div className="flex justify-center">
                                    <KPIStatusDot status={kpi.status} />
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </section>

          {/* Info Banner */}
          <div className="mt-8 p-4 bg-surface border border-default rounded-lg">
            <div className="flex items-start gap-3">
              <Target className="w-5 h-5 text-accent flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-sm font-medium text-primary">
                  Aligning Opportunities with Strategy
                </h3>
                <p className="text-sm text-secondary mt-1">
                  When evaluating AI opportunities, consider how they contribute to these company objectives
                  and department KPIs. Opportunities that directly impact multiple strategic goals should
                  receive higher priority scores.
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
