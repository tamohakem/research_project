from django.core.management.base import BaseCommand
from accounts.models import Department, Programme

class Command(BaseCommand):
    help = 'Add FET academic programmes'
    
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
        
        # Programmes data - simplified version
        programmes_data = [
            # Computer Engineering Programmes
            {'dept_code': 'CEN', 'degree': 'BENG', 'name': 'Computer Engineering', 'option': 'Software Engineering', 'duration': 4, 'is_top_up': False},
            {'dept_code': 'CEN', 'degree': 'BENG', 'name': 'Computer Engineering', 'option': 'Network Engineering', 'duration': 4, 'is_top_up': False},
            {'dept_code': 'CEN', 'degree': 'BENG', 'name': 'Computer Engineering', 'option': 'Telecommunication & Network Engineering', 'duration': 4, 'is_top_up': False},
            {'dept_code': 'CEN', 'degree': 'TOPUP_BENG', 'name': 'Computer Engineering', 'option': 'Top-up', 'duration': 1, 'is_top_up': True},
            {'dept_code': 'CEN', 'degree': 'MENG', 'name': 'Computer Engineering', 'option': 'Cryptosystems and Cyber Security', 'duration': 1, 'is_top_up': False},
            {'dept_code': 'CEN', 'degree': 'MENG', 'name': 'Computer Engineering', 'option': 'Computer Vision and AI', 'duration': 1, 'is_top_up': False},
            {'dept_code': 'CEN', 'degree': 'PHD', 'name': 'Computer Engineering', 'option': 'Software Engineering', 'duration': 3, 'is_top_up': False},
            
            # Electrical Engineering Programmes
            {'dept_code': 'EEE', 'degree': 'BENG', 'name': 'Electrical and Electronic Engineering', 'option': 'Power Systems', 'duration': 4, 'is_top_up': False},
            {'dept_code': 'EEE', 'degree': 'BENG', 'name': 'Electrical and Electronic Engineering', 'option': 'Telecommunications', 'duration': 4, 'is_top_up': False},
            {'dept_code': 'EEE', 'degree': 'MENG', 'name': 'Electrical and Electronic Engineering', 'option': 'Power Systems', 'duration': 1, 'is_top_up': False},
            {'dept_code': 'EEE', 'degree': 'MENG', 'name': 'Electrical and Electronic Engineering', 'option': 'Telecommunications', 'duration': 1, 'is_top_up': False},
            {'dept_code': 'EEE', 'degree': 'PHD', 'name': 'Electrical and Electronic Engineering', 'option': 'Power Systems', 'duration': 3, 'is_top_up': False},
            
            # Mechanical Engineering Programmes
            {'dept_code': 'MIE', 'degree': 'BENG', 'name': 'Mechanical and Industrial Engineering', 'option': 'Mechanical Design', 'duration': 4, 'is_top_up': False},
            {'dept_code': 'MIE', 'degree': 'BENG', 'name': 'Mechanical and Industrial Engineering', 'option': 'Mechatronics', 'duration': 4, 'is_top_up': False},
            {'dept_code': 'MIE', 'degree': 'MENG', 'name': 'Engineering', 'option': 'Mechatronics', 'duration': 1, 'is_top_up': False},
            {'dept_code': 'MIE', 'degree': 'PHD', 'name': 'Mechanical Engineering', 'option': '', 'duration': 3, 'is_top_up': False},
            
            # Civil Engineering Programmes
            {'dept_code': 'CIE', 'degree': 'BENG', 'name': 'Civil Engineering', 'option': '', 'duration': 4, 'is_top_up': False},
            {'dept_code': 'CIE', 'degree': 'MENG', 'name': 'Civil Engineering', 'option': '', 'duration': 1, 'is_top_up': False},
            {'dept_code': 'CIE', 'degree': 'PHD', 'name': 'Civil Engineering', 'option': '', 'duration': 3, 'is_top_up': False},
            
            # Chemical Engineering Programmes
            {'dept_code': 'CPE', 'degree': 'BENG', 'name': 'Chemical and Petroleum Engineering', 'option': 'Chemical Engineering', 'duration': 4, 'is_top_up': False},
            {'dept_code': 'CPE', 'degree': 'BENG', 'name': 'Chemical and Petroleum Engineering', 'option': 'Petroleum Engineering', 'duration': 4, 'is_top_up': False},
        ]
        
        programme_count = 0
        for prog_data in programmes_data:
            department = departments[prog_data['dept_code']]
            
            # Generate a unique code
            option_part = prog_data['option'].replace(' ', '_') if prog_data['option'] else 'GEN'
            code = f"{prog_data['dept_code']}_{prog_data['degree']}_{option_part}".upper()
            
            programme, created = Programme.objects.get_or_create(
                code=code,
                defaults={
                    'department': department,
                    'degree_type': prog_data['degree'],
                    'name': prog_data['name'],
                    'option_name': prog_data['option'],
                    'duration_years': prog_data['duration'],
                    'is_top_up': prog_data['is_top_up'],
                    'is_active': True,
                }
            )
            if created:
                programme_count += 1
                self.stdout.write(f"Created programme: {programme}")
            else:
                self.stdout.write(f"Found existing programme: {programme}")
        
        self.stdout.write(self.style.SUCCESS(f'Successfully loaded {programme_count} new programmes! Total: {Programme.objects.count()}'))