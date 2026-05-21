from decimal import Decimal
from .models import UserMark, Grade


class GPACalculator:
    
    @staticmethod
    def calculate_semester_gpa(user, academic_year, semester):
        """
        Calculate GPA for a specific semester.
        GPA = Sum(Credit Hours x Grade Points) / Sum(Credit Hours)
        Only passed courses (50% or above) are included.
        """
        # Get all marks for this semester
        marks = UserMark.objects.filter(
            user=user,
            academic_year=academic_year,
            semester=semester,
            exclude_from_cgpa=False
        ).select_related('course')
        
        # Group by course and calculate average percentage for each course in this semester
        course_averages = {}
        for mark in marks:
            course_id = mark.course.id
            if course_id not in course_averages:
                course_averages[course_id] = {
                    'course': mark.course,
                    'totals': [],
                    'credits': mark.course.credits
                }
            course_averages[course_id]['totals'].append(float(mark.total_mark))
        
        total_grade_points = Decimal('0.00')
        total_credits = 0
        
        for course_id, data in course_averages.items():
            # Calculate average percentage for this course in this semester
            avg_percentage = sum(data['totals']) / len(data['totals'])
            
            # Determine grade point based on average percentage
            # 50% (Grade C) is minimum pass for ALL courses
            if avg_percentage >= 80:
                grade_point = 4.00
                is_passed = True
            elif avg_percentage >= 70:
                grade_point = 3.50
                is_passed = True
            elif avg_percentage >= 60:
                grade_point = 3.00
                is_passed = True
            elif avg_percentage >= 55:
                grade_point = 2.50
                is_passed = True
            elif avg_percentage >= 50:
                grade_point = 2.00
                is_passed = True
            elif avg_percentage >= 45:
                grade_point = 1.50
                is_passed = False
            elif avg_percentage >= 40:
                grade_point = 1.00
                is_passed = False
            else:
                grade_point = 0.00
                is_passed = False
            
            if is_passed:
                total_grade_points += Decimal(str(grade_point)) * data['credits']
                total_credits += data['credits']
        
        if total_credits == 0:
            return Decimal('0.00')
        
        semester_gpa = total_grade_points / total_credits
        return round(semester_gpa, 2)
    
    @staticmethod
    def calculate_cumulative_gpa(user):
        """
        Calculate CGPA as the AVERAGE of all semester GPAs.
        CGPA = (Sum of Semester GPAs) / (Number of Semesters)
        """
        # Get all distinct semesters for this user
        semesters = UserMark.objects.filter(
            user=user,
            exclude_from_cgpa=False
        ).values('academic_year', 'semester').distinct().order_by('academic_year', 'semester')
        
        if not semesters:
            return Decimal('0.00')
        
        semester_gpas = []
        for semester_data in semesters:
            gpa = GPACalculator.calculate_semester_gpa(
                user,
                semester_data['academic_year'],
                semester_data['semester']
            )
            semester_gpas.append(gpa)
        
        if not semester_gpas:
            return Decimal('0.00')
        
        # CGPA is the average of all semester GPAs
        cgpa = sum(semester_gpas) / len(semester_gpas)
        return round(cgpa, 2)
    
    @staticmethod
    def get_semester_gpas(user):
        """
        Get a list of all semester GPAs with their details.
        Returns a list of dictionaries with academic_year, semester, and gpa.
        """
        semesters = UserMark.objects.filter(
            user=user,
            exclude_from_cgpa=False
        ).values('academic_year', 'semester').distinct().order_by('academic_year', 'semester')
        
        semester_gpas = []
        for semester_data in semesters:
            gpa = GPACalculator.calculate_semester_gpa(
                user,
                semester_data['academic_year'],
                semester_data['semester']
            )
            semester_gpas.append({
                'academic_year': semester_data['academic_year'],
                'semester': semester_data['semester'],
                'gpa': gpa
            })
        
        return semester_gpas
    
    @staticmethod
    def get_degree_classification(cgpa):
        """Determine degree classification based on CGPA"""
        if cgpa >= 3.60:
            return "First Class Honours"
        elif cgpa >= 3.00:
            return "Second Class Honours (Upper Division)"
        elif cgpa >= 2.50:
            return "Second Class Honours (Lower Division)"
        elif cgpa >= 2.00:
            return "Pass"
        else:
            return "Not Eligible for Degree"


class ProgressTracker:
    
    @staticmethod
    def get_completed_credits(user):
        """
        Calculate total credits from passed courses.
        A course is considered passed if the average of all attempts is 50% or higher.
        """
        # Get all marks for the user
        all_marks = UserMark.objects.filter(
            user=user,
            exclude_from_cgpa=False
        ).select_related('course')
        
        # Group by course and calculate average percentage for each course
        course_averages = {}
        for mark in all_marks:
            course_id = mark.course.id
            if course_id not in course_averages:
                course_averages[course_id] = {
                    'course': mark.course,
                    'totals': [],
                    'credits': mark.course.credits
                }
            course_averages[course_id]['totals'].append(float(mark.total_mark))
        
        total_credits = 0
        for course_id, data in course_averages.items():
            avg_percentage = sum(data['totals']) / len(data['totals'])
            # 50% is minimum pass for ALL courses
            if avg_percentage >= 50:
                total_credits += data['credits']
        
        return total_credits
    
    @staticmethod
    def get_remaining_credits(user):
        """Calculate remaining credits needed for graduation"""
        if not user.programme:
            return 0
        completed = ProgressTracker.get_completed_credits(user)
        required = user.programme.total_credits_required
        remaining = required - completed
        return remaining if remaining > 0 else 0
    
    @staticmethod
    def get_progress_percentage(user):
        """Calculate graduation progress percentage"""
        if not user.programme:
            return 0
        completed = ProgressTracker.get_completed_credits(user)
        required = user.programme.total_credits_required
        if required == 0:
            return 0
        percentage = (completed / required) * 100
        return min(percentage, 100)
    
    @staticmethod
    def get_remaining_courses(user):
        """Get courses not yet passed based on AVERAGE of all attempts"""
        if not user.programme:
            return []
        
        from curriculum.models import CourseProgramme
        all_courses = CourseProgramme.objects.filter(programme=user.programme)
        
        # Get all marks for the user
        all_marks = UserMark.objects.filter(
            user=user,
            exclude_from_cgpa=False
        ).select_related('course')
        
        # Group by course and calculate average percentage
        passed_course_ids = []
        course_averages = {}
        for mark in all_marks:
            course_id = mark.course.id
            if course_id not in course_averages:
                course_averages[course_id] = {
                    'course': mark.course,
                    'totals': []
                }
            course_averages[course_id]['totals'].append(float(mark.total_mark))
        
        for course_id, data in course_averages.items():
            avg_percentage = sum(data['totals']) / len(data['totals'])
            if avg_percentage >= 50:  # Pass threshold for ALL courses
                passed_course_ids.append(course_id)
        
        return all_courses.exclude(course_id__in=passed_course_ids)