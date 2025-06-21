"""
Smart Resume AI - Main Application
"""
import time
from PIL import Image
from jobs.job_search import render_job_search
from datetime import datetime
from ui_components import (
    apply_modern_styles, hero_section, feature_card, about_section,
    page_header, render_analytics_section, render_activity_section,
    render_suggestions_section
)
from feedback.feedback import FeedbackManager
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from docx import Document
import io
import base64
import plotly.graph_objects as go
from streamlit_lottie import st_lottie
import requests
from dashboard.dashboard import DashboardManager
from config.courses import COURSES_BY_CATEGORY, RESUME_VIDEOS, INTERVIEW_VIDEOS, get_courses_for_role, get_category_for_role
from config.job_roles import JOB_ROLES
from config.database import (
    get_database_connection, save_resume_data, save_analysis_data,
    init_database, 
)
from utils.resume_analyzer import ResumeAnalyzer
import traceback
import plotly.express as px
import pandas as pd
import json
import streamlit as st
import datetime

# Set page config at the very beginning
st.set_page_config(
    page_title="Resume Analyzer",
    page_icon="🚀",
    layout="wide"
)


class ResumeApp:
    def __init__(self):

        # Initialize navigation state
        if 'page' not in st.session_state:
            st.session_state.page = 'home'

        self.pages = {
            "🏠 HOME": self.render_home,
            "🔍 RESUME ANALYZER": self.render_analyzer,
            
        }

        # Initialize dashboard manager
        self.dashboard_manager = DashboardManager()

        self.analyzer = ResumeAnalyzer()
        self.job_roles = JOB_ROLES

        # Initialize session state
        if 'user_id' not in st.session_state:
            st.session_state.user_id = 'default_user'
        if 'selected_role' not in st.session_state:
            st.session_state.selected_role = None

        # Initialize database
        init_database()

        # Load external CSS
        with open('style/style.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

        # Load Google Fonts
        st.markdown("""
            <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Poppins:wght@400;500;600&display=swap" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
        """, unsafe_allow_html=True)

        if 'resume_data' not in st.session_state:
            st.session_state.resume_data = []

    def load_lottie_url(self, url: str):
        """Load Lottie animation from URL"""
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()

    def apply_global_styles(self):
        st.markdown("""
        <style>
        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: #1a1a1a;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb {
            background: #4CAF50;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #45a049;
        }

        /* Global Styles */
        .main-header {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
            text-align: center;
            position: relative;
            overflow: hidden;
        }

        .main-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(45deg, transparent 0%, rgba(255,255,255,0.1) 100%);
            z-index: 1;
        }

        .main-header h1 {
            color: white;
            font-size: 2.5rem;
            font-weight: 600;
            margin: 0;
            position: relative;
            z-index: 2;
        }

        /* Template Card Styles */
        .template-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 2rem;
            padding: 1rem;
        }

        .template-card {
            background: rgba(45, 45, 45, 0.9);
            border-radius: 20px;
            padding: 2rem;
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .template-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            border-color: #4CAF50;
        }

        .template-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(45deg, transparent 0%, rgba(76,175,80,0.1) 100%);
            z-index: 1;
        }

        .template-icon {
            font-size: 3rem;
            color: #4CAF50;
            margin-bottom: 1.5rem;
            position: relative;
            z-index: 2;
        }

        .template-title {
            font-size: 1.8rem;
            font-weight: 600;
            color: white;
            margin-bottom: 1rem;
            position: relative;
            z-index: 2;
        }

        .template-description {
            color: #aaa;
            margin-bottom: 1.5rem;
            position: relative;
            z-index: 2;
            line-height: 1.6;
        }

        /* Feature List Styles */
        .feature-list {
            list-style: none;
            padding: 0;
            margin: 1.5rem 0;
            position: relative;
            z-index: 2;
        }

        .feature-item {
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
            color: #ddd;
            font-size: 0.95rem;
        }

        .feature-icon {
            color: #4CAF50;
            margin-right: 0.8rem;
            font-size: 1.1rem;
        }

        /* Button Styles */
        .action-button {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: white;
            padding: 1rem 2rem;
            border-radius: 50px;
            border: none;
            font-weight: 500;
            cursor: pointer;
            width: 100%;
            text-align: center;
            position: relative;
            overflow: hidden;
            z-index: 2;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .action-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(76,175,80,0.3);
        }

        .action-button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.2) 50%, transparent 100%);
            transition: all 0.6s ease;
        }

        .action-button:hover::before {
            left: 100%;
        }

        /* Form Section Styles */
        .form-section {
            background: rgba(45, 45, 45, 0.9);
            border-radius: 20px;
            padding: 2rem;
            margin: 2rem 0;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }

        .form-section-title {
            font-size: 1.8rem;
            font-weight: 600;
            color: white;
            margin-bottom: 1.5rem;
            padding-bottom: 0.8rem;
            border-bottom: 2px solid #4CAF50;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        .form-label {
            color: #ddd;
            font-weight: 500;
            margin-bottom: 0.8rem;
            display: block;
        }

        .form-input {
            width: 100%;
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(30, 30, 30, 0.9);
            color: white;
            transition: all 0.3s ease;
        }

        .form-input:focus {
            border-color: #4CAF50;
            box-shadow: 0 0 0 2px rgba(76,175,80,0.2);
            outline: none;
        }

        /* Skill Tags */
        .skill-tag-container {
            display: flex;
            flex-wrap: wrap;
            gap: 0.8rem;
            margin-top: 1rem;
        }

        .skill-tag {
            background: rgba(76,175,80,0.1);
            color: #4CAF50;
            padding: 0.6rem 1.2rem;
            border-radius: 50px;
            border: 1px solid #4CAF50;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .skill-tag:hover {
            background: #4CAF50;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(76,175,80,0.2);
        }

        /* Progress Circle */
        .progress-container {
            position: relative;
            width: 150px;
            height: 150px;
            margin: 2rem auto;
        }

        .progress-circle {
            transform: rotate(-90deg);
            width: 100%;
            height: 100%;
        }

        .progress-circle circle {
            fill: none;
            stroke-width: 8;
            stroke-linecap: round;
            stroke: #4CAF50;
            transform-origin: 50% 50%;
            transition: all 0.3s ease;
        }

        .progress-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 1.5rem;
            font-weight: 600;
            color: white;
        }
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .feature-card {
            background-color: #1e1e1e;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        /* Animations */
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .animate-slide-in {
            animation: slideIn 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .template-container {
                grid-template-columns: 1fr;
            }

            .main-header {
                padding: 1.5rem;
            }

            .main-header h1 {
                font-size: 2rem;
            }

            .template-card {
                padding: 1.5rem;
            }

            .action-button {
                padding: 0.8rem 1.6rem;
            }
        }
        </style>
        """, unsafe_allow_html=True)
        


    def load_image(self, image_name):
        """Load image from static directory"""
        try:
            image_path = f"c:/Users/shree/Downloads/smart-resume-ai/{image_name}"
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            encoded = base64.b64encode(image_bytes).decode()
            return f"data:image/png;base64,{encoded}"
        except Exception as e:
            print(f"Error loading image {image_name}: {e}")
            return None
        
    def is_probably_resume(self, text: str) -> bool:
        """
        Heuristic-based check to determine if the document is likely a resume.
        """
        text = text.lower()

        required_sections = [
            "education",
            "experience",
            "skills",
            "projects",
            "profile",
            "certifications",
            "achievements",
            "summary",
            "contact",
            "objective"
     ]

        found_sections = sum(1 for section in required_sections if section in text)

    # Consider it a resume if it has at least 3 key sections and a minimum length
        return found_sections >= 5 and len(text.split()) > 100



    def export_to_excel(self):
        """Export resume data to Excel"""
        conn = get_database_connection()

        # Get resume data with analysis
        query = """
            SELECT
                rd.name, rd.email, rd.phone, rd.linkedin, rd.github, rd.portfolio,
                rd.summary, rd.target_role, rd.target_category,
                rd.education, rd.experience, rd.projects, rd.skills,
                ra.ats_score, ra.keyword_match_score, ra.format_score, ra.section_score,
                ra.missing_skills, ra.recommendations,
                rd.created_at
            FROM resume_data rd
            LEFT JOIN resume_analysis ra ON rd.id = ra.resume_id
        """

        try:
            # Read data into DataFrame
            df = pd.read_sql_query(query, conn)

            # Create Excel writer object
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Resume Data')

            return output.getvalue()
        except Exception as e:
            print(f"Error exporting to Excel: {str(e)}")
            return None
        finally:
            conn.close()


    def render_empty_state(self, icon, message):
        """Render an empty state with icon and message"""
        return f"""
            <div style='text-align: center; padding: 2rem; color: #666;'>
                <i class='{icon}' style='font-size: 2rem; margin-bottom: 1rem; color: #00bfa5;'></i>
                <p style='margin: 0;'>{message}</p>
            </div>
        """

    def analyze_resume(self, resume_text):
        """Analyze resume and store results"""
        analytics = self.analyzer.analyze_resume(resume_text)
        st.session_state.analytics_data = analytics
        return analytics

    def handle_resume_upload(self):
        """Handle resume upload and analysis"""
        uploaded_file = st.file_uploader(
            "Upload your resume", type=['pdf', 'docx'])

        if uploaded_file is not None:
            try:
                # Extract text from resume
                if uploaded_file.type == "application/pdf":
                    resume_text = self.analyzer.extract_text_from_pdf(uploaded_file)
                else:
                    resume_text = self.analyzer.extract_text_from_docx(uploaded_file)

                # Store resume data
                st.session_state.resume_data = {
                    'filename': uploaded_file.name,
                    'content': resume_text,
                    'upload_time': datetime.now().isoformat()
                }

                # Analyze resume
                analytics = self.analyze_resume(resume_text)

                return True
            except Exception as e:
                st.error(f"Error processing resume: {str(e)}")
                return False
        return False

    def render_analyzer(self):
        """Render the resume analyzer page"""
        apply_modern_styles()

        # Page Header
        page_header(
            "Resume Analyzer",
            "Optimize your resume with expert feedback to meet job expectations and improve visibility."
        )

        # Create tabs for Resume Analyzer
        analyzer_tabs = st.tabs(["Resume Analyzer"])

        with analyzer_tabs[0]:
            # Job Role Selection
            categories = list(self.job_roles.keys())
            selected_category = st.selectbox(
    "Job Category", categories, key="standard_category")

            roles = list(self.job_roles[selected_category].keys())
            selected_role = st.selectbox(
    "Specific Role", roles, key="standard_role")

            role_info = self.job_roles[selected_category][selected_role]

            # Display role information
            st.markdown(f"""
            <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; margin: 10px 0;'>
                <h3>{selected_role}</h3>
                <p>{role_info['description']}</p>
                <h4>Required Skills:</h4>
                <p>{', '.join(role_info['required_skills'])}</p>
            </div>
            """, unsafe_allow_html=True)

            # File Upload
            uploaded_file = st.file_uploader(
    "Upload your resume", type=[
        'pdf', 'docx'], key="standard_file")

            if not uploaded_file:
                # Display empty state with a prominent upload button
                st.markdown(
                    self.render_empty_state(
                    "fas fa-cloud-upload-alt",
                    "Upload your resume to get started with standard analysis"
                    ),
                    unsafe_allow_html=True
                )
                # Add a prominent upload button
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.markdown("""
                    <style>
                    .upload-button {
                        background: linear-gradient(90deg, #4b6cb7, #182848);
                        color: white;
                        border: none;
                        border-radius: 10px;
                        padding: 15px 25px;
                        font-size: 18px;
                        font-weight: bold;
                        cursor: pointer;
                        width: 100%;
                        text-align: center;
                        margin: 20px 0;
                        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
                        transition: all 0.3s ease;
                    }
                    .upload-button:hover {
                        transform: translateY(-3px);
                        box-shadow: 0 6px 15px rgba(0,0,0,0.3);
                    }

                    """, unsafe_allow_html=True)

            if uploaded_file:
                # Add a prominent analyze button
                analyze_standard = st.button("🔍 Analyze My Resume",
                                    type="primary",
                                    use_container_width=True,
                                    key="analyze_standard_button")

                if analyze_standard:
                    with st.spinner("Analyzing your document..."):
                        # Get file content
                        text = ""
                        try:
                            if uploaded_file.type == "application/pdf":
                                try:
                                    text = self.analyzer.extract_text_from_pdf(uploaded_file)
                                except Exception as pdf_error:
                                    st.error(f"PDF extraction failed: {str(pdf_error)}")
                                    st.info("Trying alternative PDF extraction method...")
                                   
                                    
                            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                                try:
                                    text = self.analyzer.extract_text_from_docx(uploaded_file)
                                except Exception as docx_error:
                                    st.error(f"DOCX extraction failed: {str(docx_error)}")
                                    
                            else:
                                text = uploaded_file.getvalue().decode()
                                
                            if not text or text.strip() == "":
                                st.error("Could not extract any text from the uploaded file.")
                                return

                            # Strict check to reject seminar reports or non-resume documents
                            if not self.is_probably_resume(text):
                                st.error("❌ This document doesn't appear to be a resume.")
                                st.warning("Please upload a resume that contains standard sections like Education, Skills, Experience, or Projects.")
                                return


                        except Exception as e:
                            st.error(f"Error reading file: {str(e)}")
                            return

                        # Analyze the document
                        analysis = self.analyzer.analyze_resume({'raw_text': text}, role_info)

                        # Check if analysis returned an error
                        if 'error' in analysis:
                            st.error(analysis['error'])
                            return

                        # 🚫 Reject non-resume documents
                        if analysis.get('document_type') != 'resume':
                            st.error(f"⚠️ This appears to be a {analysis['document_type']} document, not a resume!")
                            st.warning("Please upload a proper resume for ATS analysis.")
                            return

                        
                        # Check if analysis returned an error
                        if 'error' in analysis:
                            st.error(analysis['error'])
                            return

                        # Show snowflake effect
                        st.snow()

                        # Save resume data to database
                        resume_data = {}

                        # Save to database
                        try:
                            resume_id = save_resume_data(resume_data)

                            # Save analysis data
                            analysis_data = {
                                'resume_id': resume_id,
                                'ats_score': analysis['ats_score'],
                                'keyword_match_score': analysis['keyword_match']['score'],
                                'format_score': analysis['format_score'],
                                'section_score': analysis['section_score'],
                                'missing_skills': ','.join(analysis['keyword_match']['missing_skills']),
                                'recommendations': ','.join(analysis['suggestions'])
                            }
                            save_analysis_data(resume_id, analysis_data)
                            st.success("Resume data saved successfully!")
                        except Exception as e:
                            st.error(f"Error saving to database: {str(e)}")
                            print(f"Database error: {e}")

                        # Show results based on document type
                        if analysis.get('document_type') != 'resume':
                            st.error(
    f"⚠️ This appears to be a {
        analysis['document_type']} document, not a resume!")
                            st.warning(
                                "Please upload a proper resume for ATS analysis.")
                            return
                        # Display results in a modern card layout
                    col1, col2 = st.columns(2)

                    with col1:
                        # ATS Score Card with circular progress
                        st.markdown("""
                        <div class="feature-card">
                            <h2>ATS Score</h2>
                            <div style="position: relative; width: 150px; height: 150px; margin: 0 auto;">
                                <div style="
                                    position: absolute;
                                    width: 150px;
                                    height: 150px;
                                    border-radius: 50%;
                                    background: conic-gradient(
                                        #4CAF50 0% {score}%,
                                        #2c2c2c {score}% 100%
                                    );
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                ">
                                    <div style="
                                        width: 120px;
                                        height: 120px;
                                        background: #1a1a1a;
                                        border-radius: 50%;
                                        display: flex;
                                        align-items: center;
                                        justify-content: center;
                                        font-size: 24px;
                                        font-weight: bold;
                                        color: {color};
                                    ">
                                        {score}
                                    </div>
                                </div>
                            </div>
                            <div style="text-align: center; margin-top: 10px;">
                                <span style="
                                    font-size: 1.2em;
                                    color: {color};
                                    font-weight: bold;
                                ">
                                    {status}
                                </span>
                            </div>
                        """.format(
                            score=analysis['ats_score'],
                            color='#4CAF50' if analysis['ats_score'] >= 80 else '#FFA500' if analysis[
                                'ats_score'] >= 60 else '#FF4444',
                            status='Excellent' if analysis['ats_score'] >= 80 else 'Good' if analysis[
                                'ats_score'] >= 60 else 'Needs Improvement'
                        ), unsafe_allow_html=True)

                        st.markdown("</div>", unsafe_allow_html=True)

                        # self.display_analysis_results(analysis_results)

                        # Skills Match Card
                        st.markdown("""
                        <div class="feature-card">
                            <h2>Skills Match</h2>
                        """, unsafe_allow_html=True)

                        st.metric(
                            "Keyword Match", f"{int(analysis.get('keyword_match', {}).get('score', 0))}%")

                        if analysis['keyword_match']['missing_skills']:
                            st.markdown("#### Missing Skills:")
                            for skill in analysis['keyword_match']['missing_skills']:
                                st.markdown(f"- {skill}")

                        st.markdown("</div>", unsafe_allow_html=True)

                    with col2:
                        # Format Score Card
                        st.markdown("""
                        <div class="feature-card">
                            <h2>Format Analysis</h2>
                        """, unsafe_allow_html=True)

                        st.metric("Format Score",
                                  f"{int(analysis.get('format_score', 0))}%")
                        st.metric("Section Score",
                                  f"{int(analysis.get('section_score', 0))}%")

                        st.markdown("</div>", unsafe_allow_html=True)

                        # Suggestions Card with improved UI
                        st.markdown("""
                        <div class="feature-card">
                            <h2>📋 Resume Improvement Suggestions</h2>
                        """, unsafe_allow_html=True)

                            # Contact Section
                        if analysis.get('contact_suggestions'):
                                st.markdown("""
                                <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                                    <h3 style='color: #4CAF50; margin-bottom: 10px;'>📞 Contact Information</h3>
                                    <ul style='list-style-type: none; padding-left: 0;'>
                                """, unsafe_allow_html=True)
                                for suggestion in analysis.get(
                                    'contact_suggestions', []):
                                    st.markdown(
    f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>",
     unsafe_allow_html=True)
                                st.markdown(
    "</ul></div>", unsafe_allow_html=True)

                            # Summary Section
                        if analysis.get('summary_suggestions'):
                                st.markdown("""
                                <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                                    <h3 style='color: #4CAF50; margin-bottom: 10px;'>📝 Professional Summary</h3>
                                    <ul style='list-style-type: none; padding-left: 0;'>
                                """, unsafe_allow_html=True)
                                for suggestion in analysis.get(
                                    'summary_suggestions', []):
                                    st.markdown(
    f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>",
     unsafe_allow_html=True)
                                st.markdown(
    "</ul></div>", unsafe_allow_html=True)

                            # Skills Section
                        if analysis.get(
                            'skills_suggestions') or analysis['keyword_match']['missing_skills']:
                                st.markdown("""
                                <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                                    <h3 style='color: #4CAF50; margin-bottom: 10px;'>🎯 Skills</h3>
                                    <ul style='list-style-type: none; padding-left: 0;'>
                                """, unsafe_allow_html=True)
                                for suggestion in analysis.get(
                                    'skills_suggestions', []):
                                    st.markdown(
    f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>",
     unsafe_allow_html=True)
                                if analysis['keyword_match']['missing_skills']:
                                    st.markdown(
    "<li style='margin-bottom: 8px;'>✓ Consider adding these relevant skills:</li>",
     unsafe_allow_html=True)
                                    for skill in analysis['keyword_match']['missing_skills']:
                                        st.markdown(
    f"<li style='margin-left: 20px; margin-bottom: 4px;'>• {skill}</li>",
     unsafe_allow_html=True)
                                st.markdown(
    "</ul></div>", unsafe_allow_html=True)

                            # Experience Section
                        if analysis.get('experience_suggestions'):
                                st.markdown("""
                                <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                                    <h3 style='color: #4CAF50; margin-bottom: 10px;'>💼 Work Experience</h3>
                                    <ul style='list-style-type: none; padding-left: 0;'>
                                """, unsafe_allow_html=True)
                                for suggestion in analysis.get(
                                    'experience_suggestions', []):
                                    st.markdown(
    f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>",
     unsafe_allow_html=True)
                                st.markdown(
    "</ul></div>", unsafe_allow_html=True)


                            # General Formatting Suggestions
                        if analysis.get('format_suggestions'):
                                st.markdown("""
                                <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                                    <h3 style='color: #4CAF50; margin-bottom: 10px;'>📄 Formatting</h3>
                                    <ul style='list-style-type: none; padding-left: 0;'>
                                """, unsafe_allow_html=True)
                                for suggestion in analysis.get(
                                    'format_suggestions', []):
                                    st.markdown(
    f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>",
     unsafe_allow_html=True)
                                st.markdown(
    "</ul></div>", unsafe_allow_html=True)

                        st.markdown("</div>", unsafe_allow_html=True)


    def render_home(self):
        apply_modern_styles()
        
        # Hero Section
        hero_section(
            "Resume Analyzer",
            "Analyze your resume and match it with job-ready skills using intelligent insights."
        )
        
        # Features Section
        st.markdown('<div class="feature-grid">', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        

        # Call-to-Action with Streamlit navigation
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Get Started", key="get_started_btn", 
                        help="Click to start analyzing your resume",
                        type="primary",
                        use_container_width=True):
                cleaned_name = "🔍 RESUME ANALYZER".lower().replace(" ", "_").replace("🔍", "").strip()
                st.session_state.page = cleaned_name
                st.rerun()


    def main(self):
        """Main application entry point"""
        self.apply_global_styles()
        
       
        with st.sidebar:
            st_lottie(self.load_lottie_url("https://assets5.lottiefiles.com/packages/lf20_xyadoh9h.json"), height=200, key="sidebar_animation")
            st.title("Resume Analyzer")
            st.markdown("---")
            
            # Navigation buttons
            for page_name in self.pages.keys():
                if st.button(page_name, use_container_width=True):
                    cleaned_name = page_name.lower().replace(" ", "_").replace("🏠", "").replace("🔍", "").strip()
                    st.session_state.page = cleaned_name
                    st.rerun()


        # Force home page on first load
        if 'initial_load' not in st.session_state:
            st.session_state.initial_load = True
            st.session_state.page = 'home'
            st.rerun()
        
        # Get current page and render it
        current_page = st.session_state.get('page', 'home')
        
        # Create a mapping of cleaned page names to original names
        page_mapping = {name.lower().replace(" ", "_").replace("🏠", "").replace("🔍", "").strip(): name 
                       for name in self.pages.keys()}
        
        # Render the appropriate page
        if current_page in page_mapping:
            self.pages[page_mapping[current_page]]()
        else:
            # Default to home page if invalid page
            self.render_home()


if __name__ == "__main__":
    app = ResumeApp()
    app.main()