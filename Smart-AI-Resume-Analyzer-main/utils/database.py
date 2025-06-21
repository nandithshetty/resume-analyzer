import os
import json
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Read DB path from environment variable or use default
DB_PATH = os.getenv("DB_PATH", "resume_data.db")

# Create the base class for declarative models
Base = declarative_base()

# Resume model
class Resume(Base):
    __tablename__ = 'resumes'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100))
    job_role = Column(String(100))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

# Resume analysis model
class Analysis(Base):
    __tablename__ = 'analyses'
    
    id = Column(Integer, primary_key=True)
    resume_id = Column(Integer)
    analysis_data = Column(Text)  # JSON stored as string
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# AI analysis model
class AIAnalysis(Base):
    __tablename__ = 'ai_analyses'
    
    id = Column(Integer, primary_key=True)
    resume_id = Column(Integer)
    model_used = Column(String(100))
    resume_score = Column(Integer)
    job_role = Column(String(100))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# Database session manager
class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def save_resume(self, user_id, job_role, content):
        resume = Resume(user_id=user_id, job_role=job_role, content=content)
        self.session.add(resume)
        self.session.commit()
        return resume.id
    
    def get_resume(self, resume_id):
        return self.session.query(Resume).filter(Resume.id == resume_id).first()
    
    def get_user_resumes(self, user_id):
        return self.session.query(Resume).filter(Resume.user_id == user_id).all()
    
    def save_analysis(self, resume_id, analysis_data):
        analysis = Analysis(resume_id=resume_id, analysis_data=analysis_data)
        self.session.add(analysis)
        self.session.commit()
        return analysis.id
    
    def get_analysis(self, analysis_id):
        return self.session.query(Analysis).filter(Analysis.id == analysis_id).first()
    
    def get_resume_analyses(self, resume_id):
        return self.session.query(Analysis).filter(Analysis.resume_id == resume_id).all()
    
    def close(self):
        self.session.close()

# Create new DB session manually
def get_database_connection():
    engine = create_engine(f'sqlite:///{DB_PATH}')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

# Save raw resume data
def save_resume_data(resume_data):
    session = get_database_connection()
    try:
        resume_json = json.dumps(resume_data)
        resume = Resume(
            user_id="anonymous",
            job_role=resume_data.get('target_role', 'Unknown'),
            content=resume_json
        )
        session.add(resume)
        session.commit()
        return resume.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

# Save AI analysis data
def save_ai_analysis_data(resume_id, analysis_data):
    session = get_database_connection()
    try:
        ai_analysis = AIAnalysis(
            resume_id=resume_id,
            model_used=analysis_data.get('model_used', 'Unknown'),
            resume_score=analysis_data.get('resume_score', 0),
            job_role=analysis_data.get('job_role', 'Unknown')
        )
        session.add(ai_analysis)
        session.commit()
        return ai_analysis.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

# Retrieve aggregated analysis stats
def get_ai_analysis_statistics():
    session = get_database_connection()
    try:
        total_analyses = session.query(func.count(AIAnalysis.id)).scalar() or 0
        average_score = session.query(func.avg(AIAnalysis.resume_score)).scalar() or 0

        model_usage_query = session.query(
            AIAnalysis.model_used, func.count(AIAnalysis.id)
        ).group_by(AIAnalysis.model_used).all()
        model_usage = {model: count for model, count in model_usage_query}

        job_roles_query = session.query(
            AIAnalysis.job_role, func.count(AIAnalysis.id)
        ).group_by(AIAnalysis.job_role).all()
        job_roles = {role: count for role, count in job_roles_query}

        return {
            'total_analyses': total_analyses,
            'average_score': float(average_score),
            'model_usage': model_usage,
            'job_roles': job_roles
        }
    except Exception as e:
        print(f"Error getting AI analysis statistics: {e}")
        return None
    finally:
        session.close()
