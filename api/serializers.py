from rest_framework import serializers
from realestate.models import (Branch, Employee, Customer, Address,
                                Property, PropertyImage, PotentialBuyer,
                                BuyerInterest, Transaction, User)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ('user_id', 'username', 'full_name', 'role')


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Branch
        fields = '__all__'


class EmployeeSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.branch_name', read_only=True)
    full_name   = serializers.SerializerMethodField()

    class Meta:
        model  = Employee
        fields = ('employee_id', 'first_name', 'last_name', 'full_name',
                  'gender', 'phone', 'email', 'role', 'base_salary',
                  'commission', 'date_of_joining', 'Status', 'branch_id', 'branch_name')

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Address
        fields = '__all__'


class CustomerSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model  = Customer
        fields = ('customer_id', 'first_name', 'last_name', 'full_name',
                  'phone', 'alternate_phone', 'email', 'city', 'state',
                  'pincode', 'role_type')

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PropertyImage
        fields = ('image_id', 'image_url', 'caption', 'is_primary', 'uploaded_at')


class PropertyListSerializer(serializers.ModelSerializer):
    city          = serializers.CharField(source='address.city',        read_only=True)
    street_name   = serializers.CharField(source='address.street_name', read_only=True)
    locality      = serializers.CharField(source='address.locality',    read_only=True)
    agent_name    = serializers.SerializerMethodField()
    primary_image = serializers.CharField(read_only=True)

    class Meta:
        model  = Property
        fields = ('property_id', 'type', 'BHK', 'area', 'CARPET_area',
                  'Cost_for_rent', 'cost_for_sell', 'Year_of_construction',
                  'seller_commission_rate', 'availability', 'description',
                  'time_of_listing', 'city', 'street_name', 'locality',
                  'agent_name', 'primary_image')

    def get_agent_name(self, obj):
        return f"{obj.agent.first_name} {obj.agent.last_name}"


class PropertyDetailSerializer(serializers.ModelSerializer):
    address       = AddressSerializer(read_only=True)
    agent         = EmployeeSerializer(read_only=True)
    seller        = CustomerSerializer(read_only=True)
    images        = PropertyImageSerializer(many=True, read_only=True)
    buyer_comm_amount   = serializers.SerializerMethodField()
    seller_comm_amount  = serializers.SerializerMethodField()

    class Meta:
        model  = Property
        fields = '__all__'

    def get_buyer_comm_amount(self, obj):
        if obj.cost_for_sell:
            return round(float(obj.cost_for_sell) * 0.005, 2)
        return None

    def get_seller_comm_amount(self, obj):
        if obj.cost_for_sell:
            return round(float(obj.cost_for_sell) * float(obj.seller_commission_rate), 2)
        return None


class PotentialBuyerSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PotentialBuyer
        fields = '__all__'


class BuyerInterestSerializer(serializers.ModelSerializer):
    buyer_name    = serializers.SerializerMethodField()
    property_desc = serializers.CharField(source='property.description', read_only=True)
    comm_amount   = serializers.SerializerMethodField()

    class Meta:
        model  = BuyerInterest
        fields = ('buyer_id', 'property_id', 'buyer_name', 'property_desc',
                  'offer_amount', 'buyer_commission_rate', 'comm_amount',
                  'interest_date', 'notes')

    def get_buyer_name(self, obj):
        return f"{obj.buyer.First_name} {obj.buyer.last_name}"

    def get_comm_amount(self, obj):
        if obj.offer_amount and obj.buyer_commission_rate:
            return round(float(obj.offer_amount) * float(obj.buyer_commission_rate), 2)
        return None


class TransactionSerializer(serializers.ModelSerializer):
    buyer_name            = serializers.SerializerMethodField()
    seller_name           = serializers.SerializerMethodField()
    agent_name            = serializers.SerializerMethodField()
    property_desc         = serializers.CharField(source='property.description', read_only=True)
    property_city         = serializers.CharField(source='property.address.city', read_only=True)
    buyer_commission_amt  = serializers.SerializerMethodField()
    seller_commission_amt = serializers.SerializerMethodField()
    total_office_comm     = serializers.SerializerMethodField()
    agent_earnings        = serializers.SerializerMethodField()

    class Meta:
        model  = Transaction
        fields = ('transaction_id', 'property_id', 'property_desc', 'property_city',
                  'buyer_id', 'buyer_name', 'seller_id', 'seller_name',
                  'agent_id', 'agent_name', 'transaction_at', 'agreed_price',
                  'buyer_commission_rate', 'buyer_commission_amt',
                  'seller_commission_rate', 'seller_commission_amt',
                  'total_office_comm', 'agent_earnings',
                  'closing_date', 'comments')

    def get_buyer_name(self, obj):
        return f"{obj.buyer.first_name} {obj.buyer.last_name}"

    def get_seller_name(self, obj):
        return f"{obj.seller.first_name} {obj.seller.last_name}"

    def get_agent_name(self, obj):
        return f"{obj.agent.first_name} {obj.agent.last_name}"

    def get_buyer_commission_amt(self, obj):
        return round(float(obj.agreed_price) * float(obj.buyer_commission_rate), 2)

    def get_seller_commission_amt(self, obj):
        return round(float(obj.agreed_price) * float(obj.seller_commission_rate), 2)

    def get_total_office_comm(self, obj):
        return round(float(obj.agreed_price) *
                     (float(obj.buyer_commission_rate) + float(obj.seller_commission_rate)), 2)

    def get_agent_earnings(self, obj):
        return round(float(obj.agreed_price) *
                     (float(obj.buyer_commission_rate) + float(obj.seller_commission_rate)) *
                     float(obj.agent.commission), 2)
