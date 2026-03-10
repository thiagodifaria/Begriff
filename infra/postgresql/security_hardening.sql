-- Run as a privileged database user in PostgreSQL.
-- This script provides baseline controls for RLS, column restriction, pgcrypto and pgaudit.

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pgaudit;

-- Application role (example).
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'begriff_app') THEN
        CREATE ROLE begriff_app LOGIN PASSWORD 'change_me_now';
    END IF;
END $$;

-- Restrict table-level permissions and allow only controlled access.
REVOKE ALL ON TABLE public.transactions FROM PUBLIC;
GRANT SELECT, INSERT, UPDATE ON TABLE public.transactions TO begriff_app;

-- Optional: restrict columns containing PII/sensitive values.
REVOKE SELECT (hashed_password) ON TABLE public.users FROM begriff_app;

-- Row Level Security for user-owned data.
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS user_isolation_transactions ON public.transactions;
CREATE POLICY user_isolation_transactions
    ON public.transactions
    USING (user_id = current_setting('app.current_user_id', true)::int)
    WITH CHECK (user_id = current_setting('app.current_user_id', true)::int);

-- Audit statements.
ALTER SYSTEM SET pgaudit.log = 'read,write,ddl';
ALTER SYSTEM SET pgaudit.log_parameter = on;
SELECT pg_reload_conf();
