-- =====================================================
-- Migration Verification Script
-- Run this after applying 001_initial_schema.sql
-- =====================================================

-- =====================================================
-- SECTION 1: Tables Verification
-- =====================================================
SELECT 
    'TABLES CHECK' as check_type,
    COUNT(*) as count,
    CASE 
        WHEN COUNT(*) = 3 THEN '✓ PASS'
        ELSE '✗ FAIL'
    END as status
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'projects', 'templates');

-- List all tables
SELECT 
    'Available Tables' as info,
    table_name
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;

-- =====================================================
-- END SECTION 1
-- =====================================================


-- =====================================================
-- SECTION 2: RLS Verification
-- =====================================================
SELECT 
    'RLS CHECK' as check_type,
    tablename,
    CASE 
        WHEN rowsecurity = true THEN '✓ ENABLED'
        ELSE '✗ DISABLED'
    END as status
FROM pg_tables 
WHERE schemaname = 'public'
AND tablename IN ('users', 'projects', 'templates')
ORDER BY tablename;

-- =====================================================
-- END SECTION 2
-- =====================================================


-- =====================================================
-- SECTION 3: Policies Verification
-- =====================================================
SELECT 
    'POLICIES CHECK' as check_type,
    COUNT(*) as count,
    CASE 
        WHEN COUNT(*) >= 14 THEN '✓ PASS'
        ELSE '✗ FAIL'
    END as status
FROM pg_policies 
WHERE schemaname = 'public';

-- List all policies
SELECT 
    'Policy Details' as info,
    tablename,
    policyname,
    cmd as command
FROM pg_policies 
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- =====================================================
-- END SECTION 3
-- =====================================================


-- =====================================================
-- SECTION 4: Indexes Verification
-- =====================================================
SELECT 
    'INDEXES CHECK' as check_type,
    COUNT(*) as count,
    CASE 
        WHEN COUNT(*) > 15 THEN '✓ PASS'
        ELSE '⚠ CHECK'
    END as status
FROM pg_indexes 
WHERE schemaname = 'public'
AND tablename IN ('users', 'projects', 'templates');

-- List all indexes
SELECT 
    'Index Details' as info,
    tablename,
    indexname
FROM pg_indexes 
WHERE schemaname = 'public'
AND tablename IN ('users', 'projects', 'templates')
ORDER BY tablename, indexname;

-- =====================================================
-- END SECTION 4
-- =====================================================


-- =====================================================
-- SECTION 5: Triggers Verification
-- =====================================================
SELECT 
    'TRIGGERS CHECK' as check_type,
    event_object_table as table_name,
    trigger_name,
    event_manipulation as event,
    '✓ EXISTS' as status
FROM information_schema.triggers 
WHERE trigger_schema = 'public'
AND event_object_table IN ('users', 'projects', 'templates')
ORDER BY event_object_table, trigger_name;

-- =====================================================
-- END SECTION 5
-- =====================================================


-- =====================================================
-- SECTION 6: Functions Verification
-- =====================================================
SELECT 
    'FUNCTIONS CHECK' as check_type,
    routine_name,
    '✓ EXISTS' as status
FROM information_schema.routines
WHERE routine_schema = 'public'
AND routine_name IN ('update_updated_at_column', 'handle_new_user')
ORDER BY routine_name;

-- =====================================================
-- END SECTION 6
-- =====================================================


-- =====================================================
-- SECTION 7: Columns Verification
-- =====================================================

-- Users table columns
SELECT 
    'USERS TABLE COLUMNS' as info,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'users'
ORDER BY ordinal_position;

-- Projects table columns
SELECT 
    'PROJECTS TABLE COLUMNS' as info,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'projects'
ORDER BY ordinal_position;

-- Templates table columns
SELECT 
    'TEMPLATES TABLE COLUMNS' as info,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'templates'
ORDER BY ordinal_position;

-- =====================================================
-- END SECTION 7
-- =====================================================


-- =====================================================
-- SECTION 8: Foreign Keys Verification
-- =====================================================
SELECT 
    'FOREIGN KEYS CHECK' as check_type,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    '✓ EXISTS' as status
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_schema = 'public'
AND tc.table_name IN ('users', 'projects', 'templates')
ORDER BY tc.table_name;

-- =====================================================
-- END SECTION 8
-- =====================================================


-- =====================================================
-- SECTION 9: Summary
-- =====================================================
SELECT 
    '===================' as separator,
    'MIGRATION VERIFICATION SUMMARY' as title,
    '===================' as separator2;

SELECT 
    'Total Tables' as metric,
    COUNT(*) as value,
    'Expected: 3' as expected
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'projects', 'templates')

UNION ALL

SELECT 
    'Total Policies' as metric,
    COUNT(*) as value,
    'Expected: 14+' as expected
FROM pg_policies 
WHERE schemaname = 'public'

UNION ALL

SELECT 
    'Total Indexes' as metric,
    COUNT(*) as value,
    'Expected: 15+' as expected
FROM pg_indexes 
WHERE schemaname = 'public'
AND tablename IN ('users', 'projects', 'templates')

UNION ALL

SELECT 
    'Total Triggers' as metric,
    COUNT(*) as value,
    'Expected: 4' as expected
FROM information_schema.triggers 
WHERE trigger_schema = 'public'
AND event_object_table IN ('users', 'projects', 'templates');

SELECT 
    '===================' as separator,
    '✓ Verification Complete' as status,
    '===================' as separator2;

-- =====================================================
-- END SECTION 9: Summary
-- =====================================================

