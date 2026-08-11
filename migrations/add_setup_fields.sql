-- Supabase Database Initialization Script
-- Run this in Supabase SQL Editor to set up the database

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop existing user_profiles table if it exists
DROP TABLE IF EXISTS user_profiles CASCADE;

-- Create user_profiles table with new setup fields
CREATE TABLE user_profiles (
    sub TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    name TEXT,
    work_description TEXT,
    industry TEXT,
    responsibilities TEXT,
    company_name TEXT,
    work_environment TEXT,
    google_refresh_token TEXT,
    updated_at TEXT NOT NULL
);

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);

-- Create knowledge_chunk_vectors table (for RAG)
CREATE TABLE IF NOT EXISTS knowledge_chunk_vectors (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    user_sub TEXT NOT NULL,
    source_file TEXT NOT NULL,
    source_path TEXT,
    chunk_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(3072) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for RAG queries
CREATE INDEX IF NOT EXISTS idx_knowledge_chunk_vectors_user_sub ON knowledge_chunk_vectors(user_sub);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunk_vectors_document_id ON knowledge_chunk_vectors(document_id);