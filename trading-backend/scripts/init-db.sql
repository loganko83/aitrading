-- TradingBot AI - PostgreSQL Initialization Script
-- Executed on first container startup

-- Create database if not exists (already handled by POSTGRES_DB env var)

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create read-only user for monitoring (optional)
-- CREATE USER tradingbot_readonly WITH PASSWORD 'readonly_password';
-- GRANT CONNECT ON DATABASE tradingbot TO tradingbot_readonly;
-- GRANT USAGE ON SCHEMA public TO tradingbot_readonly;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO tradingbot_readonly;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO tradingbot_readonly;

-- Performance settings (add to postgresql.conf in production)
-- ALTER SYSTEM SET shared_buffers = '256MB';
-- ALTER SYSTEM SET effective_cache_size = '1GB';
-- ALTER SYSTEM SET maintenance_work_mem = '64MB';
-- ALTER SYSTEM SET checkpoint_completion_target = '0.9';
-- ALTER SYSTEM SET wal_buffers = '16MB';
-- ALTER SYSTEM SET default_statistics_target = '100';
-- ALTER SYSTEM SET random_page_cost = '1.1';
-- ALTER SYSTEM SET effective_io_concurrency = '200';
-- ALTER SYSTEM SET work_mem = '4MB';
-- ALTER SYSTEM SET min_wal_size = '1GB';
-- ALTER SYSTEM SET max_wal_size = '4GB';

-- Logging (for slow query analysis)
-- ALTER SYSTEM SET log_min_duration_statement = '1000'; -- Log queries > 1 second
-- ALTER SYSTEM SET log_line_prefix = '%m [%p] %q%u@%d ';
-- ALTER SYSTEM SET log_statement = 'none';

-- Connection settings
-- ALTER SYSTEM SET max_connections = '100';

-- Reload configuration
-- SELECT pg_reload_conf();

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'TradingBot AI database initialized successfully!';
END
$$;
