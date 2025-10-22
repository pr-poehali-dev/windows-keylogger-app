CREATE TABLE IF NOT EXISTS news_items (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    title TEXT,
    original_text TEXT,
    translated_title TEXT,
    translated_text TEXT,
    image_url TEXT,
    status TEXT DEFAULT 'pending',
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS news_sources (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    selector_title TEXT,
    selector_text TEXT,
    selector_image TEXT,
    check_interval_minutes INTEGER DEFAULT 60,
    last_checked_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS moderation_queue (
    id SERIAL PRIMARY KEY,
    news_id INTEGER REFERENCES news_items(id),
    telegram_message_id INTEGER,
    moderator_chat_id TEXT,
    action TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_news_status ON news_items(status);
CREATE INDEX IF NOT EXISTS idx_news_url ON news_items(url);
CREATE INDEX IF NOT EXISTS idx_sources_active ON news_sources(is_active);
