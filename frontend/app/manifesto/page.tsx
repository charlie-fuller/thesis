'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import PageLayout from '@/components/PageLayout'
import LoadingSpinner from '@/components/LoadingSpinner'

type ManifestoTab = 'poster' | 'check'

const principles = [
  {
    id: 1,
    title: 'State change or it doesn\'t count.',
    summary: 'If nothing moved -- no behavior shifted, no mindset changed, no system updated -- then nothing happened. Show me what moved.',
    rationale: [
      'State change isn\'t just money. Not just time saved. It\'s psychological. Did someone\'s understanding shift? Did a team start working differently? Did a process actually change, or did we just document a new one that nobody follows?',
      'Nobody buys AI. They buy state change. And verified reality -- what actually happened, not what was projected -- is the only truth that counts. The only measure that matters is whether something actually moved.',
      'A document that nobody reads didn\'t change state. A demo that doesn\'t connect to production didn\'t change state. A strategy deck that sits in a SharePoint folder gathering digital dust didn\'t change state. We\'ve all seen this. The graveyard of proofs of concept is real, and every headstone reads "looked great in the meeting."',
      'So we ask: What state are we trying to change? How will we know it changed? And if it didn\'t change, what do we do differently?',
      'This is the foundation. Every other principle serves this one.',
    ],
    checkQuestion: 'What specifically will be different after this? Who will behave differently, and how?',
  },
  {
    id: 2,
    title: 'Problems before solutions.',
    summary: 'Explore the problem deeply before ever discussing tools. The right answer might be "do nothing."',
    rationale: [
      'The technology is exciting. You see a demo and your brain immediately starts connecting dots -- "we could use this for X, we could automate Y." That creative impulse is valuable. But it\'s dangerous when it runs ahead of understanding.',
      'Starting with the solution is how you end up with a graveyard of proofs of concept that solved problems nobody actually had. It\'s like prescribing medication before running the diagnosis. Sure, you might get lucky. But at enterprise scale, "getting lucky" isn\'t a strategy.',
      'Don\'t start from what the model can generate. Start from which state must change. Go and see. Understand the current state before imagining the future one.',
      'The right answer might be "do nothing." It might be "this doesn\'t need AI." It might be "we need to fix the process first." Those are all valid outcomes of good problem discovery. DISCO exists precisely for this -- structured exploration of the problem space before anyone starts building.',
    ],
    checkQuestion: 'Have I fully explored the problem, or am I jumping to a tool/approach?',
  },
  {
    id: 3,
    title: 'Evidence over eloquence.',
    summary: 'Fluency feels like truth. A polished demo feels like progress. Neither is. Show your receipts.',
    rationale: [
      'Fluency -- whether from a person or an AI model -- feels like truth. A well-structured argument, a polished presentation, a confident recommendation. Our brains are wired to trust eloquence. That\'s exactly the vulnerability.',
      'Receipts, not promises. Tone feels like truth -- but it isn\'t. Lines of code are a vanity metric. A good demo vibe is not a test result.',
      'If you can\'t point to data, documents, observed reality, or measured outcomes, you\'re guessing. And guessing at enterprise scale is expensive. Not just financially -- it erodes trust. When we recommend something and can\'t show why, we\'re asking people to take it on faith. And faith doesn\'t scale across an organization.',
      'So we cite our sources. We show our work. When an agent makes a recommendation, it points to the knowledge base documents, the interview transcripts, the research that informed it. Not because we don\'t trust our judgment, but because judgment improves when it\'s grounded in evidence.',
    ],
    checkQuestion: 'Can I point to evidence for this recommendation, or does it just sound right?',
  },
  {
    id: 4,
    title: 'People are the center.',
    summary: 'Technology adoption is a community problem, not a technology problem. The human experience determines whether everything else works.',
    rationale: [
      'The sequencing matters: people first, then processes, then platforms. Not as a sentiment. As an operational sequence. Figure out the human experience before you design the process. Design the process before you choose the platform.',
      'Fear of job loss is rational. I need to say that clearly because too many AI conversations dance around it. When you tell someone "AI will handle the repetitive parts of your job," what they hear is "AI will handle the parts of my job that justify my salary." Address that honestly or lose trust permanently.',
      'Show me the incentive and I\'ll show you the outcome. If you want people to adopt new tools, you need to understand what they\'re incentivized to do. Champions burn out without support. Dignity isn\'t sentiment; it\'s an operational control. When people don\'t feel respected by the process, they\'ll find ways to work around it -- and they\'ll be right to.',
      'The human experience isn\'t a nice-to-have bolt-on at the end. It\'s the thing that determines whether everything else works.',
    ],
    checkQuestion: 'Have I considered the human experience -- fear, incentives, dignity, adoption?',
  },
  {
    id: 5,
    title: 'Humans decide.',
    summary: 'Agents explore paths; humans choose the destination. No automation by default.',
    rationale: [
      'Non-negotiable, and simpler than people make it.',
      'Agents explore paths. Humans choose the destination. AI recommends. Humans decide. No automation by default. Veto power without justification required. You don\'t have to explain why you\'re overriding the AI. The fact that you want to is enough.',
      'We decide where we\'re going; the agents get us there. The process of human judgment -- messy, intuitive, experience-driven, sometimes irrational -- has value. It should never be optimized away, even when the optimization looks like efficiency.',
      'This doesn\'t mean humans make every micro-decision. It means the important ones -- what to pursue, what to stop, what to recommend to leadership -- always have a human at the helm. The agents do the synthesis, the analysis, the pattern-finding. The human brings the judgment that no amount of training data can replicate.',
    ],
    checkQuestion: 'Is there a clear human decision point, or is this running on autopilot?',
  },
  {
    id: 6,
    title: 'Multiple perspectives.',
    summary: 'No single viewpoint is sufficient for complex decisions. The goal isn\'t consensus -- it\'s completeness.',
    rationale: [
      'Thesis has 22 agents instead of one really good one. There\'s a reason for that.',
      'No single viewpoint is sufficient for complex decisions. Finance sees ROI and payback periods. Security sees attack surfaces and compliance gaps. Legal sees liability and regulatory exposure. People-focused analysis sees adoption barriers and change fatigue. Systems thinking sees second-order effects nobody else is looking for.',
      'The goal isn\'t consensus. Consensus is often just the lowest-common-denominator answer that nobody disagrees with strongly enough to fight. The goal is completeness. Put all the perspectives on the table, let them genuinely interrogate each other, and then the human decides.',
      'There\'s a misfit language problem in AI -- different disciplines can\'t even talk to each other about it because they\'re using different vocabularies, different frameworks, different definitions of success. Thesis bridges that by having specialized agents who translate between these worlds.',
      'We also need the courage to build inside uncertainty rather than collapsing nuance into false simplicity. "It depends" is sometimes the most honest answer. The value is in understanding what it depends on.',
    ],
    checkQuestion: 'Whose viewpoint am I missing? What would security/legal/finance/users say?',
  },
  {
    id: 7,
    title: 'Context is kindness. Brevity is respect.',
    summary: 'Supply enough context that people can engage. Cut everything else. Use your big and beautiful brain for thinking, not synthesizing.',
    rationale: [
      'Two sides of the same coin, and the whole reason Thesis exists.',
      'Leaving out context is a tax on everyone downstream. When you send a recommendation without the reasoning, every recipient has to reconstruct the logic themselves -- or worse, they just trust the conclusion without understanding it. That\'s not efficiency. That\'s a setup for misalignment.',
      'But leaving in filler is a tax on everyone\'s time. Nobody needs the preamble. Nobody needs three paragraphs of background before the recommendation. Say what matters, cut everything else, and if someone needs more depth, they\'ll ask. That\'s what dig-deeper links are for.',
      'This is the tension Thesis navigates every day. Smart Brevity isn\'t about being terse -- it\'s about being thoughtful about what you include. Supply enough context that people can engage meaningfully. Don\'t assume shared understanding. But don\'t bury them either.',
      'Use your big and beautiful brain for thinking, not synthesizing. That\'s the promise. We handle the synthesis so you can do the work that actually requires human judgment.',
    ],
    checkQuestion: 'Am I providing enough context to act on, without burying the signal in noise?',
  },
  {
    id: 8,
    title: 'Guardrails, not gates.',
    summary: 'Governance isn\'t gatekeeping. The right framework frees people to build with confidence. Guardrails keep you on the road; gates keep you off it.',
    rationale: [
      'This metaphor captures something governance conversations usually miss.',
      'Gates keep you off the road. They say "stop, justify yourself, wait for approval, proceed if deemed worthy." Gates create bottlenecks, breed resentment, and incentivize people to find ways around them. Most corporate governance is gates dressed up as process improvement.',
      'Guardrails keep you on the road. They say "go ahead, build, experiment -- and here are the important questions to answer along the way." Maintenance plan. Adoption strategy. Evaluation criteria. Sustainability model. These aren\'t obstacles. They\'re the things that prevent your proof of concept from becoming an orphan.',
      'There\'s a meaningful difference between agents on rails and agents running on vibes. And the right way to think about risk is stopping the line -- not as punishment, but as an enabling function. When anyone can pull the cord, quality goes up because problems get caught early.',
      'Structured process isn\'t bureaucracy. The right framework frees people to build with confidence because the important questions have already been asked. We build guardrails, not gates.',
    ],
    checkQuestion: 'Am I enabling or blocking? Are the governance questions answered?',
  },
  {
    id: 9,
    title: 'Trace the connections.',
    summary: 'Everything is connected. Follow the ripples before you drop the stone.',
    rationale: [
      'Nexus\'s core philosophy, and possibly the most underrated principle here.',
      'Everything is connected. There are no isolated changes in a complex organization. Deploy a new tool in one department and it affects the workflows of three others. Change an incentive structure and watch behavior shift in places you didn\'t predict. Automate a process and discover that the "inefficiency" you eliminated was actually serving a communication function nobody documented.',
      '"And then what happens?" is the most important question you can ask. And you need to ask it more than once. First-order effects are obvious. Second-order effects are where the real consequences live. Third-order effects are where the surprises hide.',
      'The obvious intervention is rarely the most effective one. Follow the ripples before you drop the stone. Today\'s solution becomes tomorrow\'s problem without looking at the whole system.',
      'This is why systems thinking isn\'t optional. It\'s not a nice-to-have for academics. It\'s the difference between solving a problem and moving a problem.',
    ],
    checkQuestion: 'What are the second and third-order effects? And then what happens?',
  },
  {
    id: 10,
    title: 'The questions stay the same.',
    summary: 'The methodology is shared. The conclusions are context-specific. When the team shares a common way of discovering, their work compounds.',
    rationale: [
      'The scaling principle. The one that makes everything else compound.',
      'DISCO doesn\'t prescribe the same answer every time. It asks the right questions every time. Discovery, Intelligence, Synthesis, Convergence -- the methodology is the same whether you\'re evaluating a customer service chatbot or a company-wide knowledge management overhaul. The conclusions are context-specific. The inquiry is standardized.',
      'Standardized work isn\'t about making everyone do the same thing. It\'s about making the process of improvement consistent so that insights transfer. When one team discovers a better way to evaluate AI readiness, that insight should be immediately available to every other team.',
      'When a team of AI Solutions Partners shares a common way of discovering, analyzing, and operationalizing, their work compounds. They learn from each other\'s investigations. They build on each other\'s conclusions. They speak the same language.',
      'When everyone freelances, you get fragmentation. Four people doing four different discovery processes, producing four different formats, using four different criteria. No compounding. No shared learning. Just parallel isolation.',
      'The questions stay the same. That\'s how we scale.',
    ],
    checkQuestion: 'Am I following the shared methodology, or freelancing?',
  },
]

const agentExamples = [
  {
    principle: 'Principle 1 (State Change)',
    quote: 'This doesn\'t align with Principle 1 (State Change). The proposed action would produce documentation but no measurable shift in behavior, process, or outcome. What state are we trying to change here?',
  },
  {
    principle: 'Principle 2 (Problems Before Solutions)',
    quote: 'We\'re discussing tools before fully understanding the problem space. What problem are we solving, and have we confirmed it\'s the right one?',
  },
  {
    principle: 'Principle 3 (Evidence Over Eloquence)',
    quote: 'This recommendation sounds compelling but isn\'t grounded in evidence from the knowledge base or observed data. What are we basing this on?',
  },
]

const alignedExamples = [
  { text: 'Running DISCO discovery before recommending a platform', principles: '1, 2, 10' },
  { text: 'Citing KB documents when making a recommendation', principles: '3' },
  { text: 'Including adoption risk analysis alongside technical evaluation', principles: '4, 6' },
  { text: 'Presenting three options with tradeoffs and letting the user choose', principles: '5, 6' },
  { text: 'Flagging that a proposed automation removes human judgment', principles: '5' },
]

const misalignedExamples = [
  { text: 'Recommending a tool because "it\'s what everyone is using" without problem analysis', principles: '2, 3' },
  { text: 'Building a demo that won\'t connect to any production workflow', principles: '1' },
  { text: 'Producing a 50-page strategy document that nobody will read', principles: '1, 7' },
  { text: 'Ignoring adoption concerns because "the technology is clearly better"', principles: '4' },
  { text: 'Automating a decision process without human checkpoints', principles: '5' },
  { text: 'Analyzing an initiative from only a financial perspective', principles: '6' },
  { text: 'Blocking a team from experimenting because governance hasn\'t been "approved" yet', principles: '8' },
  { text: 'Implementing a change without considering downstream effects', principles: '9' },
  { text: 'Each team member using a completely different evaluation framework', principles: '10' },
]

function PrincipleCard({ principle, expanded = false }: { principle: typeof principles[0]; expanded?: boolean }) {
  const [isOpen, setIsOpen] = useState(expanded)

  return (
    <div className="card overflow-hidden">
      <div
        className={`flex items-start gap-4 p-5 ${!expanded ? 'cursor-pointer hover:bg-hover transition-colors' : ''}`}
        onClick={!expanded ? () => setIsOpen(!isOpen) : undefined}
      >
        {/* Number badge */}
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-teal-500 to-teal-600 flex items-center justify-center">
          <span className="text-white font-bold text-sm">{principle.id}</span>
        </div>

        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-primary leading-snug">
            {principle.title}
          </h3>
          <p className="text-secondary mt-1.5 leading-relaxed">
            {principle.summary}
          </p>
        </div>

        {!expanded && (
          <button
            className="flex-shrink-0 mt-1 p-1 text-muted hover:text-primary transition-colors"
            aria-label={isOpen ? 'Collapse' : 'Expand'}
          >
            <svg
              className={`w-5 h-5 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        )}
      </div>

      {/* Expandable rationale */}
      {(isOpen || expanded) && (
        <div className="px-5 pb-5 pt-0">
          <div className="border-t border-default pt-4 ml-14">
            {principle.rationale.map((paragraph, i) => (
              <p key={i} className="text-secondary leading-relaxed mb-3 last:mb-0">
                {paragraph}
              </p>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default function ManifestoPage() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()
  const [activeTab, setActiveTab] = useState<ManifestoTab>('poster')

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login')
    }
  }, [user, authLoading, router])

  if (authLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-page">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!user) return null

  const tabs: { id: ManifestoTab; label: string }[] = [
    { id: 'poster', label: 'The Principles' },
    { id: 'check', label: 'The Check' },
  ]

  return (
    <PageLayout>
      <div className="flex-1 overflow-auto">
        {/* Hero Section */}
        <div className="bg-gradient-to-br from-teal-600 via-teal-700 to-slate-800 text-white">
          <div className="max-w-4xl mx-auto px-6 py-12">
            <h1 className="text-4xl font-bold tracking-tight mb-2">
              The Thesis Manifesto
            </h1>
            <p className="text-teal-100 text-lg">
              10 principles for building AI that changes state, not just status.
            </p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-default bg-card sticky top-0 z-10">
          <div className="max-w-4xl mx-auto px-6">
            <div className="flex gap-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-4 py-3 text-sm font-medium transition-colors border-b-2 -mb-px ${
                    activeTab === tab.id
                      ? 'border-teal-500 text-teal-600 dark:text-teal-400'
                      : 'border-transparent text-muted hover:text-primary'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="max-w-4xl mx-auto px-6 py-8">

          {/* ===== THE POSTER ===== */}
          {activeTab === 'poster' && (
            <div>
              {/* Preamble */}
              <div className="card p-6 mb-8">
                <div className="max-w-3xl">
                  <p className="text-secondary leading-relaxed mb-4">
                    I built Thesis as a life jacket because I had a legitimate fear of drowning. Not in work &mdash; in information, decisions, stakeholders, context. Every meeting generated more questions than answers. Every initiative connected to three others. Every tool promised transformation and delivered a dashboard.
                  </p>
                  <p className="text-secondary leading-relaxed mb-4">
                    I needed my brain for <em className="text-primary font-medium not-italic">thinking</em>, not synthesizing. And I realized the people I&apos;d be building a team with would face the same firehose. Without shared methodology, four people building AI things at Contentful would create four different approaches, four different standards, and exactly zero compounding knowledge.
                  </p>
                  <p className="text-primary leading-relaxed font-medium">
                    So this is what we believe. These are the principles behind every agent, every process, every recommendation that comes out of this platform. If something we build doesn&apos;t align with these, we fix the build &mdash; not the principles.
                  </p>
                </div>
              </div>

              {/* Principles List */}
              <div className="space-y-3">
                {principles.map((p) => (
                  <PrincipleCard key={p.id} principle={p} />
                ))}
              </div>

              {/* Footer */}
              <div className="mt-8 text-center">
                <p className="text-muted text-sm italic">
                  This manifesto is a living document. If it stops changing state, it stopped working.
                </p>
              </div>
            </div>
          )}

          {/* ===== THE CHECK ===== */}
          {activeTab === 'check' && (
            <div>
              {/* Intro */}
              <div className="mb-8">
                <h2 className="text-2xl font-bold text-primary mb-2">The Manifesto Check</h2>
                <p className="text-secondary">
                  An operational test any action, command, or feature can be run against &mdash; for both agents and humans.
                </p>
              </div>

              {/* Agent Protocol */}
              <div className="card p-6 mb-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-8 h-8 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                    <svg className="w-4 h-4 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-primary">For Agents</h3>
                </div>

                <p className="text-secondary leading-relaxed mb-4">
                  Every agent carries these principles as operational context. When output conflicts with the manifesto, agents flag it directly &mdash; not as a footnote, not softened, not silently ignored.
                </p>

                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-primary uppercase tracking-wide mb-3">When to invoke</h4>
                  <ul className="space-y-2">
                    {[
                      'Before finalizing any recommendation or output',
                      'When evaluating initiatives, projects, or proposals',
                      'When a user request conflicts with manifesto principles',
                      'When generating content that could be theatre rather than substance',
                      'During DISCO processes at each phase transition',
                    ].map((item, i) => (
                      <li key={i} className="flex items-start gap-2.5">
                        <svg className="w-4 h-4 text-teal-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4" />
                        </svg>
                        <span className="text-secondary text-sm">{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-primary uppercase tracking-wide mb-3">How agents flag concerns</h4>
                  <div className="space-y-3">
                    {agentExamples.map((ex, i) => (
                      <div key={i} className="border-l-3 border-purple-400 bg-purple-50 dark:bg-purple-900/10 rounded-r-lg px-4 py-3">
                        <span className="text-xs font-semibold text-purple-600 dark:text-purple-400 uppercase tracking-wide">{ex.principle}</span>
                        <p className="text-secondary text-sm mt-1 leading-relaxed italic">&ldquo;{ex.quote}&rdquo;</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Human Self-Check */}
              <div className="card p-6 mb-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                    <svg className="w-4 h-4 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-primary">For Humans: Self-Check</h3>
                </div>

                <p className="text-secondary leading-relaxed mb-5">
                  Before shipping, building, recommending, or presenting anything, run through these:
                </p>

                <div className="overflow-x-auto -mx-6 px-6">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-default">
                        <th className="text-left py-3 pr-4 text-xs font-semibold text-muted uppercase tracking-wide w-8">#</th>
                        <th className="text-left py-3 pr-4 text-xs font-semibold text-muted uppercase tracking-wide w-48">Principle</th>
                        <th className="text-left py-3 text-xs font-semibold text-muted uppercase tracking-wide">Ask Yourself</th>
                      </tr>
                    </thead>
                    <tbody>
                      {principles.map((p) => (
                        <tr key={p.id} className="border-b border-default last:border-0">
                          <td className="py-3 pr-4 text-primary font-semibold">{p.id}</td>
                          <td className="py-3 pr-4 text-primary font-medium">{p.title.replace(/\.$/, '')}</td>
                          <td className="py-3 text-secondary">{p.checkQuestion}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Aligned vs Misaligned */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                {/* Aligned */}
                <div className="card p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <div className="w-6 h-6 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                      <svg className="w-3.5 h-3.5 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <h3 className="font-semibold text-green-700 dark:text-green-400">Aligned</h3>
                  </div>
                  <ul className="space-y-3">
                    {alignedExamples.map((ex, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-secondary text-sm leading-relaxed">{ex.text}</span>
                        <span className="flex-shrink-0 text-xs font-mono text-muted bg-hover px-1.5 py-0.5 rounded">
                          {ex.principles}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Misaligned */}
                <div className="card p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <div className="w-6 h-6 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                      <svg className="w-3.5 h-3.5 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </div>
                    <h3 className="font-semibold text-red-700 dark:text-red-400">Misaligned</h3>
                  </div>
                  <ul className="space-y-3">
                    {misalignedExamples.map((ex, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-secondary text-sm leading-relaxed">{ex.text}</span>
                        <span className="flex-shrink-0 text-xs font-mono text-muted bg-hover px-1.5 py-0.5 rounded">
                          {ex.principles}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Stop and Present Protocol */}
              <div className="card p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-8 h-8 rounded-lg bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                    <svg className="w-4 h-4 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-primary">The Stop-and-Present Protocol</h3>
                </div>

                <p className="text-secondary leading-relaxed mb-5">
                  When an agent identifies a genuine manifesto conflict:
                </p>

                <div className="space-y-3">
                  {[
                    { step: 1, label: 'Stop', desc: 'generating the current output direction' },
                    { step: 2, label: 'Name', desc: 'the specific principle being violated' },
                    { step: 3, label: 'Explain', desc: 'why the current path conflicts with the principle' },
                    { step: 4, label: 'Present', desc: 'the conflict to the user clearly and directly' },
                    { step: 5, label: 'Ask', desc: 'the user how they want to proceed' },
                  ].map((item) => (
                    <div key={item.step} className="flex items-center gap-3">
                      <div className="flex-shrink-0 w-7 h-7 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                        <span className="text-amber-700 dark:text-amber-400 text-xs font-bold">{item.step}</span>
                      </div>
                      <p className="text-sm">
                        <span className="font-semibold text-primary">{item.label}</span>
                        <span className="text-secondary"> {item.desc}</span>
                      </p>
                    </div>
                  ))}
                </div>

                <div className="mt-5 pt-4 border-t border-default">
                  <p className="text-muted text-sm italic">
                    The user always has the final say. The manifesto informs; it doesn&apos;t override human judgment. That would violate Principle 5.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </PageLayout>
  )
}
