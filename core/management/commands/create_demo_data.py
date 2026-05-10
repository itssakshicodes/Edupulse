"""
core/management/commands/create_demo_data.py
Run: python manage.py create_demo_data
Creates demo users, subjects, batches, and sample results.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Profile
from results.models import Subject, Batch, Result


SUBJECTS = [
    ('Data Structures',        'CS301', 'Computer Science', 3),
    ('Database Management',    'CS302', 'Computer Science', 3),
    ('Operating Systems',      'CS303', 'Computer Science', 3),
    ('Computer Networks',      'CS401', 'Computer Science', 4),
    ('Software Engineering',   'CS402', 'Computer Science', 4),
    ('Artificial Intelligence','CS403', 'Computer Science', 4),
]

STUDENTS = [
    ('Alice Johnson',  'CS2021001', 'alice21'),
    ('Bob Smith',      'CS2021002', 'bob21'),
    ('Carol Williams', 'CS2021003', 'carol21'),
    ('David Brown',    'CS2021004', 'david21'),
    ('Eva Martinez',   'CS2021005', 'eva21'),
]

MARKS = {
    'CS2021001': [85, 72, 91, 88, 76, 93],
    'CS2021002': [55, 38, 67, 72, 61, 45],
    'CS2021003': [78, 82, 44, 90, 85, 77],
    'CS2021004': [92, 88, 76, 94, 89, 95],
    'CS2021005': [65, 71, 58, 80, 74, 69],
}


class Command(BaseCommand):
    help = 'Create demo data for EduPulse'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Creating demo data...\n')

        # ── Admin ────────────────────────────────────────────────────────
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser('admin', 'admin@edupulse.edu', 'admin123')
            admin.first_name = 'System'
            admin.last_name  = 'Admin'
            admin.save()
            admin.profile.role = 'admin'
            admin.profile.save()
            self.stdout.write('  ✅ Admin: admin / admin123')

        # ── Faculty ──────────────────────────────────────────────────────
        if not User.objects.filter(username='faculty1').exists():
            f = User.objects.create_user('faculty1', 'faculty@edupulse.edu', 'faculty123',
                                          first_name='Prof. Rajesh', last_name='Kumar')
            f.profile.role = 'faculty'
            f.profile.department = 'Computer Science'
            f.profile.save()
            self.stdout.write('  ✅ Faculty: faculty1 / faculty123')

        # ── HOD ──────────────────────────────────────────────────────────
        if not User.objects.filter(username='hod1').exists():
            h = User.objects.create_user('hod1', 'hod@edupulse.edu', 'hod123',
                                          first_name='Dr. Priya', last_name='Sharma')
            h.profile.role = 'hod'
            h.profile.department = 'Computer Science'
            h.profile.save()
            self.stdout.write('  ✅ HOD: hod1 / hod123')

        # ── Batch ────────────────────────────────────────────────────────
        batch, _ = Batch.objects.get_or_create(
            name='2021-2025',
            defaults={'department': 'Computer Science', 'start_year': 2021, 'end_year': 2025}
        )
        self.stdout.write('  ✅ Batch: 2021-2025')

        # ── Subjects ─────────────────────────────────────────────────────
        subject_objs = []
        for name, code, dept, sem in SUBJECTS:
            s, _ = Subject.objects.get_or_create(
                code=code,
                defaults={'name': name, 'department': dept, 'semester': sem,
                          'max_marks': 100, 'pass_marks': 40, 'credits': 4}
            )
            subject_objs.append(s)
        self.stdout.write(f'  ✅ {len(SUBJECTS)} subjects created')

        # ── Students + Results ───────────────────────────────────────────
        admin_user = User.objects.get(username='admin')
        for full_name, roll, username in STUDENTS:
            first, *last = full_name.split()
            if not User.objects.filter(username=username).exists():
                st = User.objects.create_user(username, f'{username}@student.edu', 'student123',
                                               first_name=first, last_name=' '.join(last))
                st.profile.role = 'student'
                st.profile.roll_number = roll
                st.profile.department = 'Computer Science'
                st.profile.save()

                # Add results for each subject
                for i, subj in enumerate(subject_objs):
                    marks = MARKS.get(roll, [50]*6)[i]
                    Result.objects.get_or_create(
                        student=st, subject=subj, batch=batch,
                        semester=subj.semester,
                        defaults={'marks_obtained': marks, 'uploaded_by': admin_user}
                    )

        self.stdout.write(f'  ✅ {len(STUDENTS)} students with results created')
        self.stdout.write('\n🎉 Demo data ready! Login at http://127.0.0.1:8000/accounts/login/')
        self.stdout.write('\nDemo credentials:')
        self.stdout.write('  Admin:   admin   / admin123')
        self.stdout.write('  Faculty: faculty1 / faculty123')
        self.stdout.write('  HOD:     hod1    / hod123')
        self.stdout.write('  Student: alice21  / student123')
