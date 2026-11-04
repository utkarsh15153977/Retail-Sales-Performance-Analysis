-- ==============================================================================
-- Portfolio Project: Retail Sales Performance Analysis
-- Script: 01_create_database.sql
-- Purpose: Initialize PostgreSQL database, roles, extensions, and schema structure.
-- Dialect: PostgreSQL 12+ (Tested on PostgreSQL 17)
-- Author: Senior Data Analyst & SQL Developer
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. Database Creation
-- Note: In PostgreSQL, CREATE DATABASE cannot be executed inside a multi-command
-- transaction block. Run this statement individually or via psql / pgAdmin.
-- ------------------------------------------------------------------------------
-- Terminate existing connections if recreating (use with caution in dev environments)
-- SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'retail_sales_db' AND pid <> pg_backend_pid();

-- Create the database with UTF-8 encoding
-- (Uncomment the line below when running from a superuser connection like 'postgres')
-- CREATE DATABASE retail_sales_db WITH ENCODING = 'UTF8' LC_COLLATE = 'C' LC_CTYPE = 'C';

-- ------------------------------------------------------------------------------
-- 2. Schema Architecture
-- We implement a modern 3-layer medallion/layered database architecture:
--   - staging:   Raw ingestion zone (permissive types, unconstrained for ELT).
--   - core:      Enterprise Data Model / Star Schema (cleaned, typed, PK/FK constraints).
--   - analytics: Analytical views, materialized summaries, and reporting marts.
-- ------------------------------------------------------------------------------

-- Ensure schemas exist
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Document schemas
COMMENT ON SCHEMA staging IS 'Staging layer for raw CSV ingestion with flexible typing and preliminary audit tracking.';
COMMENT ON SCHEMA core IS 'Core cleansed dimensional models and transaction tables adhering to enterprise data standards.';
COMMENT ON SCHEMA analytics IS 'Semantic reporting layer containing pre-aggregated views and analytical marts.';

-- ------------------------------------------------------------------------------
-- 3. Required Extensions
-- Useful for high-performance indexing, UUID generation, and fuzzy matching.
-- ------------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ------------------------------------------------------------------------------
-- 4. Session Configuration Defaults
-- ------------------------------------------------------------------------------
-- Set search path to prioritize core and analytics schemas
ALTER DATABASE CURRENT_DATABASE() SET search_path TO core, analytics, staging, public;

-- Set timezone to UTC for standardized temporal reporting
SET timezone = 'UTC';
