from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password',     models.CharField(max_length=128, verbose_name='password')),
                ('last_login',   models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False)),
                ('user_id',      models.AutoField(primary_key=True, serialize=False)),
                ('username',     models.CharField(max_length=50, unique=True)),
                ('full_name',    models.CharField(max_length=100)),
                ('role',         models.CharField(choices=[('admin','Administrator'),('manager','Manager'),('agent','Agent')], default='agent', max_length=10)),
                ('is_active',    models.BooleanField(default=True)),
                ('is_staff',     models.BooleanField(default=False)),
                ('created_at',   models.DateTimeField(auto_now_add=True)),
                ('employee_id',  models.IntegerField(blank=True, null=True, db_column='employee_id')),
                ('groups',       models.ManyToManyField(blank=True, related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'Website User',
                'db_table': 'auth_user_website',
            },
        ),
    ]
