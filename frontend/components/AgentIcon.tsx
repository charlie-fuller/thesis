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
} from 'lucide-react';

const AGENT_ICONS: Record<string, React.ElementType> = {
  atlas: Globe,           // Research
  fortuna: Coins,         // Finance
  guardian: Shield,       // IT/Governance
  counselor: Scale,       // Legal
  oracle: Sparkles,       // Transcripts
  sage: Users,            // People/HR
  strategist: Target,     // Executive Strategy
  architect: Building2,   // Technical Architecture
  operator: Cog,          // Operations
  pioneer: Rocket,        // Innovation/R&D
  catalyst: Megaphone,    // Internal Communications
  scholar: GraduationCap, // L&D
  nexus: Network,         // Systems Thinking
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
  atlas: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  fortuna: 'bg-green-500/20 text-green-400 border-green-500/30',
  guardian: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  counselor: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  oracle: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
  sage: 'bg-pink-500/20 text-pink-400 border-pink-500/30',
  strategist: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
  architect: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
  operator: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  pioneer: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
  catalyst: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  scholar: 'bg-teal-500/20 text-teal-400 border-teal-500/30',
  nexus: 'bg-violet-500/20 text-violet-400 border-violet-500/30',
};

export function getAgentColor(name: string): string {
  return AGENT_COLORS[name.toLowerCase()] || 'bg-gray-500/20 text-gray-400 border-gray-500/30';
}
