-- ============================================================
-- DealMotion Marketing Engine - Database Schema
-- ============================================================
-- Supabase PostgreSQL schema for content tracking

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. TOPICS - Generated content topic ideas
-- ============================================================
CREATE TABLE IF NOT EXISTS topics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_type TEXT NOT NULL,  -- sales_tip, ai_news, hot_take, product_showcase
    title TEXT NOT NULL,
    hook TEXT NOT NULL,
    main_points JSONB DEFAULT '[]'::jsonb,
    cta TEXT,
    hashtags JSONB DEFAULT '[]'::jsonb,
    estimated_duration_seconds INTEGER DEFAULT 45,
    language TEXT DEFAULT 'nl',
    status TEXT DEFAULT 'pending',  -- pending, used, archived
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_topics_status ON topics(status);
CREATE INDEX idx_topics_type ON topics(content_type);
CREATE INDEX idx_topics_created ON topics(created_at DESC);

-- ============================================================
-- 2. SCRIPTS - Generated video scripts
-- ============================================================
CREATE TABLE IF NOT EXISTS scripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic_id UUID REFERENCES topics(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT,
    segments JSONB DEFAULT '[]'::jsonb,
    full_text TEXT,
    total_duration_seconds FLOAT DEFAULT 45,
    language TEXT DEFAULT 'nl',
    status TEXT DEFAULT 'pending',  -- pending, used, archived
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scripts_topic ON scripts(topic_id);
CREATE INDEX idx_scripts_status ON scripts(status);
CREATE INDEX idx_scripts_created ON scripts(created_at DESC);

-- ============================================================
-- 3. VIDEOS - Generated videos
-- ============================================================
CREATE TABLE IF NOT EXISTS videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    script_id UUID REFERENCES scripts(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT,
    video_url TEXT,
    audio_url TEXT,
    thumbnail_url TEXT,
    duration_seconds FLOAT,
    style TEXT DEFAULT 'professional',
    status TEXT DEFAULT 'pending',  -- pending, processing, ready, failed
    generation_id TEXT,  -- External ID from NanoBanana
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_videos_script ON videos(script_id);
CREATE INDEX idx_videos_status ON videos(status);
CREATE INDEX idx_videos_created ON videos(created_at DESC);

-- ============================================================
-- 4. YOUTUBE_UPLOADS - Uploaded videos to YouTube
-- ============================================================
CREATE TABLE IF NOT EXISTS youtube_uploads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    youtube_id TEXT NOT NULL,
    youtube_url TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    tags JSONB DEFAULT '[]'::jsonb,
    privacy_status TEXT DEFAULT 'public',
    is_short BOOLEAN DEFAULT true,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_youtube_video ON youtube_uploads(video_id);
CREATE INDEX idx_youtube_id ON youtube_uploads(youtube_id);
CREATE INDEX idx_youtube_published ON youtube_uploads(published_at DESC);

-- ============================================================
-- 5. PIPELINE_RUNS - Track daily pipeline executions
-- ============================================================
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_date DATE NOT NULL,
    status TEXT DEFAULT 'running',  -- running, completed, failed
    topics_generated INTEGER DEFAULT 0,
    scripts_generated INTEGER DEFAULT 0,
    videos_created INTEGER DEFAULT 0,
    videos_uploaded INTEGER DEFAULT 0,
    errors JSONB DEFAULT '[]'::jsonb,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_pipeline_date ON pipeline_runs(run_date DESC);
CREATE INDEX idx_pipeline_status ON pipeline_runs(status);

-- ============================================================
-- 6. SETTINGS - Configuration settings
-- ============================================================
CREATE TABLE IF NOT EXISTS settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key TEXT UNIQUE NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default settings
INSERT INTO settings (key, value, description) VALUES
('content_language', '"nl"', 'Default content language'),
('shorts_per_day', '1', 'Number of shorts to generate per day'),
('publish_hour', '10', 'Hour to publish content (24h format)'),
('auto_publish', 'true', 'Automatically publish to YouTube'),
('content_mix', '{"sales_tip": 40, "ai_news": 25, "hot_take": 20, "product_showcase": 15}', 'Content type distribution (percentage)')
ON CONFLICT (key) DO NOTHING;

-- ============================================================
-- FUNCTIONS
-- ============================================================

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers
CREATE TRIGGER topics_updated_at BEFORE UPDATE ON topics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER scripts_updated_at BEFORE UPDATE ON scripts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER videos_updated_at BEFORE UPDATE ON videos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER youtube_uploads_updated_at BEFORE UPDATE ON youtube_uploads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER settings_updated_at BEFORE UPDATE ON settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- VIEWS
-- ============================================================

-- Content pipeline overview
CREATE OR REPLACE VIEW content_pipeline AS
SELECT 
    t.id AS topic_id,
    t.title,
    t.content_type,
    t.status AS topic_status,
    s.id AS script_id,
    s.status AS script_status,
    v.id AS video_id,
    v.status AS video_status,
    y.youtube_id,
    y.youtube_url,
    y.views,
    t.created_at
FROM topics t
LEFT JOIN scripts s ON s.topic_id = t.id
LEFT JOIN videos v ON v.script_id = s.id
LEFT JOIN youtube_uploads y ON y.video_id = v.id
ORDER BY t.created_at DESC;

-- Daily stats
CREATE OR REPLACE VIEW daily_stats AS
SELECT 
    DATE(created_at) AS date,
    COUNT(*) FILTER (WHERE content_type = 'sales_tip') AS sales_tips,
    COUNT(*) FILTER (WHERE content_type = 'ai_news') AS ai_news,
    COUNT(*) FILTER (WHERE content_type = 'hot_take') AS hot_takes,
    COUNT(*) FILTER (WHERE content_type = 'product_showcase') AS product_showcases,
    COUNT(*) AS total
FROM topics
GROUP BY DATE(created_at)
ORDER BY date DESC;

