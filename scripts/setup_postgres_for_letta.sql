-- Run as a Postgres superuser (e.g. your macOS user or postgres).
-- Creates the role and database Letta expects when LETTA_PG_URI is unset.
-- Requires: PostgreSQL with pgvector extension available.

CREATE ROLE letta WITH LOGIN PASSWORD 'letta';
CREATE DATABASE letta OWNER letta;
\c letta
CREATE EXTENSION IF NOT EXISTS vector;
