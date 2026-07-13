from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import ExtractYear, ExtractMonth

from realestate.models import (Branch, Employee, Customer, Address,
                                Property, PropertyImage, PotentialBuyer,
                                BuyerInterest, Transaction, User)
from realestate.permissions import (IsAdmin, IsAdminOrManager,
                                     IsAnyRole, IsOwnerAgentOrAdmin)
from .serializers import (BranchSerializer, EmployeeSerializer,
                           CustomerSerializer, PropertyListSerializer,
                           PropertyDetailSerializer, PotentialBuyerSerializer,
                           BuyerInterestSerializer, TransactionSerializer,
                           UserSerializer)


# ── Auth ─────────────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if not user:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    refresh = RefreshToken.for_user(user)
    return Response({
        'access':    str(refresh.access_token),
        'refresh':   str(refresh),
        'user':      UserSerializer(user).data,
    })


@api_view(['POST'])
def api_logout(request):
    try:
        token = RefreshToken(request.data.get('refresh'))
        token.blacklist()
    except Exception:
        pass
    return Response({'message': 'Logged out.'})


@api_view(['GET'])
def api_me(request):
    return Response(UserSerializer(request.user).data)


# ── Branch ───────────────────────────────────────────────────────────────
class BranchViewSet(viewsets.ReadOnlyModelViewSet):
    queryset           = Branch.objects.all()
    serializer_class   = BranchSerializer
    permission_classes = [IsAdminOrManager]


# ── Employee ─────────────────────────────────────────────────────────────
class EmployeeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class   = EmployeeSerializer
    permission_classes = [IsAdminOrManager]
    filter_backends    = [filters.SearchFilter]
    search_fields      = ['first_name', 'last_name', 'email', 'phone']

    def get_queryset(self):
        qs = Employee.objects.select_related('branch').filter(Status=True)
        user = self.request.user
        # Manager sees only their branch
        if user.is_manager and user.employee:
            qs = qs.filter(branch_id=user.employee.branch_id)
        role = self.request.query_params.get('role')
        if role:
            qs = qs.filter(role=role)
        return qs

    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        emp = self.get_object()
        txns = Transaction.objects.filter(agent_id=pk)
        yearly = (txns
                  .annotate(year=ExtractYear('closing_date'))
                  .values('year')
                  .annotate(total=Sum('agreed_price'), count=Count('transaction_id'))
                  .order_by('year'))
        total_earnings = sum(
            float(t.agreed_price) *
            (float(t.buyer_commission_rate) + float(t.seller_commission_rate)) *
            float(emp.commission)
            for t in txns
        )
        return Response({
            'employee':      EmployeeSerializer(emp).data,
            'yearly_sales':  list(yearly),
            'total_earnings': round(total_earnings, 2),
            'total_deals':   txns.count(),
            'total_value':   txns.aggregate(s=Sum('agreed_price'))['s'] or 0,
        })


# ── Customer ─────────────────────────────────────────────────────────────
class CustomerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset           = Customer.objects.all()
    serializer_class   = CustomerSerializer
    permission_classes = [IsAdminOrManager]
    filter_backends    = [filters.SearchFilter]
    search_fields      = ['first_name', 'last_name', 'phone', 'email']


# ── Property ─────────────────────────────────────────────────────────────
class PropertyViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAnyRole]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['description', 'address__street_name', 'address__city',
                          'address__locality']
    ordering_fields    = ['cost_for_sell', 'Cost_for_rent', 'area', 'time_of_listing']

    def get_queryset(self):
        qs   = Property.objects.select_related('address', 'agent').prefetch_related('images')
        user = self.request.user

        if user.is_agent and user.employee:
            qs = qs.filter(agent_id=user.employee.employee_id)
        elif user.is_manager and user.employee:
            branch_agents = Employee.objects.filter(
                branch_id=user.employee.branch_id
            ).values_list('employee_id', flat=True)
            qs = qs.filter(agent_id__in=branch_agents)

        # Query params
        p = self.request.query_params
        if p.get('city'):         qs = qs.filter(address__city__icontains=p['city'])
        if p.get('type'):         qs = qs.filter(type=p['type'])
        if p.get('availability'): qs = qs.filter(availability=p['availability'])
        if p.get('bhk'):          qs = qs.filter(BHK=p['bhk'])
        if p.get('min_price'):    qs = qs.filter(cost_for_sell__gte=p['min_price'])
        if p.get('max_price'):    qs = qs.filter(cost_for_sell__lte=p['max_price'])
        if p.get('min_rent'):     qs = qs.filter(Cost_for_rent__gte=p['min_rent'])
        if p.get('max_rent'):     qs = qs.filter(Cost_for_rent__lte=p['max_rent'])
        if p.get('year_after'):   qs = qs.filter(Year_of_construction__gt=p['year_after'])
        return qs

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PropertyDetailSerializer
        return PropertyListSerializer

    @action(detail=True, methods=['get'])
    def bids(self, request, pk=None):
        prop = self.get_object()
        bids = BuyerInterest.objects.filter(property=prop).select_related('buyer')
        return Response(BuyerInterestSerializer(bids, many=True).data)


# ── Potential Buyer ───────────────────────────────────────────────────────
class PotentialBuyerViewSet(viewsets.ModelViewSet):
    queryset           = PotentialBuyer.objects.all()
    serializer_class   = PotentialBuyerSerializer
    permission_classes = [IsAnyRole]
    filter_backends    = [filters.SearchFilter]
    search_fields      = ['First_name', 'last_name', 'Contact_no', 'preferred_city']


# ── Buyer Interest ────────────────────────────────────────────────────────
class BuyerInterestViewSet(viewsets.ModelViewSet):
    serializer_class   = BuyerInterestSerializer
    permission_classes = [IsAnyRole]

    def get_queryset(self):
        qs   = BuyerInterest.objects.select_related('buyer', 'property')
        user = self.request.user
        if user.is_agent and user.employee:
            qs = qs.filter(property__agent_id=user.employee.employee_id)
        prop_id = self.request.query_params.get('property_id')
        if prop_id:
            qs = qs.filter(property_id=prop_id)
        return qs


# ── Transaction ───────────────────────────────────────────────────────────
class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class   = TransactionSerializer
    permission_classes = [IsAnyRole]

    def get_queryset(self):
        qs   = Transaction.objects.select_related(
            'property', 'property__address', 'buyer', 'seller', 'agent'
        )
        user = self.request.user
        if user.is_agent and user.employee:
            qs = qs.filter(agent_id=user.employee.employee_id)
        elif user.is_manager and user.employee:
            branch_agents = Employee.objects.filter(
                branch_id=user.employee.branch_id
            ).values_list('employee_id', flat=True)
            qs = qs.filter(agent_id__in=branch_agents)
        return qs.order_by('-closing_date')


# ── Analytics endpoints ───────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAdmin])
def admin_stats(request):
    txns = Transaction.objects.all()
    return Response({
        'total_properties':  Property.objects.count(),
        'available':         Property.objects.filter(availability='Available').count(),
        'sold':              Property.objects.filter(availability='Sold').count(),
        'rented':            Property.objects.filter(availability='Rented').count(),
        'total_transactions': txns.count(),
        'total_sales_value': txns.aggregate(s=Sum('agreed_price'))['s'] or 0,
        'total_agents':      Employee.objects.filter(role='agent', Status=True).count(),
        'total_customers':   Customer.objects.count(),
        'total_branches':    Branch.objects.count(),
    })
