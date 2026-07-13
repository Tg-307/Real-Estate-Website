import os, sys, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_project.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("\n🍂  UrbanRoots Homes — Setup Script")
print("=" * 40)

# Step 1: Migrate
print("\n[1] Running migrations...")
from django.core.management import execute_from_command_line
execute_from_command_line(['manage.py', 'migrate'])

django.setup()
from django.db import connection
from realestate.models import User

# Step 2: Ensure auth_user_website table exists
print("\n[2] Ensuring auth_user_website table exists...")
with connection.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS auth_user_website (
            user_id       INT AUTO_INCREMENT PRIMARY KEY,
            username      VARCHAR(50) NOT NULL UNIQUE,
            full_name     VARCHAR(100) NOT NULL,
            role          VARCHAR(10) NOT NULL DEFAULT 'agent',
            employee_id   INT NULL,
            password      VARCHAR(128) NOT NULL,
            is_active     TINYINT(1) NOT NULL DEFAULT 1,
            is_staff      TINYINT(1) NOT NULL DEFAULT 0,
            is_superuser  TINYINT(1) NOT NULL DEFAULT 0,
            last_login    DATETIME NULL,
            created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("   auth_user_website table ready.")

# Step 3: Create / update all website users
print("\n[3] Creating website users...")

#  (username, password, full_name, role, employee_fk, is_staff, is_superuser)
users = [
    ('admin1',   'Admin@2024',  'Super Administrator', 'admin',   None, True,  True),
    ('manager1', 'Manager@1',   'Rajan Borah',         'manager', 1,    False, False),
    ('manager2', 'Manager@2',   'Priya Dutta',         'manager', 2,    False, False),
    ('agent1',   'Agent@1',     'Nirmal Kalita',       'agent',   3,    False, False),
    ('agent2',   'Agent@2',     'Ananya Sharma',       'agent',   4,    False, False),
    ('agent3',   'Agent@3',     'Debajit Das',         'agent',   5,    False, False),
]

for username, password, full_name, role, emp_fk, is_staff, is_superuser in users:
    if not User.objects.filter(username=username).exists():
        u = User(
            username=username, full_name=full_name, role=role,
            employee_fk=emp_fk, is_active=True,
            is_staff=is_staff, is_superuser=is_superuser,
        )
        u.set_password(password)
        u.save()
        print(f"   Created : {username}")
    else:
        # Update password and ensure active
        u = User.objects.get(username=username)
        u.set_password(password)
        u.is_active = True
        u.employee_fk = emp_fk
        u.is_staff = is_staff
        u.is_superuser = is_superuser
        u.save()
        print(f"   Updated : {username}")

print("\n✅  Setup complete!")
print("\n┌─────────────────────────────────────────────┐")
print("│           Login Credentials                 │")
print("├──────────────┬─────────────┬────────────────┤")
print("│ Username     │ Password    │ Role           │")
print("├──────────────┼─────────────┼────────────────┤")
for username, password, _, role, *__ in users:
    print(f"│ {username:<12} │ {password:<11} │ {role:<14} │")
print("└──────────────┴─────────────┴────────────────┘")
print("\nNote: employee_fk links match populate_data.sql employee IDs.")
print("Run populate_data.sql in MySQL first, then this script.\n")
