/**
 * @deprecated Supabase has been removed. Use @/lib/api instead.
 *
 * This file exists only as a build-time safety net so that any overlooked
 * imports of `supabase` fail loudly at runtime rather than silently at
 * compile time.
 */

export const supabase: never = new Proxy({} as never, {
  get() {
    throw new Error(
      'supabase has been removed. Use authenticatedFetch / apiFetch from @/lib/api instead.'
    );
  },
});
