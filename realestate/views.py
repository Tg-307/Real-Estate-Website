import datetime
import json

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import connection, IntegrityError
from django.db.models import Count, Q, Sum
from django.db.models.functions import ExtractYear
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import (Address, Branch, BuyerInterest, Customer, Employee,
                     PotentialBuyer, Property, PropertyImage, Transaction, User)

# ── Mock image pool (by property type) ───────────────────────────────────
MOCK_IMAGES = {
    'residential': [
        'https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=600',
        'https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=600',
        'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600',
        'https://images.unsplash.com/photo-1605276374104-dee2a0ed3cd6?w=600',
    ],
    'commercial': [
        'https://images.unsplash.com/photo-1497366754035-f200968a6e72?w=600',
        'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=600',
        'https://images.unsplash.com/photo-1554469384-e58fac16e23a?w=600',
    ],
    'land': [
        'https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=600',
        'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=600',
    ],
    'industrial': [
        'https://images.unsplash.com/photo-1513828583688-c52646db42da?w=600',
        'https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=600',
    ],
}

def get_mock_image(prop_type, prop_id):
    pool = MOCK_IMAGES.get(prop_type, MOCK_IMAGES['residential'])
    return pool[prop_id % len(pool)]

def get_emp(user):
    return user.get_employee()

def _validate_phone(phone):
    digits = ''.join(c for c in phone if c.isdigit())
    return len(digits) == 10

def _validate_aadhar(aadhar):
    digits = ''.join(c for c in aadhar if c.isdigit())
    return len(digits) == 12


# ════════════════════════════════════════════════════════════════════════
#  PUBLIC
# ════════════════════════════════════════════════════════════════════════
def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    featured = list(Property.objects.filter(
        availability='Available'
    ).select_related('address').prefetch_related('images')[:6])
    # Attach mock image where no real image exists

    stats = {
        'properties': Property.objects.count(),
        'agents':     Employee.objects.filter(role='agent', Status=True).count(),
        'branches':   Branch.objects.count(),
        'sold':       Property.objects.filter(availability='Sold').count(),
    }
    team = [
        {'name': 'Tanishk Gupta',    'roll': '2401213', 'contrib': 'Database schema design, ER diagram, stored procedures & views, Django backend architecture, agent & transaction module, JDBC admin interface queries Q1–Q2, S1–S2, S8–S9, deployment & integration.'},
        {'name': 'Parth Pande',      'roll': '2401140', 'contrib': 'Relational schema normalisation, data population scripts, branch & employee module, JDBC queries Q3–Q4, S3–S4, S10–S11, property listing workflows, frontend UI components.'},
        {'name': 'Vidhi Garg',       'roll': '2401229', 'contrib': 'Customer & buyer modules, buyer interest composite-key design, commission rate modelling, JDBC queries Q5–Q6, S5–S7, S12–S15, property search & filter logic, analytics dashboards.'},
        {'name': 'Praneet Sunkari',  'roll': '2401147', 'contrib': 'Event scheduler, trigger design, advanced SQL queries, JDBC stored-procedure calls S21–S26 via CallableStatement, manager interface, branch analysis, role-based access control, report generation.'},
    ]
    return render(request, 'realestate/landing.html', {'featured': featured, 'stats': stats, 'team': team})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        if not username or not password:
            error = 'Please enter both username and password.'
        else:
            user = authenticate(request, username=username, password=password)
            if user is None:
                error = 'Invalid credentials.'
            elif not user.is_active:
                error = 'Your account has been deactivated. Contact your manager or admin.'
            else:
                login(request, user)
                return redirect(request.GET.get('next', 'dashboard'))
    return render(request, 'realestate/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('landing')


@login_required
def dashboard(request):
    if request.user.is_admin:   return redirect('admin_dashboard')
    if request.user.is_manager: return redirect('manager_dashboard')
    return redirect('agent_dashboard')


# ════════════════════════════════════════════════════════════════════════
#  ADMIN
# ════════════════════════════════════════════════════════════════════════
@login_required
def admin_dashboard(request):
    if not request.user.is_admin:
        return redirect('dashboard')
    ctx = {
        'total_props':     Property.objects.count(),
        'available_props': Property.objects.filter(availability='Available').count(),
        'sold_props':      Property.objects.filter(availability='Sold').count(),
        'rented_props':    Property.objects.filter(availability='Rented').count(),
        'total_txns':      Transaction.objects.count(),
        'total_agents':    Employee.objects.filter(role='agent', Status=True).count(),
        'total_managers':  Employee.objects.filter(role='manager', Status=True).count(),
        'total_customers': Customer.objects.count(),
        'total_branches':  Branch.objects.count(),
        'total_buyers':    PotentialBuyer.objects.count(),
        'txn_total':       Transaction.objects.aggregate(s=Sum('agreed_price'))['s'] or 0,
        'recent_txns':     Transaction.objects.select_related('property__address', 'buyer', 'agent').order_by('-transaction_at')[:8],
        'top_agents':      Employee.objects.filter(role='agent').annotate(deals=Count('transaction')).order_by('-deals')[:5],
        'recent_props':    _props_with_mock(Property.objects.select_related('address', 'agent').prefetch_related('images').order_by('-time_of_listing')[:8]),
    }
    return render(request, 'realestate/admin_dashboard.html', ctx)


@login_required
def admin_add_manager(request):
    if not request.user.is_admin:
        return redirect('dashboard')
    branches = Branch.objects.all()
    if request.method == 'POST':
        p = request.POST
        errs = []
        if not _validate_phone(p.get('phone', '')):
            errs.append('Phone must be 10 digits.')
        if not _validate_aadhar(p.get('aadhar_no', '')):
            errs.append('Aadhar must be 12 digits.')
        if errs:
            for e in errs: messages.error(request, e)
            return render(request, 'realestate/admin_add_manager.html', {'branches': branches, 'post': p})
        try:
            emp = Employee(
                first_name=p['first_name'], last_name=p['last_name'],
                gender=p['gender'], phone=p['phone'],
                alternate_phone=p.get('alternate_phone') or None,
                email=p['email'], Aadhar_no=p['aadhar_no'],
                Apartment_no=p.get('apartment_no') or None,
                building=p.get('building') or None,
                street=p.get('street') or None,
                city=p.get('city') or None, state=p.get('state') or None,
                pincode=p.get('pincode') or None,
                role='manager',
                base_salary=float(p['base_salary']),
                commission=float(p.get('commission') or 0.30),
                date_of_joining=p.get('date_of_joining') or None,
                Status=True, branch_id=int(p['branch_id']),
            )
            emp.save()
        except Exception as e:
            messages.error(request, f"Employee record failed: {e}")
            return render(request, 'realestate/admin_add_manager.html', {'branches': branches, 'post': p})
        try:
            uname = p.get('username') or p['email'].split('@')[0]
            User.objects.create_user(
                username=uname, password=p['password'],
                full_name=f"{p['first_name']} {p['last_name']}",
                role='manager', employee_fk=emp.employee_id, is_staff=False,
            )
        except Exception as e:
            messages.error(request, f"Employee created but login account failed: {e}")
            return redirect('admin_dashboard')
        messages.success(request, f"Manager {emp.first_name} {emp.last_name} added. Login: {uname}")
        return redirect('admin_dashboard')
    return render(request, 'realestate/admin_add_manager.html', {'branches': branches})


@login_required
def admin_users(request):
    if not request.user.is_admin:
        return redirect('dashboard')
    users = User.objects.all().order_by('role', 'username')
    employees = Employee.objects.select_related('branch').all()
    return render(request, 'realestate/admin_users.html', {'users': users, 'employees': employees})


@login_required
def admin_toggle_user(request, uid):
    if not request.user.is_admin:
        return redirect('dashboard')
    u = get_object_or_404(User, pk=uid)
    if u.user_id != request.user.user_id:
        u.is_active = not u.is_active
        u.save()
        # Also sync Employee.Status
        emp = u.get_employee()
        if emp:
            emp.Status = u.is_active
            emp.save()
        messages.success(request, f"User {u.username} {'activated' if u.is_active else 'deactivated'}.")
    return redirect('admin_users')


# ════════════════════════════════════════════════════════════════════════
#  MANAGER
# ════════════════════════════════════════════════════════════════════════
@login_required
def manager_dashboard(request):
    if not (request.user.is_admin or request.user.is_manager):
        return redirect('dashboard')
    emp = get_emp(request.user)
    if not emp:
        messages.error(request, "No employee record linked. Contact admin.")
        return render(request, 'realestate/manager_dashboard.html', {'error': True})

    branch_id = emp.branch_id
    all_agents = Employee.objects.filter(branch_id=branch_id, role='agent').annotate(
        deals=Count('transaction')
    ).order_by('Status', 'first_name')
    active_agent_ids = list(all_agents.filter(Status=True).values_list('employee_id', flat=True))
    all_agent_ids    = list(all_agents.values_list('employee_id', flat=True))

    props = _props_with_mock(
        Property.objects.filter(agent_id__in=all_agent_ids)
        .select_related('address', 'agent').prefetch_related('images')
        .order_by('-time_of_listing')
    )
    # filters
    f = request.GET
    if f.get('agent_name'):
        name = f['agent_name'].strip()
        props = [p for p in props if name.lower() in p.agent.first_name.lower() or name.lower() in p.agent.last_name.lower()]
    if f.get('listing_from'):
        props = [p for p in props if p.time_of_listing.date() >= datetime.date.fromisoformat(f['listing_from'])]
    if f.get('listing_to'):
        props = [p for p in props if p.time_of_listing.date() <= datetime.date.fromisoformat(f['listing_to'])]
    if f.get('avail'):
        props = [p for p in props if p.availability == f['avail']]

    prop_stats = {
        'total':     Property.objects.filter(agent_id__in=all_agent_ids).count(),
        'available': Property.objects.filter(agent_id__in=all_agent_ids, availability='Available').count(),
        'sold':      Property.objects.filter(agent_id__in=all_agent_ids, availability='Sold').count(),
        'rented':    Property.objects.filter(agent_id__in=all_agent_ids, availability='Rented').count(),
    }
    txn_stats = Transaction.objects.filter(agent_id__in=all_agent_ids).aggregate(
        total_value=Sum('agreed_price'), count=Count('transaction_id')
    )

    ctx = {
        'employee': emp, 'branch': emp.branch,
        'all_agents': all_agents,
        'props': props[:20],
        'prop_stats': prop_stats, 'txn_stats': txn_stats,
        'filters': f,
    }
    return render(request, 'realestate/manager_dashboard.html', ctx)


@login_required
def manager_add_agent(request):
    if not (request.user.is_admin or request.user.is_manager):
        return redirect('dashboard')
    mgr_emp = get_emp(request.user)
    branch_id = mgr_emp.branch_id if mgr_emp else None

    if request.method == 'POST':
        p = request.POST
        errs = []
        if not _validate_phone(p.get('phone', '')):
            errs.append('Phone must be 10 digits.')
        if not _validate_aadhar(p.get('aadhar_no', '')):
            errs.append('Aadhar must be 12 digits.')
        if not p.get('date_of_joining'):
            errs.append('Date of joining is required.')
        if not p.get('base_salary'):
            errs.append('Base salary is required.')
        if errs:
            for e in errs: messages.error(request, e)
            return render(request, 'realestate/manager_add_agent.html', {'post': p})
        try:
            emp = Employee(
                first_name=p['first_name'], last_name=p['last_name'],
                gender=p['gender'], phone=p['phone'],
                alternate_phone=p.get('alternate_phone') or None,
                email=p['email'], Aadhar_no=p['aadhar_no'],
                Apartment_no=p.get('apartment_no') or None,
                building=p.get('building') or None,
                street=p.get('street_name') or None,
                city=p.get('city') or None, state=p.get('state') or None,
                pincode=p.get('pincode') or None,
                role='agent',
                base_salary=float(p['base_salary']),
                commission=float(p.get('commission') or 0.25),
                date_of_joining=p['date_of_joining'],
                Status=True,
                branch_id=branch_id or int(p.get('branch_id', 1)),
            )
            emp.save()
        except Exception as e:
            messages.error(request, f"Could not create employee: {e}")
            return render(request, 'realestate/manager_add_agent.html', {'post': p})
        try:
            uname = p.get('username') or p['email'].split('@')[0]
            User.objects.create_user(
                username=uname, password=p['password'],
                full_name=f"{p['first_name']} {p['last_name']}",
                role='agent', employee_fk=emp.employee_id,
            )
        except Exception as e:
            messages.error(request, f"Agent created but login failed: {e}")
            return redirect('manager_dashboard')
        messages.success(request, f"Agent {emp.first_name} {emp.last_name} added. Login: {uname}")
        return redirect('manager_dashboard')
    return render(request, 'realestate/manager_add_agent.html', {})


@login_required
def manager_deactivate_agent(request, agent_id):
    """Step 1: show available properties of agent that need reassignment."""
    if not (request.user.is_admin or request.user.is_manager):
        return redirect('dashboard')
    mgr_emp = get_emp(request.user)
    agent = get_object_or_404(Employee, pk=agent_id, role='agent')
    if mgr_emp and agent.branch_id != mgr_emp.branch_id:
        messages.error(request, "Agent not in your branch.")
        return redirect('manager_dashboard')

    available_props = Property.objects.filter(
        agent_id=agent_id, availability='Available'
    ).select_related('address')

    active_agents = Employee.objects.filter(
        branch_id=agent.branch_id, role='agent', Status=True
    ).exclude(employee_id=agent_id)

    return render(request, 'realestate/manager_deactivate_agent.html', {
        'agent': agent,
        'available_props': available_props,
        'active_agents': active_agents,
    })


@login_required
def manager_reassign_properties(request):
    """Step 2: accept reassignment map and deactivate agent."""
    if not (request.user.is_admin or request.user.is_manager):
        return redirect('dashboard')
    if request.method != 'POST':
        return redirect('manager_dashboard')

    agent_id = int(request.POST.get('agent_id'))
    agent = get_object_or_404(Employee, pk=agent_id)
    mgr_emp = get_emp(request.user)

    # Collect reassignment: prop_id -> new_agent_id
    available_props = Property.objects.filter(agent_id=agent_id, availability='Available')
    errors = []
    for prop in available_props:
        new_aid = request.POST.get(f'reassign_{prop.property_id}')
        if not new_aid:
            errors.append(f"Property #{prop.property_id} has no reassignment selected.")
        else:
            try:
                new_agent = Employee.objects.get(pk=int(new_aid), branch_id=agent.branch_id, Status=True)
                prop.agent_id = new_agent.employee_id
                prop.save()
            except Employee.DoesNotExist:
                errors.append(f"Invalid agent selected for property #{prop.property_id}.")

    if errors:
        for e in errors: messages.error(request, e)
        return redirect('manager_deactivate_agent', agent_id=agent_id)

    # Deactivate agent employee record
    agent.Status = False
    agent.save()
    # Deactivate corresponding website user
    try:
        u = User.objects.get(employee_fk=agent_id)
        u.is_active = False
        u.save()
    except User.DoesNotExist:
        pass

    messages.success(request, f"Agent {agent.first_name} {agent.last_name} deactivated. Properties reassigned.")
    return redirect('manager_dashboard')


@login_required
def manager_agent_analysis(request):
    if not (request.user.is_admin or request.user.is_manager):
        return redirect('dashboard')
    mgr_emp = get_emp(request.user)
    agent_id = request.GET.get('agent_id')

    if agent_id:
        emp_obj = get_object_or_404(Employee, pk=agent_id, role='agent')
        aid = emp_obj.employee_id
        txns = Transaction.objects.filter(agent_id=aid).select_related(
            'property__address', 'buyer', 'seller'
        ).order_by('-closing_date')
        # Filter by transaction type (sold/rented)
        txn_filter = request.GET.get('txn_type', '')
        if txn_filter == 'sold':
            txns = [t for t in txns if t.property.availability == 'Sold']
        elif txn_filter == 'rented':
            txns = [t for t in txns if t.property.availability == 'Rented']
        sold_txns   = [t for t in Transaction.objects.filter(agent_id=aid).select_related('property') if t.property.availability == 'Sold']
        rented_txns = [t for t in Transaction.objects.filter(agent_id=aid).select_related('property') if t.property.availability == 'Rented']
        yearly = (Transaction.objects.filter(agent_id=aid)
                  .annotate(yr=ExtractYear('closing_date'))
                  .values('yr').annotate(count=Count('transaction_id'), total=Sum('agreed_price'))
                  .order_by('yr'))
        total_earnings = sum(
            float(t.agreed_price) * (float(t.buyer_commission_rate) + float(t.seller_commission_rate)) * float(emp_obj.commission)
            for t in txns
        )
        return render(request, 'realestate/manager_agent_detail.html', {
            'agent': emp_obj, 'txns': txns, 'sold_txns': sold_txns,
            'rented_txns': rented_txns, 'yearly': list(yearly),
            'total_earnings': round(total_earnings, 2),
            'deal_count': len(txns),
            'total_value': sum(float(t.agreed_price) for t in txns) if txns else 0,
            'txn_filter': txn_filter,
        })

    # List all agents in branch
    if mgr_emp:
        agents = Employee.objects.filter(branch_id=mgr_emp.branch_id, role='agent').annotate(
            deals=Count('transaction')
        ).order_by('Status', '-deals')
    else:
        agents = Employee.objects.filter(role='agent').annotate(deals=Count('transaction'))
    return render(request, 'realestate/manager_agent_analysis.html', {'agents': agents})


@login_required
def branch_analysis(request):
    if not (request.user.is_admin or request.user.is_manager):
        return redirect('dashboard')
    mgr_emp = get_emp(request.user)
    branch_id = mgr_emp.branch_id if mgr_emp else None

    all_agent_ids = list(Employee.objects.filter(branch_id=branch_id, role='agent')
                         .values_list('employee_id', flat=True)) if branch_id else []

    qs = Transaction.objects.filter(agent_id__in=all_agent_ids).select_related(
        'property__address', 'buyer', 'agent'
    )

    # Filters
    f = request.GET
    if f.get('agent_name'):
        name = f['agent_name'].strip()
        matching = Employee.objects.filter(
            branch_id=branch_id, role='agent'
        ).filter(Q(first_name__icontains=name) | Q(last_name__icontains=name))
        qs = qs.filter(agent_id__in=matching.values_list('employee_id', flat=True))
    if f.get('status'):
        qs = qs.filter(property__availability=f['status'])
    if f.get('city'):
        qs = qs.filter(property__address__city__icontains=f['city'])
    if f.get('state'):
        qs = qs.filter(property__address__state__icontains=f['state'])
    if f.get('min_price'):
        qs = qs.filter(agreed_price__gte=float(f['min_price']))
    if f.get('max_price'):
        qs = qs.filter(agreed_price__lte=float(f['max_price']))
    if f.get('date_from'):
        qs = qs.filter(closing_date__gte=f['date_from'])
    if f.get('date_to'):
        qs = qs.filter(closing_date__lte=f['date_to'])

    total_revenue = qs.aggregate(s=Sum('agreed_price'))['s'] or 0
    total_commission = sum(
        float(t.agreed_price) * (float(t.buyer_commission_rate) + float(t.seller_commission_rate))
        for t in qs
    )
    yearly = (qs.annotate(yr=ExtractYear('closing_date'))
               .values('yr').annotate(count=Count('transaction_id'), total=Sum('agreed_price'))
               .order_by('yr'))

    return render(request, 'realestate/branch_analysis.html', {
        'txns': qs.order_by('-closing_date'),
        'total_revenue': total_revenue,
        'total_commission': round(total_commission, 2),
        'yearly': list(yearly),
        'filters': f,
        'branch': mgr_emp.branch if mgr_emp else None,
        'agents': Employee.objects.filter(branch_id=branch_id, role='agent') if branch_id else [],
    })


@login_required
def transaction_detail(request, txn_id):
    txn = get_object_or_404(
        Transaction.objects.select_related(
            'property__address', 'property__agent__branch',
            'buyer', 'seller', 'agent__branch'
        ), pk=txn_id
    )
    return render(request, 'realestate/transaction_detail.html', {'txn': txn})


# ════════════════════════════════════════════════════════════════════════
#  AGENT
# ════════════════════════════════════════════════════════════════════════
@login_required
def agent_dashboard(request):
    emp = get_emp(request.user)
    if not emp:
        messages.error(request, "No employee record linked. Contact your manager.")
        return render(request, 'realestate/agent_dashboard.html', {'error': True})

    agent_id  = emp.employee_id
    branch_id = emp.branch_id

    my_props = _props_with_mock(
        Property.objects.filter(agent_id=agent_id)
        .select_related('address').prefetch_related('images')
    )
    prop_stats = {
        'total':     Property.objects.filter(agent_id=agent_id).count(),
        'available': Property.objects.filter(agent_id=agent_id, availability='Available').count(),
        'sold':      Property.objects.filter(agent_id=agent_id, availability='Sold').count(),
        'rented':    Property.objects.filter(agent_id=agent_id, availability='Rented').count(),
    }
    my_txns = Transaction.objects.filter(agent_id=agent_id).select_related(
        'property__address', 'buyer', 'seller'
    ).order_by('-closing_date')
    total_earnings = sum(
        float(t.agreed_price) * (float(t.buyer_commission_rate) + float(t.seller_commission_rate)) * float(emp.commission)
        for t in my_txns
    )
    with connection.cursor() as cur:
        cur.execute("""
            SELECT bi.buyer_id, pb.First_name, pb.last_name, pb.Contact_no,
                   bi.property_id, p.description, a.city,
                   bi.offer_amount, bi.interest_date
            FROM buyer_interest bi
            JOIN potential_buyer pb ON bi.buyer_id = pb.buyer_id
            JOIN property p ON bi.property_id = p.property_id
            JOIN address a ON p.address_id = a.address_id
            WHERE p.agent_id = %s
            ORDER BY bi.interest_date DESC LIMIT 10
        """, [agent_id])
        cols = [c[0] for c in cur.description]
        bids_raw = [dict(zip(cols, row)) for row in cur.fetchall()]

    ctx = {
        'employee': emp, 'my_props': my_props, 'prop_stats': prop_stats,
        'my_txns': my_txns[:8], 'txn_count': my_txns.count(),
        'total_earnings': round(total_earnings, 2),
        'txn_total': my_txns.aggregate(s=Sum('agreed_price'))['s'] or 0,
        'bids_raw': bids_raw,
    }
    return render(request, 'realestate/agent_dashboard.html', ctx)


@login_required
def agent_add_buyer(request):
    if request.method == 'POST':
        p = request.POST
        errs = []
        if not _validate_phone(p.get('contact_no', '')):
            errs.append('Contact number must be 10 digits.')
        if errs:
            for e in errs: messages.error(request, e)
            return render(request, 'realestate/agent_add_buyer.html', {'post': p})
        try:
            pb = PotentialBuyer(
                First_name=p['first_name'], last_name=p['last_name'],
                Contact_no=p['contact_no'],
                preferred_city=p.get('preferred_city') or None,
                preferred_state=p.get('preferred_state') or None,
                preferred_type=p.get('preferred_type') or None,
                preferred_BHK=int(p['preferred_bhk']) if p.get('preferred_bhk') else None,
                preferred_area=float(p['preferred_area']) if p.get('preferred_area') else None,
                min_price=float(p['min_price']) if p.get('min_price') else None,
                max_price=float(p['max_price']) if p.get('max_price') else None,
                Choice=p.get('choice') or None,
            )
            pb.save()
            messages.success(request, f"Buyer {pb.First_name} {pb.last_name} registered.")
            nxt = p.get('next', '')
            if nxt:
                return redirect(nxt)
        except Exception as e:
            messages.error(request, f"Error: {e}")
        return redirect('potential_buyers_list')
    nxt = request.GET.get('next', '')
    return render(request, 'realestate/agent_add_buyer.html', {'next': nxt})


@login_required
def potential_buyers_list(request):
    emp = get_emp(request.user)
    qs = PotentialBuyer.objects.all().order_by('-created_at')
    f = request.GET
    if f.get('name'):
        qs = qs.filter(Q(First_name__icontains=f['name']) | Q(last_name__icontains=f['name']))
    if f.get('phone'):
        qs = qs.filter(Contact_no__icontains=f['phone'])
    if f.get('type'):
        qs = qs.filter(preferred_type=f['type'])
    if f.get('choice'):
        qs = qs.filter(Choice=f['choice'])
    if f.get('city'):
        qs = qs.filter(preferred_city__icontains=f['city'])
    return render(request, 'realestate/potential_buyers_list.html', {
        'buyers': qs, 'filters': f, 'count': qs.count()
    })


@login_required
def agent_add_property(request):
    emp = get_emp(request.user)
    if not emp:
        messages.error(request, "No employee record found.")
        return redirect('dashboard')
    customers = Customer.objects.filter(role_type__in=['seller', 'both']).order_by('first_name')

    if request.method == 'POST':
        p = request.POST
        errs = []
        has_price = p.get('cost_for_sell') or p.get('cost_for_rent')
        if not has_price:
            errs.append('At least one of Sell Price or Rent Price is required.')
        if not p.get('year_construction'):
            errs.append('Year of construction is required.')

        # Resolve seller
        seller_id = None
        use_new = p.get('use_new_seller') == '1'
        if use_new:
            # Validate and create new seller
            ns_phone  = p.get('new_seller_phone', '')
            ns_aadhar = p.get('new_seller_aadhar', '')
            if not _validate_phone(ns_phone):
                errs.append('Seller phone must be 10 digits.')
            if not _validate_aadhar(ns_aadhar):
                errs.append('Seller Aadhar must be 12 digits.')
        else:
            if not p.get('seller_id'):
                errs.append('Please select or register a seller.')
            else:
                seller_id = int(p['seller_id'])

        if errs:
            for e in errs: messages.error(request, e)
            return render(request, 'realestate/agent_add_property.html',
                          {'customers': customers, 'employee': emp, 'post': p})
        try:
            if use_new:
                new_seller = Customer(
                    first_name=p.get('new_seller_first_name', ''),
                    last_name=p.get('new_seller_last_name', ''),
                    phone=p['new_seller_phone'],
                    alternate_phone=p.get('new_seller_alt_phone') or None,
                    email=p.get('new_seller_email') or None,
                    Aadhar_no=p['new_seller_aadhar'],
                    street=p.get('new_seller_street') or None,
                    city=p.get('new_seller_city') or None,
                    state=p.get('new_seller_state') or None,
                    pincode=p.get('new_seller_pincode') or None,
                    role_type='seller',
                )
                new_seller.save()
                seller_id = new_seller.customer_id
            addr = Address(
                street_name=p['street_name'],
                street_number=p.get('street_number') or None,
                locality=p.get('locality') or None,
                city=p['city'], state=p['state'], pincode=p['pincode'],
                Apartment_no=p.get('apartment_no') or None,
                building=p.get('building') or None,
                country=p.get('country') or 'India',
            )
            addr.save()
            prop = Property(
                type=p['type'],
                BHK=int(p['bhk']) if p.get('bhk') else None,
                area=float(p['area']),
                CARPET_area=float(p['carpet_area']) if p.get('carpet_area') else None,
                Cost_for_rent=float(p['cost_for_rent']) if p.get('cost_for_rent') else None,
                cost_for_sell=float(p['cost_for_sell']) if p.get('cost_for_sell') else None,
                Year_of_construction=int(p['year_construction']),
                seller_commission_rate=float(p.get('seller_commission_rate') or 0.030),
                availability='Available',
                description=p.get('description') or None,
                address_id=addr.address_id,
                seller_id=seller_id,
                agent_id=emp.employee_id,
            )
            prop.save()
            img_url = p.get('image_url', '').strip()
            if not img_url:
                img_url = get_mock_image(prop.type, prop.property_id)
            PropertyImage(property_id=prop.property_id, image_url=img_url, caption='Primary photo', is_primary=True).save()
            messages.success(request, f"Property #{prop.property_id} listed.")
            return redirect('property_detail', pk=prop.property_id)
        except Exception as e:
            messages.error(request, f"Error: {e}")

    return render(request, 'realestate/agent_add_property.html', {'customers': customers, 'employee': emp})


# ════════════════════════════════════════════════════════════════════════
#  BID
# ════════════════════════════════════════════════════════════════════════
@login_required
def agent_add_bid(request, prop_id):
    emp = get_emp(request.user)
    prop = get_object_or_404(Property, pk=prop_id)
    # Only agent who owns the property can add bids
    if request.user.is_agent and emp and prop.agent_id != emp.employee_id:
        messages.error(request, "You can only add bids for your own properties.")
        return redirect('property_detail', pk=prop_id)

    f = request.GET
    buyers_qs = PotentialBuyer.objects.all().order_by('First_name')
    if f.get('search_name'):
        buyers_qs = buyers_qs.filter(
            Q(First_name__icontains=f['search_name']) | Q(last_name__icontains=f['search_name'])
        )
    if f.get('search_phone'):
        buyers_qs = buyers_qs.filter(Contact_no__icontains=f['search_phone'])

    if request.method == 'POST':
        p = request.POST
        buyer_id = int(p['buyer_id'])
        try:
            with connection.cursor() as cur:
                cur.execute("""
                    INSERT INTO buyer_interest
                        (buyer_id, property_id, offer_amount, buyer_commission_rate, interest_date, notes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE offer_amount=%s, notes=%s
                """, [
                    buyer_id, prop_id,
                    float(p['offer_amount']) if p.get('offer_amount') else None,
                    float(p.get('commission_rate') or 0.005),
                    datetime.date.today(),
                    p.get('notes') or None,
                    float(p['offer_amount']) if p.get('offer_amount') else None,
                    p.get('notes') or None,
                ])
            messages.success(request, "Bid recorded.")
        except Exception as e:
            messages.error(request, f"Error: {e}")
        return redirect('property_detail', pk=prop_id)

    return render(request, 'realestate/agent_add_bid.html', {
        'property': prop, 'buyers': buyers_qs,
        'filters': f,
        'add_buyer_url': f"/dashboard/agent/add-buyer/?next=/properties/{prop_id}/bid/",
    })


# ════════════════════════════════════════════════════════════════════════
#  TRANSACTION (multi-step)
# ════════════════════════════════════════════════════════════════════════
@login_required
def agent_create_transaction(request, prop_id):
    emp = get_emp(request.user)
    prop = get_object_or_404(
        Property.objects.select_related('address', 'seller'), pk=prop_id
    )

    if request.user.is_agent and emp and prop.agent_id != emp.employee_id:
        messages.error(request, "You can only transact on your own properties.")
        return redirect('agent_dashboard')
    if prop.availability in ('Sold', 'Rented'):
        messages.error(request, f"This property is already {prop.availability}.")
        return redirect('property_detail', pk=prop_id)

    # Fetch bids for this property via raw SQL
    with connection.cursor() as cur:
        cur.execute("""
            SELECT bi.buyer_id, pb.First_name, pb.last_name, pb.Contact_no,
                   bi.offer_amount, bi.buyer_commission_rate, bi.notes,
                   bi.interest_date
            FROM buyer_interest bi
            JOIN potential_buyer pb ON bi.buyer_id = pb.buyer_id
            WHERE bi.property_id = %s
            ORDER BY bi.offer_amount DESC
        """, [prop_id])
        cols = [c[0] for c in cur.description]
        bids = [dict(zip(cols, row)) for row in cur.fetchall()]

    step = request.GET.get('step', '1')

    # ── STEP 1: select interested buyer ──────────────────────────────────
    if step == '1':
        return render(request, 'realestate/transaction_step1.html', {
            'property': prop, 'bids': bids,
        })

    # ── STEP 2: aadhar check → prefill or new customer form ──────────────
    if step == '2':
        buyer_id   = request.GET.get('buyer_id') or request.POST.get('buyer_id')
        bid_buyer  = next((b for b in bids if str(b['buyer_id']) == str(buyer_id)), None)
        if not bid_buyer:
            messages.error(request, "Select an interested buyer first.")
            return redirect(f'/properties/{prop_id}/transaction/?step=1')

        # Try aadhar check
        aadhar = request.POST.get('aadhar_no', '').strip()
        existing_customer = None
        if aadhar:
            try:
                existing_customer = Customer.objects.get(Aadhar_no=aadhar)
            except Customer.DoesNotExist:
                pass
        return render(request, 'realestate/transaction_step2.html', {
            'property': prop, 'bid_buyer': bid_buyer,
            'buyer_id': buyer_id,
            'existing_customer': existing_customer,
            'aadhar': aadhar,
        })

    # ── STEP 3: transaction details form ─────────────────────────────────
    if step == '3':
        buyer_id          = request.POST.get('buyer_id')
        customer_id       = request.POST.get('customer_id') or None
        use_existing      = request.POST.get('use_existing') == '1'

        bid_buyer = next((b for b in bids if str(b['buyer_id']) == str(buyer_id)), None)
        return render(request, 'realestate/transaction_step3.html', {
            'property': prop,
            'bid_buyer': bid_buyer,
            'buyer_id': buyer_id,
            'customer_id': customer_id,
            'use_existing': use_existing,
            # Pass all POST data forward as hidden fields
            'form_data': request.POST,
        })

    # ── FINAL POST: commit everything ────────────────────────────────────
    if request.method == 'POST' and step == 'commit':
        p = request.POST
        buyer_id    = p.get('buyer_id')
        customer_id = p.get('customer_id') or None
        use_existing = p.get('use_existing') == '1'

        errs = []
        # Validate closing date <= today
        try:
            closing = datetime.date.fromisoformat(p['closing_date'])
            if closing > datetime.date.today():
                errs.append("Closing date must be on or before today.")
            if closing < prop.time_of_listing.date():
                errs.append("Closing date cannot be before listing date.")
        except (KeyError, ValueError):
            errs.append("Invalid closing date.")

        if not p.get('buyer_commission_rate'):
            errs.append("Buyer commission rate is required.")
        if not p.get('seller_commission_rate'):
            errs.append("Seller commission rate is required.")
        if not p.get('agreed_price'):
            errs.append("Agreed price is required.")

        if errs:
            for e in errs: messages.error(request, e)
            return redirect(f'/properties/{prop_id}/transaction/?step=1')

        # 1. Create or resolve customer
        if use_existing and customer_id:
            customer = get_object_or_404(Customer, pk=customer_id)
            # If they currently are 'seller', upgrade to 'both'
            if customer.role_type == 'seller':
                customer.role_type = 'both'
                customer.save()
        else:
            # Validate new customer phone/aadhar
            if not _validate_phone(p.get('cust_phone', '')):
                messages.error(request, "Customer phone must be 10 digits.")
                return redirect(f'/properties/{prop_id}/transaction/?step=1')
            if not _validate_aadhar(p.get('cust_aadhar', '')):
                messages.error(request, "Customer Aadhar must be 12 digits.")
                return redirect(f'/properties/{prop_id}/transaction/?step=1')
            try:
                customer = Customer(
                    first_name=p['cust_first_name'], last_name=p['cust_last_name'],
                    phone=p['cust_phone'],
                    alternate_phone=p.get('cust_alt_phone') or None,
                    email=p.get('cust_email') or None,
                    Aadhar_no=p['cust_aadhar'],
                    apartment_no=p.get('cust_apt') or None,
                    street=p.get('cust_street') or None,
                    city=p.get('cust_city') or None,
                    state=p.get('cust_state') or None,
                    pincode=p.get('cust_pincode') or None,
                    role_type='buyer',
                )
                customer.save()
            except Exception as e:
                messages.error(request, f"Could not create customer: {e}")
                return redirect(f'/properties/{prop_id}/transaction/?step=1')

        # 2. Create Transaction
        try:
            txn = Transaction(
                property_id=prop_id,
                buyer_id=customer.customer_id,
                seller_id=prop.seller_id,
                agent_id=prop.agent_id,
                agreed_price=float(p['agreed_price']),
                buyer_commission_rate=float(p['buyer_commission_rate']),
                seller_commission_rate=float(p['seller_commission_rate']),
                closing_date=closing,
                comments=p.get('comments') or None,
            )
            txn.save()
        except Exception as e:
            messages.error(request, f"Transaction failed: {e}")
            return redirect(f'/properties/{prop_id}/transaction/?step=1')

        # 3. Mark property sold/rented
        new_status = p.get('new_status', 'Sold')
        prop.availability = new_status
        prop.save()

        # 4. Delete all bids for this property (at API level — no trigger needed)
        with connection.cursor() as cur:
            cur.execute("DELETE FROM buyer_interest WHERE property_id = %s", [prop_id])

        # 5. Remove potential buyer record (they're now a customer)
        pb_id = p.get('buyer_id')
        if pb_id:
            try:
                PotentialBuyer.objects.get(pk=int(pb_id)).delete()
            except PotentialBuyer.DoesNotExist:
                pass

        messages.success(request, f"Transaction #{txn.transaction_id} committed. Property marked {new_status}.")
        return redirect('property_detail', pk=prop_id)

    return redirect(f'/properties/{prop_id}/transaction/?step=1')


# ════════════════════════════════════════════════════════════════════════
#  PROPERTY SEARCH / DETAIL
# ════════════════════════════════════════════════════════════════════════
@login_required
def property_search(request):
    user = request.user
    emp  = get_emp(user)

    qs = Property.objects.select_related('address', 'agent').prefetch_related('images')

    # Scope filter: agent sees own OR all branch props
    scope = request.GET.get('scope', 'mine')
    if user.is_agent and emp:
        branch_agent_ids = list(Employee.objects.filter(
            branch_id=emp.branch_id
        ).values_list('employee_id', flat=True))
        if scope == 'branch':
            qs = qs.filter(agent_id__in=branch_agent_ids)
        else:
            qs = qs.filter(agent_id=emp.employee_id)
    elif user.is_manager and emp:
        branch_agent_ids = list(Employee.objects.filter(
            branch_id=emp.branch_id
        ).values_list('employee_id', flat=True))
        qs = qs.filter(agent_id__in=branch_agent_ids)

    p = request.GET
    if p.get('city'):         qs = qs.filter(address__city__icontains=p['city'])
    if p.get('type'):         qs = qs.filter(type=p['type'])
    if p.get('availability'): qs = qs.filter(availability=p['availability'])
    if p.get('bhk'):          qs = qs.filter(BHK=int(p['bhk']))
    if p.get('min_price'):    qs = qs.filter(cost_for_sell__gte=float(p['min_price']))
    if p.get('max_price'):    qs = qs.filter(cost_for_sell__lte=float(p['max_price']))
    if p.get('max_rent'):     qs = qs.filter(Cost_for_rent__lte=float(p['max_rent']))

    props = _props_with_mock(qs)
    return render(request, 'realestate/property_search.html', {
        'properties': props, 'filters': p, 'count': len(props), 'scope': scope
    })


@login_required
def property_detail(request, pk):
    prop = get_object_or_404(
        Property.objects.select_related('address', 'agent__branch', 'seller').prefetch_related('images'),
        pk=pk
    )
    user = request.user
    emp  = get_emp(user)

    # Agent: can view any branch property, but only act on own
    if user.is_agent and emp:
        branch_agent_ids = list(Employee.objects.filter(
            branch_id=emp.branch_id
        ).values_list('employee_id', flat=True))
        if prop.agent_id not in branch_agent_ids:
            messages.error(request, "Access denied.")
            return redirect('property_search')

    with connection.cursor() as cur:
        cur.execute("""
            SELECT bi.buyer_id, pb.First_name, pb.last_name, pb.Contact_no,
                   bi.offer_amount, bi.buyer_commission_rate, bi.interest_date, bi.notes
            FROM buyer_interest bi
            JOIN potential_buyer pb ON bi.buyer_id = pb.buyer_id
            WHERE bi.property_id = %s
            ORDER BY bi.offer_amount DESC
        """, [pk])
        cols = [c[0] for c in cur.description]
        bids = [dict(zip(cols, row)) for row in cur.fetchall()]

    txns = Transaction.objects.filter(property_id=pk).select_related(
        'buyer', 'seller', 'agent'
    ).order_by('-closing_date')

    is_own_property = user.is_admin or user.is_manager or (
        user.is_agent and emp and prop.agent_id == emp.employee_id
    )
    already_closed = prop.availability in ('Sold', 'Rented')



    return render(request, 'realestate/property_detail.html', {
        'property': prop, 'bids': bids, 'transactions': txns,
        'is_own_property': is_own_property,
        'already_closed': already_closed,
        'employee': emp,
    })


@login_required
def agent_update_availability(request, prop_id):
    emp  = get_emp(request.user)
    prop = get_object_or_404(Property, pk=prop_id)

    if request.user.is_agent and emp and prop.agent_id != emp.employee_id:
        messages.error(request, "Not your property.")
        return redirect('property_detail', pk=prop_id)

    if prop.availability in ('Sold', 'Rented'):
        messages.error(request, "Cannot change availability of a sold/rented property.")
        return redirect('property_detail', pk=prop_id)

    if request.method == 'POST':
        new_status = request.POST.get('availability')
        if new_status in ('Available', 'Not Available'):
            prop.availability = new_status
            prop.save()
            messages.success(request, f"Availability updated to '{new_status}'.")
        else:
            messages.error(request, "Only 'Available' or 'Not Available' can be set manually.")
    return redirect('property_detail', pk=prop_id)


# ════════════════════════════════════════════════════════════════════════
#  ANALYTICS (agent's own view)
# ════════════════════════════════════════════════════════════════════════
@login_required
def agent_analytics(request):
    user    = request.user
    emp_obj = get_emp(user) if user.is_agent else None
    if not emp_obj:
        return redirect('dashboard')

    aid  = emp_obj.employee_id
    txns = Transaction.objects.filter(agent_id=aid).select_related('property__address', 'buyer')
    props = Property.objects.filter(agent_id=aid).select_related('address')
    yearly = (txns.annotate(yr=ExtractYear('closing_date'))
              .values('yr').annotate(count=Count('transaction_id'), total=Sum('agreed_price'))
              .order_by('yr'))
    total_earnings = sum(
        float(t.agreed_price) *
        (float(t.buyer_commission_rate) + float(t.seller_commission_rate)) *
        float(emp_obj.commission)
        for t in txns
    )
    return render(request, 'realestate/agent_analytics.html', {
        'employee': emp_obj, 'txns': txns.order_by('-closing_date')[:20],
        'props': props, 'yearly': list(yearly),
        'total_earnings': round(total_earnings, 2),
        'deal_count': txns.count(),
        'total_value': txns.aggregate(s=Sum('agreed_price'))['s'] or 0,
    })


# ════════════════════════════════════════════════════════════════════════
#  AJAX
# ════════════════════════════════════════════════════════════════════════
@login_required
def ajax_check_aadhar(request):
    aadhar = request.GET.get('aadhar', '').strip()
    try:
        c = Customer.objects.get(Aadhar_no=aadhar)
        return JsonResponse({
            'found': True,
            'customer_id': c.customer_id,
            'first_name': c.first_name, 'last_name': c.last_name,
            'phone': c.phone, 'email': c.email or '',
            'alternate_phone': c.alternate_phone or '',
            'apartment_no': c.apartment_no or '',
            'street': c.street or '', 'city': c.city or '',
            'state': c.state or '', 'pincode': c.pincode or '',
            'role_type': c.role_type,
        })
    except Customer.DoesNotExist:
        return JsonResponse({'found': False})


@login_required
def ajax_seller_lookup(request):
    aadhar = request.GET.get('aadhar', '').strip()
    try:
        c = Customer.objects.get(Aadhar_no=aadhar, role_type__in=['seller', 'both'])
        return JsonResponse({'found': True, 'customer_id': c.customer_id,
                             'name': f"{c.first_name} {c.last_name}", 'phone': c.phone})
    except Customer.DoesNotExist:
        return JsonResponse({'found': False})


# ── helpers ───────────────────────────────────────────────────────────────
def _props_with_mock(qs):
    """Return list of Property objects (images not needed for display)."""
    return list(qs)


# ════════════════════════════════════════════════════════════════════════
#  UPDATE INTERFACES
# ════════════════════════════════════════════════════════════════════════
@login_required
def update_employee_profile(request):
    """Agent or Manager can update their own contact details."""
    emp = get_emp(request.user)
    if not emp:
        messages.error(request, "No employee record linked.")
        return redirect('dashboard')

    if request.method == 'POST':
        p = request.POST
        errs = []
        if p.get('phone') and not _validate_phone(p['phone']):
            errs.append('Phone must be 10 digits.')
        if p.get('alternate_phone') and not _validate_phone(p['alternate_phone']):
            errs.append('Alternate phone must be 10 digits.')
        if errs:
            for e in errs: messages.error(request, e)
            return render(request, 'realestate/update_employee.html', {'emp': emp})
        try:
            if p.get('phone'):         emp.phone = p['phone']
            if p.get('alternate_phone'): emp.alternate_phone = p['alternate_phone'] or None
            if p.get('email'):         emp.email = p['email']
            if p.get('street'):        emp.street = p['street']
            if p.get('city'):          emp.city = p['city']
            if p.get('state'):         emp.state = p['state']
            if p.get('pincode'):       emp.pincode = p['pincode']
            emp.save()
            messages.success(request, "Profile updated successfully.")
        except Exception as e:
            messages.error(request, f"Update failed: {e}")
        return redirect('dashboard')

    return render(request, 'realestate/update_employee.html', {'emp': emp})


@login_required
def update_property(request, prop_id):
    """Agent who owns property can update description, prices, image URL."""
    emp  = get_emp(request.user)
    prop = get_object_or_404(Property, pk=prop_id)

    if request.user.is_agent and emp and prop.agent_id != emp.employee_id:
        messages.error(request, "Not your property.")
        return redirect('property_detail', pk=prop_id)
    if prop.availability in ('Sold', 'Rented'):
        messages.error(request, "Cannot edit a sold/rented property.")
        return redirect('property_detail', pk=prop_id)

    if request.method == 'POST':
        p = request.POST
        errs = []
        if not (p.get('cost_for_sell') or p.get('cost_for_rent')):
            errs.append("At least one of Sell Price or Rent is required.")
        if errs:
            for e in errs: messages.error(request, e)
            return render(request, 'realestate/update_property.html', {'property': prop})
        try:
            if p.get('description'):   prop.description = p['description']
            prop.cost_for_sell = float(p['cost_for_sell']) if p.get('cost_for_sell') else None
            prop.Cost_for_rent = float(p['cost_for_rent']) if p.get('cost_for_rent') else None
            if p.get('bhk'):           prop.BHK = int(p['bhk'])
            if p.get('area'):          prop.area = float(p['area'])
            if p.get('carpet_area'):   prop.CARPET_area = float(p['carpet_area'])
            if p.get('seller_commission_rate'): prop.seller_commission_rate = float(p['seller_commission_rate'])
            prop.save()
            # Update primary image if new URL given
            img_url = p.get('image_url', '').strip()
            if img_url:
                existing = prop.images.filter(is_primary=True).first()
                if existing:
                    existing.image_url = img_url
                    existing.save()
                else:
                    PropertyImage(property_id=prop.property_id, image_url=img_url,
                                  caption='Primary photo', is_primary=True).save()
            messages.success(request, f"Property #{prop.property_id} updated.")
        except Exception as e:
            messages.error(request, f"Update failed: {e}")
        return redirect('property_detail', pk=prop_id)

    return render(request, 'realestate/update_property.html', {'property': prop})
