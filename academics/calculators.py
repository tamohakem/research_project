from decimal import Decimal
from .models import UserMark, Grade


class GPACalculator:
    
    @staticmethod
    def calculate_semester_gpa(user, academic_year, semester):
        marks = UserMark.objects.filter(
            user=user,
            academic_year=academic_year,
            semester=semester,
            exclude_from_cgpa=False
        ).select_related('course')
        
        course_avg = {}
        for mark in marks:
            cid = mark.course.id
            if cid not in course_avg:
                course_avg[cid] = {
                    'course': mark.course,
                    'totals': [],
                    'credits': mark.course.credits
                }
            course_avg[cid]['totals'].append(float(mark.total_mark))
        
        total_grade_points = Decimal('0.00')
        total_credits = 0
        
        for data in course_avg.values():
            avg_perc = sum(data['totals']) / len(data['totals'])
            if avg_perc >= 80:
                gp = 4.00
                passed = True
            elif avg_perc >= 70:
                gp = 3.50
                passed = True
            elif avg_perc >= 60:
                gp = 3.00
                passed = True
            elif avg_perc >= 55:
                gp = 2.50
                passed = True
            elif avg_perc >= 50:
                gp = 2.00
                passed = True
            elif avg_perc >= 45:
                gp = 1.50
                passed = False
            elif avg_perc >= 40:
                gp = 1.00
                passed = False
            else:
                gp = 0.00
                passed = False
            
            if passed:
                total_grade_points += Decimal(str(gp)) * data['credits']
                total_credits += data['credits']
        
        if total_credits == 0:
            return Decimal('0.00')
        return round(total_grade_points / total_credits, 2)
    
    @staticmethod
    def calculate_cumulative_gpa(user):
        semesters = UserMark.objects.filter(
            user=user,
            exclude_from_cgpa=False
        ).values('academic_year', 'semester').distinct().order_by('academic_year', 'semester')
        if not semesters:
            return Decimal('0.00')
        gpas = [GPACalculator.calculate_semester_gpa(user, s['academic_year'], s['semester']) for s in semesters]
        if not gpas:
            return Decimal('0.00')
        return round(sum(gpas) / len(gpas), 2)
    
    @staticmethod
    def get_semester_gpas(user):
        semesters = UserMark.objects.filter(
            user=user,
            exclude_from_cgpa=False
        ).values('academic_year', 'semester').distinct().order_by('academic_year', 'semester')
        return [{'academic_year': s['academic_year'], 'semester': s['semester'], 'gpa': GPACalculator.calculate_semester_gpa(user, s['academic_year'], s['semester'])} for s in semesters]
    
    @staticmethod
    def get_degree_classification(cgpa):
        if cgpa >= 3.60:
            return "First Class Honours"
        if cgpa >= 3.00:
            return "Second Class Honours (Upper Division)"
        if cgpa >= 2.50:
            return "Second Class Honours (Lower Division)"
        if cgpa >= 2.00:
            return "Pass"
        return "Not Eligible for Degree"


class ProgressTracker:
    
    @staticmethod
    def get_completed_credits(user):
        all_marks = UserMark.objects.filter(user=user, exclude_from_cgpa=False).select_related('course')
        course_data = {}
        for m in all_marks:
            cid = m.course.id
            if cid not in course_data:
                course_data[cid] = {'totals': [], 'credits': m.course.credits}
            course_data[cid]['totals'].append(float(m.total_mark))
        total = 0
        for data in course_data.values():
            if sum(data['totals']) / len(data['totals']) >= 50:
                total += data['credits']
        return total
    
    @staticmethod
    def get_remaining_credits(user):
        if not user.programme:
            return 0
        if user.programme.degree_type in ['BENG', 'TOPUP_BENG']:
            required = 240
        elif user.programme.degree_type in ['MENG', 'MSC_ENG', 'TOPUP_MENG', 'TOPUP_MSC']:
            required = 120
        elif user.programme.degree_type == 'PHD':
            required = 180
        else:
            required = 240
        completed = ProgressTracker.get_completed_credits(user)
        return max(required - completed, 0)
    
    @staticmethod
    def get_progress_percentage(user):
        if not user.programme:
            return 0
        if user.programme.degree_type in ['BENG', 'TOPUP_BENG']:
            required = 240
        elif user.programme.degree_type in ['MENG', 'MSC_ENG', 'TOPUP_MENG', 'TOPUP_MSC']:
            required = 120
        elif user.programme.degree_type == 'PHD':
            required = 180
        else:
            required = 240
        if required == 0:
            return 0
        completed = ProgressTracker.get_completed_credits(user)
        return min((completed / required) * 100, 100)
    
    @staticmethod
    def get_remaining_courses(user):
        if not user.programme:
            from curriculum.models import CourseProgramme
            return CourseProgramme.objects.none()
        from curriculum.models import CourseProgramme
        all_courses = CourseProgramme.objects.filter(programme=user.programme)
        all_marks = UserMark.objects.filter(user=user, exclude_from_cgpa=False).select_related('course')
        passed_ids = []
        course_avg = {}
        for m in all_marks:
            cid = m.course.id
            if cid not in course_avg:
                course_avg[cid] = {'totals': []}
            course_avg[cid]['totals'].append(float(m.total_mark))
        for cid, data in course_avg.items():
            if sum(data['totals']) / len(data['totals']) >= 50:
                passed_ids.append(cid)
        if passed_ids:
            return all_courses.exclude(course_id__in=passed_ids)
        return all_courses