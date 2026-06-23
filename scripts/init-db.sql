-- TrendScope 数据库初始化脚本
-- PostgreSQL 16

-- 平台定义表
CREATE TABLE IF NOT EXISTS platforms (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(32) UNIQUE NOT NULL,
    name        VARCHAR(64) NOT NULL,
    name_en     VARCHAR(128),
    icon_url    VARCHAR(512),
    base_url    VARCHAR(512),
    category    VARCHAR(32) DEFAULT 'general',
    is_active   BOOLEAN DEFAULT true,
    crawl_interval INTEGER DEFAULT 300,
    crawl_config JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 热门话题表
CREATE TABLE IF NOT EXISTS trending_topics (
    id              BIGSERIAL PRIMARY KEY,
    platform_id     INT NOT NULL REFERENCES platforms(id) ON DELETE CASCADE,
    rank            INT NOT NULL,
    title           VARCHAR(512) NOT NULL,
    hot_value       VARCHAR(128),
    hot_value_norm  DECIMAL(15,2),
    topic_url       VARCHAR(2048),
    category        VARCHAR(64),
    snapshot_at     TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trending_platform_snapshot
    ON trending_topics(platform_id, snapshot_at DESC);
CREATE INDEX IF NOT EXISTS idx_trending_snapshot
    ON trending_topics(snapshot_at DESC);
CREATE INDEX IF NOT EXISTS idx_trending_title
    ON trending_topics USING gin(to_tsvector('simple', title));
CREATE INDEX IF NOT EXISTS idx_trending_norm
    ON trending_topics(hot_value_norm DESC);

-- 热门文章表
CREATE TABLE IF NOT EXISTS hot_articles (
    id              BIGSERIAL PRIMARY KEY,
    platform_id     INT NOT NULL REFERENCES platforms(id) ON DELETE CASCADE,
    title           VARCHAR(1024) NOT NULL,
    summary         TEXT,
    content_text    TEXT,
    images          JSONB DEFAULT '[]',
    video_url       VARCHAR(2048),
    author_name     VARCHAR(256),
    author_avatar   VARCHAR(512),
    source_url      VARCHAR(2048) NOT NULL,
    read_count      BIGINT DEFAULT 0,
    like_count      BIGINT DEFAULT 0,
    comment_count   BIGINT DEFAULT 0,
    share_count     BIGINT DEFAULT 0,
    publish_at      TIMESTAMPTZ,
    status          VARCHAR(16) DEFAULT 'pending',
    snapshot_at     TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_articles_platform_snapshot
    ON hot_articles(platform_id, snapshot_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_publish
    ON hot_articles(publish_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_read_count
    ON hot_articles(read_count DESC);
CREATE INDEX IF NOT EXISTS idx_articles_status
    ON hot_articles(status);
CREATE INDEX IF NOT EXISTS idx_articles_title_gin
    ON hot_articles USING gin(to_tsvector('simple', title));
CREATE INDEX IF NOT EXISTS idx_articles_content_gin
    ON hot_articles USING gin(to_tsvector('simple', content_text));

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id              BIGSERIAL PRIMARY KEY,
    username        VARCHAR(64) UNIQUE NOT NULL,
    email           VARCHAR(256),
    phone           VARCHAR(20),
    password_hash   VARCHAR(256) NOT NULL,
    nickname        VARCHAR(128),
    avatar_url      VARCHAR(512),
    role            VARCHAR(16) DEFAULT 'user',
    status          VARCHAR(16) DEFAULT 'active',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);

-- 用户收藏表
CREATE TABLE IF NOT EXISTS user_favorites (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    article_id  BIGINT NOT NULL REFERENCES hot_articles(id) ON DELETE CASCADE,
    folder_id   BIGINT DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, article_id)
);

CREATE INDEX IF NOT EXISTS idx_favorites_user ON user_favorites(user_id);

-- 用户订阅表
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform_id     INT REFERENCES platforms(id) ON DELETE SET NULL,
    keywords        JSONB DEFAULT '[]',
    notify_email    BOOLEAN DEFAULT false,
    notify_webpush  BOOLEAN DEFAULT true,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON user_subscriptions(user_id);

-- 通知表
CREATE TABLE IF NOT EXISTS notifications (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type        VARCHAR(32) NOT NULL,
    title       VARCHAR(256) NOT NULL,
    content     TEXT,
    reference_id BIGINT,
    is_read     BOOLEAN DEFAULT false,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read, created_at DESC);

-- API Key 表
CREATE TABLE IF NOT EXISTS api_keys (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash        VARCHAR(256) UNIQUE NOT NULL,
    key_prefix      VARCHAR(16) NOT NULL,
    name            VARCHAR(128),
    rate_limit      INT DEFAULT 100,
    is_active       BOOLEAN DEFAULT true,
    last_used_at    TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_apikeys_user ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_apikeys_hash ON api_keys(key_hash);

-- API 调用记录表
CREATE TABLE IF NOT EXISTS api_usage_logs (
    id          BIGSERIAL PRIMARY KEY,
    api_key_id  INT REFERENCES api_keys(id) ON DELETE SET NULL,
    endpoint    VARCHAR(256) NOT NULL,
    method      VARCHAR(16) NOT NULL,
    status_code INT,
    ip_address  VARCHAR(64),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_apikey ON api_usage_logs(api_key_id, created_at DESC);

-- 采集日志表
CREATE TABLE IF NOT EXISTS crawl_logs (
    id              BIGSERIAL PRIMARY KEY,
    platform_id     INT NOT NULL REFERENCES platforms(id) ON DELETE CASCADE,
    status          VARCHAR(16) NOT NULL DEFAULT 'running',
    items_count     INT DEFAULT 0,
    error_message   TEXT,
    duration_ms     INT,
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    finished_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_crawl_platform ON crawl_logs(platform_id, created_at DESC);

-- 插入默认平台数据
INSERT INTO platforms (code, name, name_en, category, crawl_interval) VALUES
    ('weibo',       '微博',     'Weibo',        'social',    60),
    ('baidu',       '百度',     'Baidu',        'general',   180),
    ('zhihu',       '知乎',     'Zhihu',        'knowledge', 180),
    ('bilibili',    'B站',      'Bilibili',     'video',     180),
    ('toutiao',     '今日头条',  'Toutiao',      'news',      300),
    ('douyin',      '抖音',     'Douyin',       'video',     900),
    ('xiaohongshu', '小红书',   'Xiaohongshu',  'lifestyle', 900),
    ('youtube',     'YouTube',  'YouTube',      'video',     900),
    ('weixin_article', '公众号', 'WeChatArticle','article',   1800),
    ('shipinhao',   '视频号',   'Shipinhao',    'video',     1800),
    ('tiktok',      'TikTok',   'TikTok',       'video',     3600),
    ('x_twitter',   'X',        'X/Twitter',    'social',    1800)
ON CONFLICT (code) DO NOTHING;

-- 插入默认管理员（密码: admin123，bcrypt hash）
INSERT INTO users (username, email, password_hash, role, status) VALUES
    ('admin', 'admin@trendscope.cn', '$2a$12$LJ3m4ys3Lg3YOCwKkp/wte1mX5GqOZyOSxV5b.VQ0qPqF7.Pr1.zu', 'admin', 'active')
ON CONFLICT (username) DO NOTHING;
