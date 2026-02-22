-- Uniflow Database Schema for Supabase
-- Run this in the Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (with role and department columns)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    organization_name VARCHAR(255),
    organization_nif VARCHAR(50),
    role VARCHAR(50) DEFAULT 'viewer',
    department VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Proposals table
CREATE TABLE IF NOT EXISTS proposals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT DEFAULT '',
    pinned BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'draft',
    final_draft BOOLEAN DEFAULT FALSE,
    proposal_revision TEXT,
    assigned_to_email VARCHAR(255),  -- Email of user who can see this revision (NULL = owner only)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_org ON users(organization_name);
CREATE INDEX IF NOT EXISTS idx_proposals_user_id ON proposals(user_id);
CREATE INDEX IF NOT EXISTS idx_proposals_created_at ON proposals(created_at);
CREATE INDEX IF NOT EXISTS idx_proposals_assigned_to ON proposals(assigned_to_email);

-- If upgrading from previous schema, add role column:
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'viewer';

-- If upgrading from previous schema, add department column:
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS department VARCHAR(255);

-- If upgrading from previous schema, add assigned_to_email column:
-- ALTER TABLE proposals ADD COLUMN IF NOT EXISTS assigned_to_email VARCHAR(255);

-- Active Tenders table - stores published tenders
CREATE TABLE IF NOT EXISTS active_tenders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    
    -- Required Fields
    title VARCHAR(500) NOT NULL,
    organization_nif VARCHAR(50) NOT NULL,
    price INTEGER NOT NULL DEFAULT 0,
    
    -- Dates (auto-calculated)
    submission_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    submission_deadline TIMESTAMP WITH TIME ZONE NOT NULL,
    contract_expiry_date TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Content & Audit
    tender_content TEXT NOT NULL,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for active_tenders
CREATE INDEX IF NOT EXISTS idx_active_tenders_proposal ON active_tenders(proposal_id);
CREATE INDEX IF NOT EXISTS idx_active_tenders_nif ON active_tenders(organization_nif);
CREATE INDEX IF NOT EXISTS idx_active_tenders_submission_date ON active_tenders(submission_date DESC);
CREATE INDEX IF NOT EXISTS idx_active_tenders_created_by ON active_tenders(created_by);

