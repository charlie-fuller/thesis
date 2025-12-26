-- Fix for users table role column issue
-- If roles are showing as "authenticated" instead of actual role values

-- Step 1: Check current state
SELECT id, email, name, role, client_id
FROM public.users
ORDER BY created_at DESC
LIMIT 10;

-- Step 2: Check if there's a trigger overriding roles
SELECT trigger_name, event_manipulation, event_object_table, action_statement
FROM information_schema.triggers
WHERE event_object_table = 'users'
AND event_object_schema = 'public';

-- Step 3: Fix - Update your user to be admin
-- REPLACE 'your-email@example.com' with your actual email address
UPDATE public.users
SET role = 'admin'
WHERE email = 'your-email@example.com';

-- Step 4: Verify the change worked
SELECT email, role, name, client_id
FROM public.users
WHERE email = 'your-email@example.com';

-- Step 5: If role keeps reverting to 'authenticated', check the trigger
-- The trigger might be in the database that auto-creates users from auth.users

-- You may need to modify the trigger to respect the role column
-- or set role in a separate UPDATE statement after user creation
