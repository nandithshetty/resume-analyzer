import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from config.database import get_database_connection
import plotly.express as px

class DashboardManager:
    def __init__(self):
        self.conn = get_database_connection()
        self.colors = {
            'primary': '#4CAF50',
            'secondary': '#2196F3',
            'warning': '#FFA726',
            'danger': '#F44336',
            'info': '#00BCD4',
            'success': '#66BB6A',
            'purple': '#9C27B0',
            'background': '#1E1E1E',
            'card': '#2D2D2D',
            'text': '#FFFFFF',
            'subtext': '#B0B0B0'
        }

    def get_resume_metrics(self):
        cursor = self.conn.cursor()
        now = datetime.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week = now - timedelta(days=now.weekday())
        start_of_month = now.replace(day=1)
        metrics = {}
        for period, start_date in [
            ('Today', start_of_day),
            ('This Week', start_of_week),
            ('This Month', start_of_month),
            ('All Time', datetime(2000, 1, 1))
        ]:
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT rd.id) as total_resumes,
                    ROUND(AVG(ra.ats_score), 1) as avg_ats_score,
                    ROUND(AVG(ra.keyword_match_score), 1) as avg_keyword_score,
                    COUNT(DISTINCT CASE WHEN ra.ats_score >= 70 THEN rd.id END) as high_scoring
                FROM resume_data rd
                LEFT JOIN resume_analysis ra ON rd.id = ra.resume_id
                WHERE rd.created_at >= ?
            """, (start_date.strftime('%Y-%m-%d %H:%M:%S'),))
            row = cursor.fetchone()
            metrics[period] = {
                'total': row[0] or 0,
                'ats_score': row[1] or 0,
                'keyword_score': row[2] or 0,
                'high_scoring': row[3] or 0
            }
        return metrics

    def get_skill_distribution(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            WITH RECURSIVE split(skill, rest) AS (
                SELECT '', skills || ',' FROM resume_data
                UNION ALL
                SELECT substr(rest, 0, instr(rest, ',')), substr(rest, instr(rest, ',') + 1)
                FROM split WHERE rest <> ''
            ),
            SkillCategories AS (
                SELECT 
                    CASE 
                        WHEN LOWER(TRIM(skill, '[]" ')) LIKE '%python%' OR LOWER(TRIM(skill, '[]" ')) LIKE '%java%' OR 
                             LOWER(TRIM(skill, '[]" ')) LIKE '%javascript%' OR LOWER(TRIM(skill, '[]" ')) LIKE '%c++%' THEN 'Programming'
                        WHEN LOWER(TRIM(skill, '[]" ')) LIKE '%sql%' OR LOWER(TRIM(skill, '[]" ')) LIKE '%database%' THEN 'Database'
                        WHEN LOWER(TRIM(skill, '[]" ')) LIKE '%aws%' OR LOWER(TRIM(skill, '[]" ')) LIKE '%cloud%' THEN 'Cloud'
                        WHEN LOWER(TRIM(skill, '[]" ')) LIKE '%agile%' OR LOWER(TRIM(skill, '[]" ')) LIKE '%scrum%' THEN 'Management'
                        ELSE 'Other'
                    END as category, COUNT(*) as count
                FROM split
                WHERE skill <> ''
                GROUP BY category
            )
            SELECT category, count FROM SkillCategories ORDER BY count DESC
        """)
        categories, counts = zip(*cursor.fetchall()) if cursor.rowcount else ([], [])
        return categories, counts

    def get_weekly_trends(self):
        cursor = self.conn.cursor()
        now = datetime.now()
        dates = [(now - timedelta(days=x)).strftime('%Y-%m-%d') for x in range(6, -1, -1)]
        submissions = []
        for date in dates:
            cursor.execute("SELECT COUNT(*) FROM resume_data WHERE DATE(created_at) = DATE(?)", (date,))
            submissions.append(cursor.fetchone()[0])
        return [d[-3:] for d in dates], submissions

    def get_job_category_stats(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                COALESCE(target_category, 'Other') as category,
                COUNT(*) as count,
                ROUND(AVG(CASE WHEN ra.ats_score >= 70 THEN 1 ELSE 0 END) * 100, 1) as success_rate
            FROM resume_data rd
            LEFT JOIN resume_analysis ra ON rd.id = ra.resume_id
            GROUP BY category
            ORDER BY count DESC
            LIMIT 5
        """)
        categories, rates = zip(*[(row[0], row[2]) for row in cursor.fetchall()])
        return categories, rates

    def create_submission_trends_chart(self):
        dates, submissions = self.get_weekly_trends()
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=submissions,
            mode='lines+markers',
            line=dict(color=self.colors['info'], width=3),
            marker=dict(size=8, color=self.colors['info'])
        ))
        fig.update_layout(
            title="Weekly Submission Pattern",
            paper_bgcolor=self.colors['card'],
            plot_bgcolor=self.colors['card'],
            font={'color': self.colors['text']},
            height=300,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        fig.update_xaxes(title_text="Day of Week", color=self.colors['text'])
        fig.update_yaxes(title_text="Number of Submissions", color=self.colors['text'])
        return fig

    def create_job_category_chart(self):
        categories, rates = self.get_job_category_stats()
        fig = go.Figure(go.Bar(
            x=categories,
            y=rates,
            marker_color=[self.colors['success'], self.colors['info'], self.colors['warning'], self.colors['purple'], self.colors['secondary']],
            text=[f"{rate}%" for rate in rates],
            textposition='auto',
        ))
        fig.update_layout(
            title="Success Rate by Job Category",
            paper_bgcolor=self.colors['card'],
            plot_bgcolor=self.colors['card'],
            font={'color': self.colors['text']},
            height=300,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        fig.update_xaxes(title_text="Job Category", color=self.colors['text'])
        fig.update_yaxes(title_text="Success Rate (%)", color=self.colors['text'])
        return fig
