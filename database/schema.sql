CREATE TABLE topics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  main_keyword TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE keywords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keyword TEXT NOT NULL,
    topic_id UUID NOT NULL,
    search_volume INT,
    competition_score DOUBLE PRECISION,
    last_searched_at TIMESTAMPTZ,
    CONSTRAINT fk_keywords_topic
        FOREIGN KEY (topic_id)
        REFERENCES topics(id)
        ON DELETE CASCADE
);

CREATE TABLE channels (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  youtube_channel_id TEXT UNIQUE NOT NULL,
  channel_name TEXT,
  channel_url TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_scraped_at TIMESTAMPTZ,
  scrape_frequency_hours INT DEFAULT 24
);

CREATE TABLE videos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  youtube_video_id TEXT UNIQUE NOT NULL,
  channel_id UUID NOT NULL,
  title TEXT,
  description TEXT,
  published_at TIMESTAMP WITH TIME ZONE,
  duration_seconds INT,
  is_shorts BOOLEAN,
  discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  thumbnail_url TEXT,
  transcript TEXT,
  language TEXT,
  raw_json JSONB,
  scrape_priority INT,
  discovered_via_query TEXT,
  search_position INT,

  deleted_at TIMESTAMPTZ,

 first_seen_at TIMESTAMPTZ DEFAULT NOW(),
 last_updated_at TIMESTAMPTZ DEFAULT NOW(),


  CONSTRAINT fk_video_to_channel
    FOREIGN KEY (channel_id)
    REFERENCES channels(id)
    ON DELETE CASCADE
);

CREATE TABLE video_tags (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  video_id UUID NOT NULL,
  tag TEXT NOT NULL,

  CONSTRAINT fk_tags_to_video
    FOREIGN KEY (video_id)
    REFERENCES videos(id)
    ON DELETE CASCADE
);

CREATE TABLE topic_videos (
  topic_id UUID NOT NULL,
  video_id UUID NOT NULL,
  relevance_score double precision DEFAULT NULL,
  PRIMARY KEY (topic_id, video_id),

  CONSTRAINT fk_topic_videos_link
    FOREIGN KEY (topic_id)
    REFERENCES topics(id)
    ON DELETE CASCADE,

  CONSTRAINT fk_video_link
    FOREIGN KEY (video_id)
    REFERENCES videos(id)
    ON DELETE CASCADE
);


CREATE TABLE video_thumbnails (
  video_id UUID PRIMARY KEY REFERENCES videos(id) ON DELETE CASCADE,
  dominant_color_hex TEXT,
  brightness DOUBLE PRECISION,
  saturation DOUBLE PRECISION,
  has_face BOOLEAN DEFAULT FALSE,
  face_emotion TEXT,
  text_on_image TEXT,
  text_density DOUBLE PRECISION,
  contrast_score DOUBLE PRECISION,
  is_high_quality BOOLEAN,
  analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE video_metrics_history (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL,
    view_count BIGINT,
    like_count BIGINT,
    comment_count BIGINT,
  view_diff BIGINT DEFAULT 0,
  search_rank INT,
  collection_source TEXT, -- 'search', 'manual', 'discovery'
  velocity_per_hour FLOAT DEFAULT 0,
  is_trending BOOLEAN DEFAULT FALSE,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  CONSTRAINT fk_metrics_to_video
    FOREIGN KEY (video_id)
        REFERENCES videos(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_metrics_video_time ON public.video_metrics_history (video_id, collected_at DESC);

CREATE TABLE channel_metrics_history (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id uuid NOT NULL,

    subscribers BIGINT,
    total_views BIGINT,
    video_count INT,

    subs_diff BIGINT DEFAULT 0,
    views_diff BIGINT DEFAULT 0,

    collected_at timestamp with time zone DEFAULT now(),

    CONSTRAINT fk_metrics_to_channels
    FOREIGN KEY (channel_id)
        REFERENCES public.channels (id) MATCH SIMPLE
        ON DELETE CASCADE
);


CREATE INDEX idx_channel_metrics_history_cid_time
ON public.channel_metrics_history (channel_id, collected_at DESC);

CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL,
    youtube_comment_id TEXT UNIQUE NOT NULL,
    comment_text TEXT,
    likes INT DEFAULT 0,
    sentiment_score double precision,
    is_question boolean DEFAULT FALSE,

    published_at timestamp with time zone,
    discovered_at timestamp with time zone DEFAULT now(),

    CONSTRAINT fk_comment_to_video FOREIGN KEY (video_id)
        REFERENCES videos (id) ON DELETE CASCADE
);

CREATE TABLE comment_keywords (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    comment_id uuid NOT NULL,
    keyword text,

    relevance_score DOUBLE PRECISION DEFAULT NULL,

    CONSTRAINT fk_keyword_to_comment FOREIGN KEY (comment_id)
        REFERENCES comments(id) ON DELETE CASCADE
);

CREATE TABLE topic_channels (
  topic_id UUID NOT NULL,
  channel_id UUID NOT NULL,

  relevance_score double precision DEFAULT NULL,

  assigned_at timestamp with time zone DEFAULT now(),

  -- 'auto' (script) or 'manual'
  assignment_method text DEFAULT 'auto',

  PRIMARY KEY (topic_id, channel_id),
  CONSTRAINT fk_topic_channel_link FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE,
  CONSTRAINT fk_channel_link FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE
);

CREATE TABLE video_keywords (
    video_id uuid NOT NULL,
    keyword text NOT NULL,
    source text NOT NULL, -- title, tags, description, transcript

    relevance_score DOUBLE PRECISION DEFAULT NULL,

    occurrence_count integer DEFAULT 1,

    PRIMARY KEY (video_id, keyword, source),
    CONSTRAINT fk_keywords_to_video
        FOREIGN KEY (video_id) REFERENCES public.videos(id) ON DELETE CASCADE
);


CREATE INDEX idx_video_keywords_val ON public.video_keywords(keyword);

CREATE INDEX idx_keywords_topic_id ON keywords(topic_id);
CREATE INDEX idx_videos_channel_id ON videos(channel_id);
CREATE INDEX idx_video_tags_video_id ON video_tags(video_id);
CREATE INDEX idx_topic_videos_topic_id ON topic_videos(topic_id);
CREATE INDEX idx_topic_channels_topic_id ON topic_channels(topic_id);
CREATE INDEX idx_comments_video_id ON comments(video_id);

-- Finding frequently query videos by published date
CREATE INDEX idx_videos_published_at ON videos(published_at DESC);

-- Finding recent shorts vs regular videos
CREATE INDEX idx_videos_is_shorts ON videos(is_shorts) WHERE is_shorts = true;

-- Filtering out deleted videos
CREATE INDEX idx_videos_deleted_at ON videos(deleted_at) WHERE deleted_at IS NULL;

-- Finding trending videos
CREATE INDEX idx_metrics_trending ON video_metrics_history(is_trending, collected_at DESC)
WHERE is_trending = true;

-- Comment sentiment analysis
CREATE INDEX idx_comments_sentiment ON comments(sentiment_score);
CREATE INDEX idx_comments_published ON comments(published_at DESC);

-- Prevent negative metrics
ALTER TABLE video_metrics_history
  ADD CONSTRAINT check_positive_views CHECK (view_count >= 0),
  ADD CONSTRAINT check_positive_likes CHECK (like_count >= 0);

-- For finding top videos in a topic by recent metrics
CREATE INDEX idx_topic_videos_relevance
ON topic_videos(topic_id, relevance_score DESC);

-- For analyzing channel growth over time
CREATE INDEX idx_channel_metrics_composite
ON channel_metrics_history(channel_id, collected_at DESC, subscribers);

-- For keyword searches across video content
CREATE INDEX idx_video_keywords_composite
ON video_keywords(keyword, relevance_score DESC);

CREATE TABLE scrape_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic_id UUID REFERENCES topics(id),
  keyword TEXT,
  status TEXT CHECK (status IN ('pending', 'running', 'completed', 'failed')),
  videos_found INT DEFAULT 0,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  error_message TEXT
);

CREATE TABLE api_quota_usage (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  endpoint TEXT NOT NULL, -- 'search', 'videos', 'channels', etc.
  quota_cost INT NOT NULL,
  requested_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_quota_daily ON api_quota_usage (
    ( (requested_at AT TIME ZONE 'UTC')::DATE ),
    endpoint
);

CREATE TABLE video_categories (
  video_id UUID PRIMARY KEY REFERENCES videos(id) ON DELETE CASCADE,
  primary_category TEXT,
  secondary_categories TEXT[],
  auto_detected BOOLEAN DEFAULT true,
  confidence_score DOUBLE PRECISION
);

CREATE TABLE channel_relationships (
  channel_id UUID REFERENCES channels(id),
  related_channel_id UUID REFERENCES channels(id),
  relationship_type TEXT, -- 'competitor', 'similar', 'collaborator'
  overlap_score DOUBLE PRECISION,
  PRIMARY KEY (channel_id, related_channel_id)
);

CREATE TABLE niche_difficulty (
  topic_id UUID PRIMARY KEY REFERENCES topics(id),
  competition_level TEXT, -- 'low', 'medium', 'high'
  avg_subscriber_requirement BIGINT,
  avg_video_quality_score DOUBLE PRECISION,
  barrier_to_entry_score DOUBLE PRECISION,
  recommendation TEXT,
  analyzed_at TIMESTAMPTZ DEFAULT NOW()
);
