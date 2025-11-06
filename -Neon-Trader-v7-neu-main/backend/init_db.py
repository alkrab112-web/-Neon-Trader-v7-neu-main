#!/usr/bin/env python3
"""
Database Initialization Script
Creates all tables in PostgreSQL
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from database import init_db, engine, Base
from models.database_models import (
    User, UserSettings, Portfolio, Trade, Platform,
    PortfolioSnapshot, AIRecommendation, DailyPlan,
    AuditLog, RefreshToken
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Initialize database"""
    try:
        logger.info("Starting database initialization...")
        logger.info(f"Creating tables for models: User, Portfolio, Trade, Platform, etc.")
        
        # Create all tables
        await init_db()
        
        logger.info("✅ Database initialization completed successfully!")
        logger.info("All tables created in PostgreSQL")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
