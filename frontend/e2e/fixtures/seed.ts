import { createClient, SupabaseClient } from '@supabase/supabase-js'

/**
 * E2E Test Data Seeding
 * Creates and cleans up test data for E2E tests.
 */

// Test data identifiers
const TEST_CLIENT_ID = 'e2e-test-client-00000000-0000-0000-0000-000000000001'
const TEST_USER_EMAIL = 'test@example.com'

// Initialize Supabase client with service role key for admin access
function getSupabaseClient(): SupabaseClient {
  const url = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY

  if (!url || !key) {
    throw new Error('Missing Supabase environment variables for E2E tests')
  }

  return createClient(url, key, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
  })
}

/**
 * Seed test data for E2E tests
 */
export async function seedTestData(): Promise<void> {
  const supabase = getSupabaseClient()

  console.log('Seeding E2E test data...')

  // Create test client
  const { error: clientError } = await supabase.from('clients').upsert({
    id: TEST_CLIENT_ID,
    name: 'E2E Test Client',
    description: 'Client for E2E testing',
    created_at: new Date().toISOString(),
  })

  if (clientError) {
    console.error('Error creating test client:', clientError)
  }

  // Create test documents
  const testDocuments = [
    {
      id: 'e2e-doc-00000000-0000-0000-0000-000000000001',
      client_id: TEST_CLIENT_ID,
      title: 'AI Strategy Guide',
      content: 'This is a test document about AI strategy for enterprise organizations.',
      classification: 'strategy',
      created_at: new Date().toISOString(),
    },
    {
      id: 'e2e-doc-00000000-0000-0000-0000-000000000002',
      client_id: TEST_CLIENT_ID,
      title: 'Implementation Playbook',
      content: 'Steps for implementing AI in your organization.',
      classification: 'playbook',
      created_at: new Date().toISOString(),
    },
  ]

  const { error: docsError } = await supabase.from('kb_documents').upsert(testDocuments)

  if (docsError) {
    console.error('Error creating test documents:', docsError)
  }

  // Create test opportunities
  const testOpportunities = [
    {
      id: 'e2e-opp-00000000-0000-0000-0000-000000000001',
      client_id: TEST_CLIENT_ID,
      name: 'AI Chatbot Implementation',
      description: 'Implement customer service chatbot',
      status: 'discovery',
      impact_score: 8,
      feasibility_score: 7,
      alignment_score: 9,
      tier: 1,
      created_at: new Date().toISOString(),
    },
    {
      id: 'e2e-opp-00000000-0000-0000-0000-000000000002',
      client_id: TEST_CLIENT_ID,
      name: 'Document Processing Automation',
      description: 'Automate document processing with AI',
      status: 'validation',
      impact_score: 6,
      feasibility_score: 8,
      alignment_score: 7,
      tier: 2,
      created_at: new Date().toISOString(),
    },
  ]

  const { error: oppError } = await supabase.from('opportunities').upsert(testOpportunities)

  if (oppError) {
    console.error('Error creating test opportunities:', oppError)
  }

  // Create test stakeholders
  const testStakeholders = [
    {
      id: 'e2e-stake-00000000-0000-0000-0000-000000000001',
      client_id: TEST_CLIENT_ID,
      name: 'John Smith',
      role: 'CTO',
      email: 'john.smith@testclient.com',
      sentiment_score: 0.8,
      engagement_level: 'high',
      created_at: new Date().toISOString(),
    },
    {
      id: 'e2e-stake-00000000-0000-0000-0000-000000000002',
      client_id: TEST_CLIENT_ID,
      name: 'Jane Doe',
      role: 'VP Engineering',
      email: 'jane.doe@testclient.com',
      sentiment_score: 0.6,
      engagement_level: 'medium',
      created_at: new Date().toISOString(),
    },
  ]

  const { error: stakeError } = await supabase.from('stakeholders').upsert(testStakeholders)

  if (stakeError) {
    console.error('Error creating test stakeholders:', stakeError)
  }

  // Create test meeting room
  const { error: roomError } = await supabase.from('meeting_rooms').upsert({
    id: 'e2e-room-00000000-0000-0000-0000-000000000001',
    client_id: TEST_CLIENT_ID,
    name: 'Strategy Discussion Room',
    topic: 'AI Strategy Planning',
    autonomous_mode: false,
    created_at: new Date().toISOString(),
  })

  if (roomError) {
    console.error('Error creating test meeting room:', roomError)
  }

  console.log('E2E test data seeded successfully')
}

/**
 * Clean up test data after E2E tests
 */
export async function cleanupTestData(): Promise<void> {
  const supabase = getSupabaseClient()

  console.log('Cleaning up E2E test data...')

  // Delete in reverse order of dependencies

  // Delete meeting room messages
  await supabase.from('meeting_room_messages').delete().eq('room_id', 'e2e-room-00000000-0000-0000-0000-000000000001')

  // Delete meeting room participants
  await supabase
    .from('meeting_room_participants')
    .delete()
    .eq('room_id', 'e2e-room-00000000-0000-0000-0000-000000000001')

  // Delete meeting rooms
  await supabase.from('meeting_rooms').delete().eq('client_id', TEST_CLIENT_ID)

  // Delete conversations and messages
  await supabase.from('messages').delete().eq('client_id', TEST_CLIENT_ID)
  await supabase.from('conversations').delete().eq('client_id', TEST_CLIENT_ID)

  // Delete document chunks
  await supabase.from('document_chunks').delete().like('document_id', 'e2e-doc-%')

  // Delete documents
  await supabase.from('kb_documents').delete().eq('client_id', TEST_CLIENT_ID)

  // Delete stakeholder insights
  await supabase.from('stakeholder_insights').delete().like('stakeholder_id', 'e2e-stake-%')

  // Delete stakeholders
  await supabase.from('stakeholders').delete().eq('client_id', TEST_CLIENT_ID)

  // Delete opportunities
  await supabase.from('opportunities').delete().eq('client_id', TEST_CLIENT_ID)

  // Delete test client
  await supabase.from('clients').delete().eq('id', TEST_CLIENT_ID)

  console.log('E2E test data cleaned up successfully')
}

/**
 * Reset test data (cleanup + seed)
 */
export async function resetTestData(): Promise<void> {
  await cleanupTestData()
  await seedTestData()
}

// Export for CLI usage
if (require.main === module) {
  const command = process.argv[2]

  switch (command) {
    case 'seed':
      seedTestData()
        .then(() => process.exit(0))
        .catch((err) => {
          console.error(err)
          process.exit(1)
        })
      break
    case 'cleanup':
      cleanupTestData()
        .then(() => process.exit(0))
        .catch((err) => {
          console.error(err)
          process.exit(1)
        })
      break
    case 'reset':
      resetTestData()
        .then(() => process.exit(0))
        .catch((err) => {
          console.error(err)
          process.exit(1)
        })
      break
    default:
      console.log('Usage: ts-node seed.ts [seed|cleanup|reset]')
      process.exit(1)
  }
}
