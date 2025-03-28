import os
import django

# Setup Django environment when running directly
if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'majorproject.settings')  # Update with your project name
    django.setup()

# Now import Django models
import google.generativeai as genai
from authentication.models import Student
from attendance.models import Attendance
from leave.models import StudentLeave
from remarks.models import CounselorRemark
from reports.models import StudentWork
from django.db.models import Avg
import json
from datetime import datetime, timedelta
import markdown
import bleach


def configure_genai():
    """Configure the Gemini API with your API key"""
    genai.configure(api_key='AIzaSyDoByBtUxwgu5t_X13HE4RqGA4_YrOYoBQ')
    # genai.configure(api_key=settings.GEMINI_API_KEY)


def get_student_data(counselor):
    """
    Fetch and structure student data for the given counselor
    Returns a formatted string with all relevant student information
    """
    # Get all students assigned to this counselor
    students = Student.objects.filter(counselor=counselor).select_related('user')

    student_data = []

    for student in students:
        # Get display values for choice fields
        branch_display = dict(student.BRANCH_CHOICES).get(student.branch, '')
        year_display = dict(student.YEAR_CHOICES).get(student.year, '')
        semester_display = dict(student.SEMESTER_CHOICES).get(student.semester, '')
        gender_display = dict(student.GENDER_CHOICES).get(student.gender, '')

        # Basic student info
        student_info = {
            "roll_number": student.roll_number,
            "name": student.user.username,
            "branch": branch_display,
            "year": year_display,
            "semester": semester_display,
            "section": student.section,
            "gender": gender_display,
            "attendance_percentage": student.attendance_percentage,
        }

        # Recent attendance records (last 10)
        attendance_records = Attendance.objects.filter(student=student).order_by('-date')[:10]
        student_info["recent_attendance"] = [{
            "date": str(record.date),
            "status": record.status
        } for record in attendance_records]

        # Leave applications (last 5)
        leave_applications = StudentLeave.objects.filter(student=student).order_by('-created_at')[:5]
        student_info["leave_applications"] = [{
            "date": str(leave.date),
            "reason": leave.reason,
            "no_of_days": leave.no_of_days,
            "status": leave.status,
            "created_at": str(leave.created_at.date())
        } for leave in leave_applications]

        # Recent remarks (last 5)
        remarks = CounselorRemark.objects.filter(student=student).order_by('-date')[:5]
        student_info["remarks"] = [{
            "date": str(remark.date),
            "content": remark.remarks,
            "sentiment": remark.sentiment,
        } for remark in remarks]

        # Recent weekly reports (last 3)
        reports = StudentWork.objects.filter(student=student).order_by('-date')[:3]
        student_info["weekly_reports"] = [{
            "date": str(report.date),
            "work_done": report.work_done
        } for report in reports]

        student_data.append(student_info)

    # Get overall statistics
    today = datetime.now().date()
    last_week = today - timedelta(days=7)

    # Attendance statistics
    avg_attendance = students.aggregate(Avg('attendance_percentage'))['attendance_percentage__avg']
    attendance_below_75 = students.filter(attendance_percentage__lt=75).count()

    # Recent leave stats
    pending_leaves = StudentLeave.objects.filter(
        student__in=students,
        status='Pending'
    ).count()

    # Recent remarks with sentiment analysis
    positive_remarks = CounselorRemark.objects.filter(
        student__in=students,
        sentiment='POSITIVE',
        date__gte=last_week
    ).count()

    negative_remarks = CounselorRemark.objects.filter(
        student__in=students,
        sentiment='NEGATIVE',
        date__gte=last_week
    ).count()

    stats = {
        "total_students": students.count(),
        "average_attendance": avg_attendance if avg_attendance else 0,
        "students_below_75_attendance": attendance_below_75,
        "pending_leave_applications": pending_leaves,
        "recent_positive_remarks": positive_remarks,
        "recent_negative_remarks": negative_remarks,
        "students_data": student_data
    }

    return json.dumps(stats, indent=2)


def markdown_to_html(text):
    """
    Convert markdown text to safe HTML

    Args:
        text: The markdown text to convert

    Returns:
        Safe HTML string
    """
    # Convert markdown to HTML using Python's markdown package
    html = markdown.markdown(
        text,
        extensions=[
            'markdown.extensions.tables',
            'markdown.extensions.fenced_code',
            'markdown.extensions.codehilite',
            'markdown.extensions.nl2br',  # Convert newlines to <br>
        ]
    )

    # List of allowed HTML tags and attributes for security
    allowed_tags = [
        'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'br',
        'ul', 'ol', 'li', 'strong', 'em', 'code', 'pre',
        'table', 'thead', 'tbody', 'tr', 'th', 'td',
        'blockquote', 'span', 'div', 'a'
    ]

    allowed_attrs = {
        '*': ['class'],
        'a': ['href', 'title', 'target'],
        'th': ['scope', 'colspan', 'rowspan'],
        'td': ['colspan', 'rowspan']
    }

    # Sanitize HTML to prevent XSS
    clean_html = bleach.clean(
        html,
        tags=allowed_tags,
        attributes=allowed_attrs,
        strip=True
    )

    return clean_html


def chat(message, counselor):
    """
    Process a chat message using the Gemini API

    Args:
        message: The question from the counselor
        counselor: The Counselor object for the current user

    Returns:
        The formatted HTML response from Gemini
    """
    try:
        configure_genai()
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Get structured student data
        student_data = get_student_data(counselor)

        # Create the prompt for Gemini
        prompt = f"""
        You are InfoMate, an intelligent assistant for college counselors. Your job is to help counselors understand 
        and analyze student data. Use the following student data to answer the counselor's question accurately.
        The data is organized by student, with details about their attendance, leave applications, remarks, and weekly reports.

        STUDENT DATA:
        {student_data}

        When answering, make sure to:
        1. Be concise and direct
        2. Provide specific details from the data when relevant
        3. Highlight patterns or concerns (low attendance, frequently absent students, etc.)
        4. Format numerical data clearly
        5. For attendance, emphasize if any student is below 75% (the minimum requirement)
        6. If asked about a specific student, provide all relevant information about that student
        7. Use Markdown formatting for your response with:
           - Headers (## and ###) for sections
           - Bold text for important information
           - Lists for multiple items
           - Tables when comparing data
           - Code blocks for any structured data
        8. Format student roll numbers, percentage values, and important status information as **bold**

        Counselor Question: {message}

        Your response:
        """

        # Generate the response
        response = model.generate_content(prompt)
        markdown_response = response.text.strip()

        # Convert markdown to HTML
        html_response = markdown_to_html(markdown_response)

        return html_response

    except Exception as e:
        print(f"Error in chat: {e}")
        error_message = f"I'm sorry, but I encountered an error while processing your question: {str(e)}"
        return markdown_to_html(error_message)


# For testing purposes when running the script directly
if __name__ == "__main__":
    # Import Counselor at runtime to avoid circular imports
    from authentication.models import Counselor

    # Get the first counselor for testing or by a specific username
    try:
        test_counselor = Counselor.objects.first()
        if test_counselor:
            response = chat("List students with attendance below 75%", test_counselor)
            print(response)
        else:
            print("No counselors found in the database")
    except Exception as e:
        print(f"Error during testing: {e}")