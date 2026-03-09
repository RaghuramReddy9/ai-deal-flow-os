# Database models
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Deal(Base):
    __tablename__ = 'deals'
    
    # Primary Key
    id = Column(Integer, primary_key=True)
    
    # Base Fields (From Scraper)
    deal_name = Column(String(255), nullable=False)
    location = Column(String(255))
    asking_price = Column(Float)
    revenue = Column(Float)
    ebitda = Column(Float)
    description = Column(Text)
    source_url = Column(String(512), unique=True)
    source_name = Column(String(100))
    
    # AI-Generated Fields
    summary = Column(Text)
    industry = Column(String(100))
    score = Column(Integer)  # 0-100
    risks = Column(Text)
    stage = Column(String(50))  # early, growth, mature, declining
    recurring_revenue_signal = Column(String(50))
    growth_potential = Column(String(50))
    
    # Internal Operations Fields
    raw_price_text = Column(Text)
    raw_revenue_text = Column(Text)
    raw_ebitda_text = Column(Text)
    dedupe_hash = Column(String(64), unique=True)
    
    # Timestamps
    scraped_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)