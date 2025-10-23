-- Migration: Add chat history and edit tracking tables
-- Description: Store chat messages and edit history for undo/redo functionality
-- Date: 2025-10-23

-- =====================================================
-- Create project_chat_messages table
-- =====================================================

CREATE TABLE IF NOT EXISTS public.project_chat_messages (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,

    -- Message type
    message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('generation', 'edit', 'question')),

    -- Message content
    user_prompt TEXT NOT NULL,
    ai_response TEXT NOT NULL,

    -- Additional metadata (stores selected_element, file_path, etc.)
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =====================================================
-- Create project_edit_history table
-- =====================================================

CREATE TABLE IF NOT EXISTS public.project_edit_history (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    chat_message_id UUID REFERENCES public.project_chat_messages(id) ON DELETE SET NULL,

    -- File information
    file_path TEXT NOT NULL, -- Component file that was edited

    -- Code changes
    old_code TEXT NOT NULL, -- Code before edit
    new_code TEXT NOT NULL, -- Code after edit
    diff_summary TEXT, -- Brief summary of changes

    -- Edit context
    selected_element JSONB, -- Full element data from selector
    edit_description TEXT, -- AI-generated description of what changed
    ai_instruction TEXT NOT NULL, -- Original user instruction

    -- Undo/redo tracking
    is_reverted BOOLEAN NOT NULL DEFAULT false,
    reverted_at TIMESTAMPTZ,
    reverted_by_edit_id UUID REFERENCES public.project_edit_history(id) ON DELETE SET NULL,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =====================================================
-- Indexes for performance
-- =====================================================

-- Chat messages indexes
CREATE INDEX IF NOT EXISTS idx_chat_messages_project_id
    ON public.project_chat_messages(project_id);

CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id
    ON public.project_chat_messages(user_id);

CREATE INDEX IF NOT EXISTS idx_chat_messages_type
    ON public.project_chat_messages(message_type);

CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at
    ON public.project_chat_messages(project_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_chat_messages_metadata
    ON public.project_chat_messages USING GIN (metadata);

-- Edit history indexes
CREATE INDEX IF NOT EXISTS idx_edit_history_project_id
    ON public.project_edit_history(project_id);

CREATE INDEX IF NOT EXISTS idx_edit_history_chat_message_id
    ON public.project_edit_history(chat_message_id);

CREATE INDEX IF NOT EXISTS idx_edit_history_file_path
    ON public.project_edit_history(project_id, file_path);

CREATE INDEX IF NOT EXISTS idx_edit_history_created_at
    ON public.project_edit_history(project_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_edit_history_not_reverted
    ON public.project_edit_history(project_id, is_reverted) WHERE is_reverted = false;

-- =====================================================
-- Triggers
-- =====================================================

-- Trigger for updated_at on chat messages
CREATE TRIGGER update_chat_messages_updated_at
    BEFORE UPDATE ON public.project_chat_messages
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- =====================================================
-- RLS Policies for project_chat_messages
-- =====================================================

ALTER TABLE public.project_chat_messages ENABLE ROW LEVEL SECURITY;

-- Users can view chat messages for their own projects
CREATE POLICY "Users can view own project chat messages"
ON public.project_chat_messages FOR SELECT
USING (
    project_id IN (
        SELECT id FROM public.projects WHERE user_id = auth.uid()
    )
);

-- Users can insert chat messages for their own projects
CREATE POLICY "Users can insert own project chat messages"
ON public.project_chat_messages FOR INSERT
WITH CHECK (
    project_id IN (
        SELECT id FROM public.projects WHERE user_id = auth.uid()
    )
    AND user_id = auth.uid()
);

-- Users can update chat messages for their own projects
CREATE POLICY "Users can update own project chat messages"
ON public.project_chat_messages FOR UPDATE
USING (
    project_id IN (
        SELECT id FROM public.projects WHERE user_id = auth.uid()
    )
);

-- Users can delete chat messages for their own projects
CREATE POLICY "Users can delete own project chat messages"
ON public.project_chat_messages FOR DELETE
USING (
    project_id IN (
        SELECT id FROM public.projects WHERE user_id = auth.uid()
    )
);

-- =====================================================
-- RLS Policies for project_edit_history
-- =====================================================

ALTER TABLE public.project_edit_history ENABLE ROW LEVEL SECURITY;

-- Users can view edit history for their own projects
CREATE POLICY "Users can view own project edit history"
ON public.project_edit_history FOR SELECT
USING (
    project_id IN (
        SELECT id FROM public.projects WHERE user_id = auth.uid()
    )
);

-- Users can insert edit history for their own projects
CREATE POLICY "Users can insert own project edit history"
ON public.project_edit_history FOR INSERT
WITH CHECK (
    project_id IN (
        SELECT id FROM public.projects WHERE user_id = auth.uid()
    )
);

-- Users can update edit history for their own projects (for undo/redo)
CREATE POLICY "Users can update own project edit history"
ON public.project_edit_history FOR UPDATE
USING (
    project_id IN (
        SELECT id FROM public.projects WHERE user_id = auth.uid()
    )
);

-- =====================================================
-- Grants
-- =====================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON public.project_chat_messages TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.project_edit_history TO authenticated;

-- =====================================================
-- Comments
-- =====================================================

COMMENT ON TABLE public.project_chat_messages IS 'Chat history for project interactions (generation, edits, questions)';
COMMENT ON COLUMN public.project_chat_messages.message_type IS 'Type of interaction: generation, edit, or question';
COMMENT ON COLUMN public.project_chat_messages.metadata IS 'Additional data like selected_element, file_path, edit_id';

COMMENT ON TABLE public.project_edit_history IS 'Component edit history for undo/redo functionality';
COMMENT ON COLUMN public.project_edit_history.old_code IS 'Component code before edit';
COMMENT ON COLUMN public.project_edit_history.new_code IS 'Component code after edit';
COMMENT ON COLUMN public.project_edit_history.is_reverted IS 'True if this edit has been undone';
COMMENT ON COLUMN public.project_edit_history.reverted_by_edit_id IS 'ID of the edit that reverted this one';
