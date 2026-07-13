from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import (User, Branch, Employee, Customer, Address,
                     Property, PropertyImage, PotentialBuyer,
                     BuyerInterest, Transaction)


# ── User ────────────────────────────────────────────────────────────────
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display   = ('username', 'full_name', 'role', 'is_active', 'created_at')
    list_filter    = ('role', 'is_active')
    search_fields  = ('username', 'full_name')
    ordering       = ('role', 'username')
    fieldsets = (
        (None,           {'fields': ('username', 'password')}),
        ('Personal',     {'fields': ('full_name', 'role', 'employee')}),
        ('Permissions',  {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('username', 'full_name', 'role', 'employee', 'password1', 'password2')}),
    )


# ── Branch ──────────────────────────────────────────────────────────────
@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display  = ('branch_id', 'branch_name', 'city', 'state', 'phone', 'email')
    search_fields = ('branch_name', 'city')
    list_filter   = ('state',)


# ── Employee ────────────────────────────────────────────────────────────
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display  = ('employee_id', 'full_name', 'role', 'branch', 'base_salary',
                     'commission', 'Status', 'date_of_joining')
    list_filter   = ('role', 'Status', 'branch')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    ordering      = ('branch', 'role', 'first_name')

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


# ── Customer ────────────────────────────────────────────────────────────
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display  = ('customer_id', 'full_name', 'phone', 'email', 'role_type', 'city')
    list_filter   = ('role_type', 'state')
    search_fields = ('first_name', 'last_name', 'phone', 'email', 'Aadhar_no')

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


# ── Address ─────────────────────────────────────────────────────────────
@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display  = ('address_id', 'street_name', 'locality', 'city', 'state', 'pincode')
    search_fields = ('street_name', 'locality', 'city')
    list_filter   = ('city', 'state')


# ── Property Image inline ────────────────────────────────────────────────
class PropertyImageInline(admin.TabularInline):
    model  = PropertyImage
    extra  = 1
    fields = ('image_url', 'caption', 'is_primary')


# ── Property ────────────────────────────────────────────────────────────
@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display   = ('property_id', 'type', 'BHK', 'area', 'availability',
                      'cost_for_sell', 'Cost_for_rent', 'city_display',
                      'agent', 'time_of_listing')
    list_filter    = ('type', 'availability', 'address__city')
    search_fields  = ('description', 'address__street_name', 'address__city')
    readonly_fields = ('time_of_listing',)
    inlines        = [PropertyImageInline]
    ordering       = ('-time_of_listing',)

    def city_display(self, obj):
        return obj.address.city
    city_display.short_description = 'City'

    def commission_info(self, obj):
        return f"{float(obj.seller_commission_rate)*100:.1f}%"
    commission_info.short_description = 'Seller Comm.'


# ── Property Image ──────────────────────────────────────────────────────
@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display  = ('image_id', 'property', 'caption', 'is_primary', 'uploaded_at')
    list_filter   = ('is_primary',)

    def image_preview(self, obj):
        return format_html('<a href="{}" target="_blank">View</a>', obj.image_url)
    image_preview.short_description = 'Preview'


# ── Potential Buyer ─────────────────────────────────────────────────────
@admin.register(PotentialBuyer)
class PotentialBuyerAdmin(admin.ModelAdmin):
    list_display  = ('buyer_id', 'First_name', 'last_name', 'Contact_no',
                     'preferred_city', 'preferred_type', 'preferred_BHK',
                     'min_price', 'max_price', 'Choice', 'created_at')
    list_filter   = ('preferred_type', 'Choice', 'preferred_city')
    search_fields = ('First_name', 'last_name', 'Contact_no', 'preferred_city')


# ── Buyer Interest ──────────────────────────────────────────────────────
@admin.register(BuyerInterest)
class BuyerInterestAdmin(admin.ModelAdmin):
    list_display  = ('buyer', 'property', 'offer_amount',
                     'buyer_commission_rate', 'interest_date', 'notes')
    list_filter   = ('interest_date',)
    search_fields = ('buyer__First_name', 'buyer__last_name', 'property__description')


# ── Transaction ─────────────────────────────────────────────────────────
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display  = ('transaction_id', 'property', 'agreed_price',
                     'buyer_comm_display', 'seller_comm_display',
                     'office_comm_display', 'agent', 'closing_date')
    list_filter   = ('closing_date', 'agent__branch')
    search_fields = ('property__description', 'buyer__first_name', 'seller__first_name')
    readonly_fields = ('transaction_at',)
    ordering      = ('-closing_date',)

    def buyer_comm_display(self, obj):
        return f"₹{obj.buyer_commission_amount:,.0f}"
    buyer_comm_display.short_description = 'Buyer Comm.'

    def seller_comm_display(self, obj):
        return f"₹{obj.seller_commission_amount:,.0f}"
    seller_comm_display.short_description = 'Seller Comm.'

    def office_comm_display(self, obj):
        return f"₹{obj.total_office_commission:,.0f}"
    office_comm_display.short_description = 'Office Total'
