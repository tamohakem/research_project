from django.core.management.base import BaseCommand
from accounts.models import Department, Programme

class Command(BaseCommand):
    help = 'Load FET academic programmes from official 2026 structure'
    
    def handle(self, *args, **options):
        # Create Departments
        departments_data = [
            {'name': 'Chemical and Petroleum Engineering', 'code': 'CPE'},
            {'name': 'Electrical and Electronic Engineering', 'code': 'EEE'},
            {'name': 'Computer Engineering', 'code': 'CEN'},
            {'name': 'Mechanical and Industrial Engineering', 'code': 'MIE'},
            {'name': 'Civil Engineering', 'code': 'CIE'},
        ]
        
        departments = {}
        for dept_data in departments_data:
            dept, created = Department.objects.get_or_create(
                code=dept_data['code'],
                defaults={'name': dept_data['name']}
            )
            departments[dept_data['code']] = dept
            self.stdout.write(f"{'Created' if created else 'Found'} department: {dept.name}")
        
        # Programme data from FET 2026 document with correct durations
        programmes_data = [
            # ========== CHEMICAL AND PETROLEUM ENGINEERING ==========
            # BEng programmes (4 years)
            {'dept_code': 'CPE', 'degree': 'BENG', 'name': 'Chemical and Petroleum Engineering', 'option': 'Chemical Engineering', 'duration': 4, 'duration_semesters': 8, 'is_top_up': False},
            {'dept_code': 'CPE', 'degree': 'BENG', 'name': 'Chemical and Petroleum Engineering', 'option': 'Petroleum Engineering', 'duration': 4, 'duration_semesters': 8, 'is_top_up': False},
            # Top-up BEng (2 years)
            {'dept_code': 'CPE', 'degree': 'TOPUP_BENG', 'name': 'Chemical and Petroleum Engineering', 'option': 'Petroleum Engineering', 'duration': 2, 'duration_semesters': 4, 'is_top_up': True},
            
            # ========== ELECTRICAL AND ELECTRONIC ENGINEERING ==========
            # BEng programmes (4 years)
            {'dept_code': 'EEE', 'degree': 'BENG', 'name': 'Electrical and Electronic Engineering', 'option': 'Power Systems Engineering', 'duration': 4, 'duration_semesters': 8, 'is_top_up': False},
            {'dept_code': 'EEE', 'degree': 'BENG', 'name': 'Electrical and Electronic Engineering', 'option': 'Telecommunications Engineering', 'duration': 4, 'duration_semesters': 8, 'is_top_up': False},
            # MEng programmes (1 year)
            {'dept_code': 'EEE', 'degree': 'MENG', 'name': 'Electrical and Electronic Engineering', 'option': 'Power Systems Engineering', 'duration': 1, 'duration_semesters': 2, 'is_top_up': False},
            {'dept_code': 'EEE', 'degree': 'MENG', 'name': 'Electrical and Electronic Engineering', 'option': 'Telecommunications and Network Engineering', 'duration': 1, 'duration_semesters': 2, 'is_top_up': False},
            # MSc Eng programmes (2 years)
            {'dept_code': 'EEE', 'degree': 'MSC_ENG', 'name': 'Electrical and Electronic Engineering', 'option': 'Power Systems Engineering', 'duration': 2, 'duration_semesters': 4, 'is_top_up': False},
            {'dept_code': 'EEE', 'degree': 'MSC_ENG', 'name': 'Electrical and Electronic Engineering', 'option': 'Telecommunications and Network Engineering', 'duration': 2, 'duration_semesters': 4, 'is_top_up': False},
            {'dept_code': 'EEE', 'degree': 'MSC_ENG', 'name': 'Electrical and Electronic Engineering', 'option': 'Renewable Engineering', 'duration': 2, 'duration_semesters': 4, 'is_top_up': False},
            # PhD programmes (3 years)
            {'dept_code': 'EEE', 'degree': 'PHD', 'name': 'Electrical and Electronic Engineering', 'option': 'Power Systems Engineering', 'duration': 3, 'duration_semesters': 6, 'is_top_up': False},
            {'dept_code': 'EEE', 'degree': 'PHD', 'name': 'Electrical and Electronic Engineering', 'option': 'Telecommunications and Network Engineering', 'duration': 3, 'duration_semesters': 6, 'is_top_up': False},
            {'dept_code': 'EEE', 'degree': 'PHD', 'name': 'Electrical and Electronic Engineering', 'option': 'Renewable Engineering', 'duration': 3, 'duration_semesters': 6, 'is_top_up': False},
            
            # ========== COMPUTER ENGINEERING ==========
            # BEng programmes (4 years)
            {'dept_code': 'CEN', 'degree': 'BENG', 'name': 'Computer Engineering', 'option': 'Software Engineering', 'duration': 4, 'duration_semesters': 8, 'is_top_up': False},
            {'dept_code': 'CEN', 'degree': 'BENG', 'name': 'Computer Engineering', 'option': 'Network Engineering', 'duration': 4, 'duration_semesters': 8, 'is_top_up': False},
            {'dept_code': 'CEN', 'degree': 'BENG', 'name': 'Computer Engineering', 'option': 'Telecommunication & Network Engineering', 'duration': 4, 'duration_semesters': 8, 'is_top_up': False},
            # MEng programmes (1 year)
            {'dept_code': 'CEN', 'degree': 'MENG', 'name': 'Computer Engineering', 'option': 'Cryptosystems and Cyber Security', 'duration': 1, 'duration_semesters': 2, 'is_top_up': False},
            {'dept_code': 'CEN', 'degree': 'MENG', 'name': 'Computer Engineering', 'option': 'Computer Vision and Artificial Intelligence', 'duration': 1, 'duration_semesters': 2, 'is_top_up': False},
            {'dept_code': 'CEN', 'degree': 'MENG', 'name': 'Computer Engineering', 'option': 'Software Engineering, Audit and Consultations', 'duration': 1, 'duration_semesters': 2, 'is_top_up': False},
            # MSc Eng programmes (2 years)
            {'dept_code': 'CEN', 'degree': 'MSC_ENG', 'name': 'Engineering', 'option': 'Software Engineering', 'duration': 2, 'duration_semesters': 4, 'is_top_up': False},
            {'dept_code': 'CEN', 'degree': 'MSC_ENG', 'name': 'Engineering', 'option': 'Network Engineering and Security', 'duration': 2, 'duration_semesters': 4, 'is_top_up': False},
            # Top-up MSc Eng programmes (1 year)
            {'dept_code': 'CEN', 'degree': 'TOPUP_MSC', 'name': 'Engineering', 'option': 'Cryptosystems and Cyber Security', 'duration': 1, 'duration_semesters': 2, 'is_top_up': True},
            {'dept_code': 'CEN', 'degree': 'TOPUP_MSC', 'name': 'Engineering', 'option': 'Computer Vision and Artificial Intelligence', 'duration': 1, 'duration_semesters': 2, 'is_top_up': True},
            {'dept_code': 'CEN', 'degree': 'TOPUP_MSC', 'name': 'Engineering', 'option': 'Software Engineering, Audit and Consultations', 'duration': 1, 'duration_semesters': 2, 'is_top_up': True},
            # PhD programmes (3 years)
            {'dept_code': 'CEN', 'degree': 'PHD', 'name': 'Computer Engineering', 'option': 'Software Engineering', 'duration': 3, 'duration_semesters': 6, 'is_top_up': False},
            {'dept_code': 'CEN', 'degree': 'PHD', 'name': 'Computer Engineering', 'option': 'Network Security and Distributed Systems', 'duration': 3, 'duration_semesters': 6, 'is_top_up': False},
            
            # ========== MECHANICAL AND INDUSTRIAL ENGINEERING ==========
            # BEng programmes (4 years)
            {'dept_code': 'MIE', 'degree': 'BENG', 'name': 'Mechanical and Industrial Engineering', 'option': 'Mechanical Design', 'duration': 4, 'duration_semesters': 8, 'is_top_up': False},
            {'dept_code': 'MIE', 'degree': 'BENG', 'name': 'Mechanical and Industrial Engineering', 'option': 'Mechatronics Engineering', 'duration': 4, 'duration_semesters': 8, 'is_top_up': False},
            # Top-up BEng (1 year)
            {'dept_code': 'MIE', 'degree': 'TOPUP_BENG', 'name': 'Mechanical and Industrial Engineering', 'option': '', 'duration': 1, 'duration_semesters': 2, 'is_top_up': True},
            # MEng programmes (1 year)
            {'dept_code': 'MIE', 'degree': 'MENG', 'name': 'Engineering', 'option': 'Mechatronics Engineering', 'duration': 1, 'duration_semesters': 2, 'is_top_up': False},
            {'dept_code': 'MIE', 'degree': 'MENG', 'name': 'Engineering', 'option': 'Energy Engineering', 'duration': 1, 'duration_semesters': 2, 'is_top_up': False},
            {'dept_code': 'MIE', 'degree': 'MENG', 'name': 'Engineering', 'option': 'Industrial Engineering', 'duration': 1, 'duration_semesters': 2, 'is_top_up': False},
            # MSc Eng programmes (2 years)
            {'dept_code': 'MIE', 'degree': 'MSC_ENG', 'name': 'Engineering', 'option': 'Mechatronics Engineering', 'duration': 2, 'duration_semesters': 4, 'is_top_up': False},
            {'dept_code': 'MIE', 'degree': 'MSC_ENG', 'name': 'Engineering', 'option': 'Energy Engineering', 'duration': 2, 'duration_semesters': 4, 'is_top_up': False},
            {'dept_code': 'MIE', 'degree': 'MSC_ENG', 'name': 'Engineering', 'option': 'Industrial Engineering', 'duration': 2, 'duration_semesters': 4, 'is_top_up': False},
            # Top-up MSc Eng (1 year)
            {'dept_code': 'MIE', 'degree': 'TOPUP_MSC', 'name': 'Mechanical and Industrial Engineering', 'option': '', 'duration': 1, 'duration_semesters': 2, 'is_top_up': True},
            # PhD (3 years)
            {'dept_code': 'MIE', 'degree': 'PHD', 'name': 'Mechanical Engineering', 'option': '', 'duration': 3, 'duration_semesters': 6, 'is_top_up': False},
            
            # ========== CIVIL ENGINEERING ==========
            # BEng (4 years)
            {'dept_code': 'CIE', 'degree': 'BENG', 'name': 'Civil Engineering', 'option': '', 'duration': 4, 'duration_semesters': 8, 'is_top_up': False},
            # MEng (5 years)
            {'dept_code': 'CIE', 'degree': 'MENG', 'name': 'Civil Engineering', 'option': '', 'duration': 5, 'duration_semesters': 10, 'is_top_up': False},
            # Top-up MEng for BEng holders (1 year)
            {'dept_code': 'CIE', 'degree': 'TOPUP_MENG', 'name': 'Civil Engineering', 'option': '', 'duration': 1, 'duration_semesters': 2, 'is_top_up': True},
            # Top-up MEng for BTech holders (3 years)
            {'dept_code': 'CIE', 'degree': 'TOPUP_MENG', 'name': 'Civil Engineering', 'option': '', 'duration': 3, 'duration_semesters': 6, 'is_top_up': True},
            # Top-up MSc for MEng holders (1 year)
            {'dept_code': 'CIE', 'degree': 'TOPUP_MSC', 'name': 'Structural Engineering', 'option': '', 'duration': 1, 'duration_semesters': 2, 'is_top_up': True},
            {'dept_code': 'CIE', 'degree': 'TOPUP_MSC', 'name': 'Transportation Engineering', 'option': '', 'duration': 1, 'duration_semesters': 2, 'is_top_up': True},
            # MSc Eng Environmental Engineering (2 years)
            {'dept_code': 'CIE', 'degree': 'MSC_ENG', 'name': 'Environmental Engineering', 'option': '', 'duration': 2, 'duration_semesters': 4, 'is_top_up': False},
        ]
        
        programme_count = 0
        for prog_data in programmes_data:
            department = departments[prog_data['dept_code']]
            
            # Use get_or_create with natural key
            programme, created = Programme.objects.get_or_create(
                department=department,
                degree_type=prog_data['degree'],
                name=prog_data['name'],
                option_name=prog_data['option'],
                defaults={
                    'duration_years': prog_data['duration'],
                    'duration_semesters': prog_data['duration_semesters'],
                    'is_top_up': prog_data['is_top_up'],
                    'is_active': True,
                }
            )
            if created:
                programme_count += 1
                self.stdout.write(f"Created programme: {programme}")
            else:
                # Update existing programme with correct duration if needed
                if programme.duration_years != prog_data['duration']:
                    programme.duration_years = prog_data['duration']
                    programme.duration_semesters = prog_data['duration_semesters']
                    programme.save()
                    self.stdout.write(f"Updated programme duration: {programme}")
                else:
                    self.stdout.write(f"Found existing programme: {programme}")
        
        self.stdout.write(self.style.SUCCESS(f'Successfully loaded {programme_count} new programmes! Total: {Programme.objects.count()}'))