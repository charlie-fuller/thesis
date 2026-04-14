/**
 * E2E Test Data Seeding
 *
 * Stubbed out after Supabase removal. Test data seeding should
 * now go through the backend API or PocketBase directly.
 */

export async function seedTestData(): Promise<void> {
  console.log('E2E seed: Supabase client removed. Use backend API or PocketBase admin for seeding.')
}

export async function cleanupTestData(): Promise<void> {
  console.log('E2E cleanup: Supabase client removed. Use backend API or PocketBase admin for cleanup.')
}

export async function resetTestData(): Promise<void> {
  await cleanupTestData()
  await seedTestData()
}
