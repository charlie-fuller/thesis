import {
  Globe,
  Coins,
  Shield,
  Scale,
  Sparkles,
  Users,
  Target,
  Building2,
  Cog,
  Rocket,
  Megaphone,
  GraduationCap,
  Network,
  Bot,
  Mic,
  Workflow,
  MessageCircle,
  FileText,
} from 'lucide-react';

const AGENT_ICONS: Record<string, React.ElementType> = {
  // Meta-Agents
  facilitator: MessageCircle, // Meeting Orchestration
  reporter: FileText,         // Synthesis & Documentation
  // Stakeholder Perspective Agents
  atlas: Globe,           // Research
  capital: Coins,         // Finance
  guardian: Shield,       // IT/Governance
  counselor: Scale,       // Legal
  oracle: Sparkles,       // Transcripts
  sage: Users,            // People/HR
  // Consulting/Implementation Agents
  strategist: Target,     // Executive Strategy
  architect: Building2,   // Technical Architecture
  operator: Cog,          // Operations
  pioneer: Rocket,        // Innovation/R&D
  // Internal Enablement Agents
  catalyst: Megaphone,    // Internal Communications
  scholar: GraduationCap, // L&D
  echo: Mic,              // Brand Voice
  // Systems Agent
  nexus: Network,         // Systems Thinking
  // Coordinator
  coordinator: Workflow,  // Central Orchestrator
};

interface AgentIconProps {
  name: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function AgentIcon({ name, className, size = 'md' }: AgentIconProps) {
  const Icon = AGENT_ICONS[name.toLowerCase()] || Bot;
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };
  return <Icon className={`${sizeClasses[size]} ${className || ''}`} />;
}

export const AGENT_COLORS: Record<string, string> = {
  // Meta-Agents
  facilitator: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  reporter: 'bg-lime-600/20 text-lime-400 border-lime-600/30',
  // Stakeholder Perspective Agents
  atlas: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  capital: 'bg-green-500/20 text-green-400 border-green-500/30',
  guardian: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  counselor: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  oracle: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
  sage: 'bg-pink-500/20 text-pink-400 border-pink-500/30',
  // Consulting/Implementation Agents
  strategist: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
  architect: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
  operator: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  pioneer: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
  // Internal Enablement Agents
  catalyst: 'bg-lime-500/20 text-lime-400 border-lime-500/30',
  scholar: 'bg-teal-500/20 text-teal-400 border-teal-500/30',
  echo: 'bg-fuchsia-500/20 text-fuchsia-400 border-fuchsia-500/30',
  // Systems Agent
  nexus: 'bg-violet-500/20 text-violet-400 border-violet-500/30',
  // Coordinator
  coordinator: 'bg-sky-500/20 text-sky-400 border-sky-500/30',
};

export function getAgentColor(name: string): string {
  return AGENT_COLORS[name.toLowerCase()] || 'bg-gray-500/20 text-gray-400 border-gray-500/30';
}

// Solid background colors for avatars (meeting messages)
export const AGENT_AVATAR_COLORS: Record<string, { bg: string; text: string }> = {
  // Meta-Agents
  facilitator: { bg: 'bg-yellow-500', text: 'text-yellow-700' },
  reporter: { bg: 'bg-lime-600', text: 'text-lime-700' },
  // Stakeholder Perspective Agents
  atlas: { bg: 'bg-blue-500', text: 'text-blue-700' },
  capital: { bg: 'bg-green-500', text: 'text-green-700' },
  guardian: { bg: 'bg-purple-500', text: 'text-purple-700' },
  counselor: { bg: 'bg-amber-500', text: 'text-amber-700' },
  oracle: { bg: 'bg-cyan-500', text: 'text-cyan-700' },
  sage: { bg: 'bg-pink-500', text: 'text-pink-700' },
  // Consulting/Implementation Agents
  strategist: { bg: 'bg-indigo-500', text: 'text-indigo-700' },
  architect: { bg: 'bg-slate-500', text: 'text-slate-700' },
  operator: { bg: 'bg-orange-500', text: 'text-orange-700' },
  pioneer: { bg: 'bg-rose-500', text: 'text-rose-700' },
  // Internal Enablement Agents
  catalyst: { bg: 'bg-lime-500', text: 'text-lime-700' },
  scholar: { bg: 'bg-teal-500', text: 'text-teal-700' },
  echo: { bg: 'bg-fuchsia-500', text: 'text-fuchsia-700' },
  // Systems/Coordination Agents
  nexus: { bg: 'bg-violet-500', text: 'text-violet-700' },
  coordinator: { bg: 'bg-sky-500', text: 'text-sky-700' },
};

export function getAgentAvatarColor(name: string): { bg: string; text: string } {
  return AGENT_AVATAR_COLORS[name.toLowerCase()] || { bg: 'bg-gray-500', text: 'text-gray-700' };
}
