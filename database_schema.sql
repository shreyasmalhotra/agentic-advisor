-- Supabase Database Schema for Agentic Portfolio Advisor

-- 1) Portfolio Sessions Table - stores each questionnaire session
CREATE TABLE IF NOT EXISTS portfolio_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'questionnaire_started',
    questionnaire_responses JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE NULL
);

-- 2) Chat Messages Table - stores all chat interactions
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('user', 'agent', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (session_id) REFERENCES portfolio_sessions(session_id) ON DELETE CASCADE
);

-- 3) Analysis Results Table - stores AI analysis and recommendations
CREATE TABLE IF NOT EXISTS analysis_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,
    results JSONB NOT NULL,
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (session_id) REFERENCES portfolio_sessions(session_id) ON DELETE CASCADE
);

-- 4) User Preferences Table - stores user settings and preferences
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    preference_key VARCHAR(100) NOT NULL,
    preference_value JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (session_id) REFERENCES portfolio_sessions(session_id) ON DELETE CASCADE,
    UNIQUE(session_id, preference_key)
);

-- 5) Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_portfolio_sessions_session_id ON portfolio_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_sessions_status ON portfolio_sessions(status);
CREATE INDEX IF NOT EXISTS idx_portfolio_sessions_created_at ON portfolio_sessions(created_at);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_messages_type ON chat_messages(message_type);

CREATE INDEX IF NOT EXISTS idx_analysis_results_session_id ON analysis_results(session_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_type ON analysis_results(analysis_type);

-- 6) Row Level Security (RLS) policies
ALTER TABLE portfolio_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Allow all operations for now (you can restrict this later)
CREATE POLICY "Allow all operations on portfolio_sessions" ON portfolio_sessions FOR ALL USING (true);
CREATE POLICY "Allow all operations on chat_messages" ON chat_messages FOR ALL USING (true);
CREATE POLICY "Allow all operations on analysis_results" ON analysis_results FOR ALL USING (true);
CREATE POLICY "Allow all operations on user_preferences" ON user_preferences FOR ALL USING (true);

-- 7) Functions for common operations
CREATE OR REPLACE FUNCTION update_session_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 8) Triggers
CREATE TRIGGER update_portfolio_sessions_timestamp
    BEFORE UPDATE ON portfolio_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_session_timestamp();

CREATE TRIGGER update_user_preferences_timestamp
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_session_timestamp();

-- 10) View for easy session overview
CREATE OR REPLACE VIEW session_overview AS
SELECT 
    ps.session_id,
    ps.status,
    ps.created_at,
    ps.updated_at,
    ps.completed_at,
    ps.questionnaire_responses,
    COUNT(cm.id) as message_count,
    COUNT(ar.id) as analysis_count
FROM portfolio_sessions ps
LEFT JOIN chat_messages cm ON ps.session_id = cm.session_id
LEFT JOIN analysis_results ar ON ps.session_id = ar.session_id
GROUP BY ps.session_id, ps.status, ps.created_at, ps.updated_at, ps.completed_at, ps.questionnaire_responses; 