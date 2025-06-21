import pypdf
import docx
import re
from io import BytesIO

class ResumeParser:
    def __init__(self):
        # Define commonly searched skill keywords
        self.skill_keywords = [
            'python', 'java', 'javascript', 'html', 'css', 'sql', 'react', 'angular', 'vue',
            'node', 'express', 'django', 'flask', 'spring', 'docker', 'kubernetes', 'aws',
            'azure', 'git', 'jenkins', 'jira'
        ]

    def extract_text_from_pdf(self, pdf_file):
        try:
            file_content = pdf_file.read() if hasattr(pdf_file, 'read') else pdf_file
            pdf_file.seek(0) if hasattr(pdf_file, 'seek') else None

            reader = pypdf.PdfReader(BytesIO(file_content))
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                text += page_text + "\n" if page_text else "\n"
            return text.strip()
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""

    def extract_text_from_docx(self, docx_file):
        try:
            doc = docx.Document(BytesIO(docx_file.read()))
            text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
            return text.strip()
        except Exception as e:
            print(f"Error extracting text from DOCX: {e}")
            return ""

    def extract_text(self, file):
        try:
            file.seek(0)
            if file.name.lower().endswith('.pdf'):
                return self.extract_text_from_pdf(file)
            elif file.name.lower().endswith('.docx'):
                return self.extract_text_from_docx(file)
            else:
                print("Unsupported file format")
                return ""
        except Exception as e:
            print(f"Error reading file: {e}")
            return ""

    def parse(self, file):
        text = self.extract_text(file)
        text_lower = text.lower()

        # Extract skills
        skills = [skill for skill in self.skill_keywords if skill in text_lower]

        # Placeholder lists (can be filled later with NLP)
        experience = []
        education = []

        return {
            "skills": skills,
            "experience": experience,
            "education": education,
            "raw_text": text
        }
