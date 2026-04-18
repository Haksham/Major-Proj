-- SALF Database Initialization Script
-- PostgreSQL schema for Academic Credit Ledger

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    wallet_address VARCHAR(42) UNIQUE NOT NULL,
    employee_id VARCHAR(50) UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    department VARCHAR(100),
    designation VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'faculty',
    institution_id UUID,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_role CHECK (role IN ('admin', 'hod', 'faculty', 'reviewer'))
);

-- Institutions table
CREATE TABLE IF NOT EXISTS institutions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    address TEXT,
    website VARCHAR(255),
    accreditation_status VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Departments table
CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    institution_id UUID REFERENCES institutions(id),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL,
    hod_id UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(institution_id, code)
);

-- Contributions table
CREATE TABLE IF NOT EXISTS contributions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    blockchain_id VARCHAR(66),  -- Transaction hash
    faculty_id UUID REFERENCES users(id) NOT NULL,
    category VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    ipfs_hash VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'pending',
    base_points INTEGER DEFAULT 0,
    final_credits DECIMAL(10, 2) DEFAULT 0,
    quality_score DECIMAL(5, 2),
    novelty_score DECIMAL(5, 2),
    submission_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    evaluation_date TIMESTAMP WITH TIME ZONE,
    evaluated_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_status CHECK (status IN ('pending', 'under_review', 'evaluated', 'approved', 'rejected'))
);

-- Contribution categories lookup
CREATE TABLE IF NOT EXISTS contribution_categories (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    base_points INTEGER NOT NULL,
    ugc_mapping VARCHAR(100)
);

-- Insert default categories with UGC point mapping
INSERT INTO contribution_categories (code, name, description, base_points, ugc_mapping) VALUES
('JOURNAL_PAPER', 'Research Journal Paper', 'Publication in peer-reviewed journal', 25, 'UGC-CARE Listed Journal'),
('INTL_BOOK', 'International Book Publication', 'Book published by international publisher', 30, 'International Publishers'),
('NATL_BOOK', 'National Book Publication', 'Book published by national publisher', 20, 'National Publishers'),
('PATENT_GRANTED', 'Patent Granted', 'Granted patent (national/international)', 50, 'IPR - Patent'),
('PATENT_FILED', 'Patent Filed', 'Filed patent application', 25, 'IPR - Patent Application'),
('CONFERENCE_INTL', 'International Conference', 'Paper at international conference', 15, 'Conference Paper'),
('CONFERENCE_NATL', 'National Conference', 'Paper at national conference', 10, 'Conference Paper'),
('PROJECT_MAJOR', 'Major Research Project', 'Funded research project (>10 lakhs)', 40, 'Research Projects'),
('PROJECT_MINOR', 'Minor Research Project', 'Small funded research project', 20, 'Research Projects'),
('CONSULTANCY', 'Consultancy Work', 'Industry consultancy projects', 30, 'Consultancy')
ON CONFLICT (code) DO NOTHING;

-- Evaluations table
CREATE TABLE IF NOT EXISTS evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contribution_id UUID REFERENCES contributions(id) NOT NULL,
    evaluator_id UUID REFERENCES users(id) NOT NULL,
    quality_score DECIMAL(5, 2) NOT NULL,
    novelty_score DECIMAL(5, 2),
    category_scores JSONB DEFAULT '{}',
    comments TEXT,
    recommendation VARCHAR(20),
    fraud_check_passed BOOLEAN DEFAULT TRUE,
    fraud_check_details JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_recommendation CHECK (recommendation IN ('approve', 'reject', 'revise'))
);

-- Credit portfolios table
CREATE TABLE IF NOT EXISTS credit_portfolios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    faculty_id UUID REFERENCES users(id) UNIQUE NOT NULL,
    total_credits DECIMAL(10, 2) DEFAULT 0,
    journal_credits DECIMAL(10, 2) DEFAULT 0,
    book_credits DECIMAL(10, 2) DEFAULT 0,
    patent_credits DECIMAL(10, 2) DEFAULT 0,
    conference_credits DECIMAL(10, 2) DEFAULT 0,
    project_credits DECIMAL(10, 2) DEFAULT 0,
    other_credits DECIMAL(10, 2) DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Credit transfers table (for portability)
CREATE TABLE IF NOT EXISTS credit_transfers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    faculty_id UUID REFERENCES users(id) NOT NULL,
    from_institution_id UUID REFERENCES institutions(id),
    to_institution_id UUID REFERENCES institutions(id),
    credits_transferred DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    request_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    approval_date TIMESTAMP WITH TIME ZONE,
    approved_by UUID REFERENCES users(id),
    blockchain_tx_hash VARCHAR(66),
    CONSTRAINT valid_transfer_status CHECK (status IN ('pending', 'approved', 'rejected', 'completed'))
);

-- Audit log table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    old_value JSONB,
    new_value JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_contributions_faculty ON contributions(faculty_id);
CREATE INDEX IF NOT EXISTS idx_contributions_status ON contributions(status);
CREATE INDEX IF NOT EXISTS idx_contributions_category ON contributions(category);
CREATE INDEX IF NOT EXISTS idx_contributions_submission_date ON contributions(submission_date);
CREATE INDEX IF NOT EXISTS idx_evaluations_contribution ON evaluations(contribution_id);
CREATE INDEX IF NOT EXISTS idx_users_wallet ON users(wallet_address);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to tables with updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contributions_updated_at
    BEFORE UPDATE ON contributions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create view for faculty dashboard
CREATE OR REPLACE VIEW faculty_dashboard AS
SELECT 
    u.id as faculty_id,
    u.full_name,
    u.department,
    u.designation,
    COUNT(c.id) as total_contributions,
    COUNT(CASE WHEN c.status = 'approved' THEN 1 END) as approved_contributions,
    COUNT(CASE WHEN c.status = 'pending' THEN 1 END) as pending_contributions,
    COALESCE(SUM(CASE WHEN c.status = 'approved' THEN c.final_credits ELSE 0 END), 0) as total_credits,
    AVG(CASE WHEN c.status = 'approved' THEN c.quality_score END) as avg_quality_score
FROM users u
LEFT JOIN contributions c ON u.id = c.faculty_id
WHERE u.role = 'faculty'
GROUP BY u.id, u.full_name, u.department, u.designation;

-- Create view for admin reports
CREATE OR REPLACE VIEW admin_contribution_report AS
SELECT 
    c.category,
    COUNT(*) as total_submissions,
    COUNT(CASE WHEN c.status = 'approved' THEN 1 END) as approved,
    COUNT(CASE WHEN c.status = 'rejected' THEN 1 END) as rejected,
    COUNT(CASE WHEN c.status = 'pending' THEN 1 END) as pending,
    AVG(c.quality_score) as avg_quality_score,
    SUM(c.final_credits) as total_credits
FROM contributions c
GROUP BY c.category;

-- Grant permissions (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO salf_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO salf_user;

COMMENT ON TABLE users IS 'Faculty, HoD, and Admin users with wallet addresses';
COMMENT ON TABLE contributions IS 'Academic contributions submitted by faculty';
COMMENT ON TABLE evaluations IS 'AI and manual evaluations of contributions';
COMMENT ON TABLE credit_portfolios IS 'Aggregated credit scores for each faculty';
COMMENT ON TABLE credit_transfers IS 'Inter-institutional credit transfer records';
