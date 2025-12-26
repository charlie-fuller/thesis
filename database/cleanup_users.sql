-- Clean up test users from database
-- This deletes users from both auth.users and public.users tables

-- Step 1: See what users exist
SELECT id, email, name, role
FROM public.users
ORDER BY created_at DESC;

-- Step 2: Delete specific test users
-- DELETE FROM BOTH TABLES (Supabase stores users in both places)

-- Delete charlie@sickofancy.ai
DELETE FROM auth.users WHERE email = 'charlie@sickofancy.ai';
DELETE FROM public.users WHERE email = 'charlie@sickofancy.ai';

-- Delete charlie@sickfancy.ai
DELETE FROM auth.users WHERE email = 'charlie@sickfancy.ai';
DELETE FROM public.users WHERE email = 'charlie@sickfancy.ai';

-- Delete charlie@test.com
DELETE FROM auth.users WHERE email = 'charlie@test.com';
DELETE FROM public.users WHERE email = 'charlie@test.com';

-- Delete motorthings@gmail.com
DELETE FROM auth.users WHERE email = 'motorthings@gmail.com';
DELETE FROM public.users WHERE email = 'motorthings@gmail.com';

-- Delete your-email@example.com
DELETE FROM auth.users WHERE email = 'your-email@example.com';
DELETE FROM public.users WHERE email = 'your-email@example.com';

-- Delete test@example.com
DELETE FROM auth.users WHERE email = 'test@example.com';
DELETE FROM public.users WHERE email = 'test@example.com';

-- Step 3: Verify deletions
SELECT id, email, name, role
FROM public.users
ORDER BY created_at DESC;

-- You should only see charlie@waifinder.org (admin) remaining
