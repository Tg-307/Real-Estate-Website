from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra):
        if not username:
            raise ValueError("Username required")
        user = self.model(username=username, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra):
        extra.setdefault('role', 'admin')
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [('admin','Administrator'),('manager','Manager'),('agent','Agent')]
    user_id     = models.AutoField(primary_key=True)
    username    = models.CharField(max_length=50, unique=True)
    full_name   = models.CharField(max_length=100)
    role        = models.CharField(max_length=10, choices=ROLE_CHOICES, default='agent')
    employee_fk = models.IntegerField(null=True, blank=True, db_column='employee_id')
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    USERNAME_FIELD  = 'username'
    REQUIRED_FIELDS = ['full_name']
    objects = UserManager()

    class Meta:
        db_table = 'auth_user_website'
        verbose_name = 'Website User'

    def __str__(self):
        return f"{self.full_name} ({self.role})"

    def get_employee(self):
        if self.employee_fk:
            try:
                return Employee.objects.get(pk=self.employee_fk)
            except Employee.DoesNotExist:
                return None
        return None

    @property
    def is_admin(self):   return self.role == 'admin'
    @property
    def is_manager(self): return self.role == 'manager'
    @property
    def is_agent(self):   return self.role == 'agent'


class Branch(models.Model):
    branch_id   = models.AutoField(primary_key=True)
    branch_name = models.CharField(max_length=100)
    phone       = models.CharField(max_length=20, null=True, blank=True)
    email       = models.CharField(max_length=100, null=True, blank=True)
    street      = models.CharField(max_length=150, null=True, blank=True)
    city        = models.CharField(max_length=80,  null=True, blank=True)
    state       = models.CharField(max_length=80,  null=True, blank=True)
    pincode     = models.CharField(max_length=10,  null=True, blank=True)
    manager_id  = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'branch'
        managed  = False

    def __str__(self):
        return f"{self.branch_name} ({self.city})"


class Employee(models.Model):
    GENDER_CHOICES = [('MALE','Male'),('FEMALE','Female'),('OTHERS','Others')]
    ROLE_CHOICES   = [('agent','Agent'),('manager','Manager')]

    employee_id     = models.AutoField(primary_key=True)
    first_name      = models.CharField(max_length=50)
    last_name       = models.CharField(max_length=50)
    gender          = models.CharField(max_length=10, choices=GENDER_CHOICES)
    phone           = models.CharField(max_length=20)
    alternate_phone = models.CharField(max_length=20, null=True, blank=True)
    email           = models.CharField(max_length=100, unique=True)
    Aadhar_no       = models.CharField(max_length=12,  unique=True)
    Apartment_no    = models.CharField(max_length=10,  null=True, blank=True)
    building        = models.CharField(max_length=50,  null=True, blank=True)
    street          = models.CharField(max_length=150, null=True, blank=True)
    city            = models.CharField(max_length=80,  null=True, blank=True)
    state           = models.CharField(max_length=80,  null=True, blank=True)
    pincode         = models.CharField(max_length=10,  null=True, blank=True)
    role            = models.CharField(max_length=10, choices=ROLE_CHOICES)
    base_salary     = models.DecimalField(max_digits=10, decimal_places=2)
    commission      = models.DecimalField(max_digits=4,  decimal_places=3, default=0.300)
    date_of_joining = models.DateField(null=True, blank=True)
    Status          = models.BooleanField(default=True)
    branch          = models.ForeignKey(Branch, on_delete=models.RESTRICT, db_column='branch_id')

    class Meta:
        db_table = 'employee'
        managed  = False

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


class Address(models.Model):
    address_id    = models.AutoField(primary_key=True)
    Apartment_no  = models.CharField(max_length=10,  null=True, blank=True)
    building      = models.CharField(max_length=50,  null=True, blank=True)
    street_number = models.CharField(max_length=20,  null=True, blank=True)
    street_name   = models.CharField(max_length=150)
    locality      = models.CharField(max_length=100, null=True, blank=True)
    city          = models.CharField(max_length=80)
    state         = models.CharField(max_length=80)
    pincode       = models.CharField(max_length=10)
    country       = models.CharField(max_length=60, default='India')

    class Meta:
        db_table = 'address'
        managed  = False

    def __str__(self):
        return f"{self.street_name}, {self.locality or ''}, {self.city}"


class Customer(models.Model):
    ROLE_CHOICES = [('buyer','Buyer'),('seller','Seller'),('both','Both')]

    customer_id     = models.AutoField(primary_key=True)
    first_name      = models.CharField(max_length=50)
    last_name       = models.CharField(max_length=50)
    phone           = models.CharField(max_length=20)
    alternate_phone = models.CharField(max_length=20, null=True, blank=True)
    email           = models.CharField(max_length=100, unique=True, null=True, blank=True)
    Aadhar_no       = models.CharField(max_length=12,  unique=True)
    apartment_no    = models.CharField(max_length=20,  null=True, blank=True)
    street          = models.CharField(max_length=150, null=True, blank=True)
    city            = models.CharField(max_length=80,  null=True, blank=True)
    state           = models.CharField(max_length=80,  null=True, blank=True)
    pincode         = models.CharField(max_length=10,  null=True, blank=True)
    role_type       = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')

    class Meta:
        db_table = 'customer'
        managed  = False

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role_type})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


class Property(models.Model):
    TYPE_CHOICES = [
        ('residential','Residential'),('commercial','Commercial'),
        ('land','Land'),('industrial','Industrial'),
    ]
    AVAIL_CHOICES = [
        ('Available','Available'),('Not Available','Not Available'),
        ('Sold','Sold'),('Rented','Rented'),
    ]
    property_id            = models.AutoField(primary_key=True)
    type                   = models.CharField(max_length=20, choices=TYPE_CHOICES)
    BHK                    = models.PositiveSmallIntegerField(null=True, blank=True)
    area                   = models.DecimalField(max_digits=10, decimal_places=2)
    CARPET_area            = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    Cost_for_rent          = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cost_for_sell          = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    Year_of_construction   = models.PositiveSmallIntegerField(null=True, blank=True)
    seller_commission_rate = models.DecimalField(max_digits=4,  decimal_places=3, default=0.030)
    availability           = models.CharField(max_length=15, choices=AVAIL_CHOICES, default='Available')
    description            = models.TextField(null=True, blank=True)
    time_of_listing        = models.DateTimeField(auto_now_add=True)
    address                = models.OneToOneField(Address, on_delete=models.RESTRICT, db_column='address_id')
    seller                 = models.ForeignKey(Customer, on_delete=models.RESTRICT, db_column='seller_id')
    agent                  = models.ForeignKey(Employee, on_delete=models.RESTRICT, db_column='agent_id')

    class Meta:
        db_table            = 'property'
        managed             = False
        ordering            = ['-time_of_listing']
        verbose_name_plural = 'Properties'

    def __str__(self):
        bhk = f"{self.BHK}BHK " if self.BHK else ""
        return f"{bhk}{self.type.title()} - {self.address.street_name}, {self.address.city}"

    def get_primary_image(self):
        img = self.images.filter(is_primary=True).first()
        return img.image_url if img else None


class PropertyImage(models.Model):
    image_id    = models.AutoField(primary_key=True)
    property    = models.ForeignKey(Property, on_delete=models.CASCADE,
                                    related_name='images', db_column='property_id')
    image_url   = models.CharField(max_length=500)
    caption     = models.CharField(max_length=200, null=True, blank=True)
    is_primary  = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'property_image'
        managed  = False

    def __str__(self):
        return f"Image for Property {self.property_id}"


class PotentialBuyer(models.Model):
    TYPE_CHOICES   = [('residential','Residential'),('commercial','Commercial'),
                      ('land','Land'),('industrial','Industrial')]
    CHOICE_CHOICES = [('Rent','Rent'),('Buy','Buy')]

    buyer_id        = models.AutoField(primary_key=True)
    First_name      = models.CharField(max_length=30)
    last_name       = models.CharField(max_length=30)
    Contact_no      = models.CharField(max_length=20)
    preferred_city  = models.CharField(max_length=20, null=True, blank=True)
    preferred_state = models.CharField(max_length=20, null=True, blank=True)
    preferred_type  = models.CharField(max_length=20, choices=TYPE_CHOICES, null=True, blank=True)
    preferred_BHK   = models.SmallIntegerField(null=True, blank=True)
    preferred_area  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_price       = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    max_price       = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    Choice          = models.CharField(max_length=4, choices=CHOICE_CHOICES, null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'potential_buyer'
        managed  = False

    def __str__(self):
        return f"{self.First_name} {self.last_name} ({self.Contact_no})"


class BuyerInterest(models.Model):
    # Real table uses composite PK (buyer_id, property_id)
    # We declare id=AutoField so Django ORM does not look for .id column
    # managed=False means Django never alters the table
    id                    = models.AutoField(primary_key=True)
    buyer                 = models.ForeignKey(PotentialBuyer, on_delete=models.CASCADE,
                                              db_column='buyer_id', related_name='interests')
    property              = models.ForeignKey(Property, on_delete=models.CASCADE,
                                              db_column='property_id', related_name='bids')
    offer_amount          = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    buyer_commission_rate = models.DecimalField(max_digits=4,  decimal_places=3, default=0.005)
    interest_date         = models.DateField(auto_now_add=True)
    notes                 = models.TextField(null=True, blank=True)

    class Meta:
        db_table        = 'buyer_interest'
        managed         = False
        unique_together = [('buyer', 'property')]

    def __str__(self):
        return f"{self.buyer} -> Property {self.property_id}"


class Transaction(models.Model):
    transaction_id         = models.AutoField(primary_key=True)
    property               = models.ForeignKey(Property, on_delete=models.RESTRICT,
                                               db_column='property_id')
    buyer                  = models.ForeignKey(Customer, on_delete=models.RESTRICT,
                                               db_column='buyer_id', related_name='purchases')
    seller                 = models.ForeignKey(Customer, on_delete=models.RESTRICT,
                                               db_column='seller_id', related_name='sales')
    agent                  = models.ForeignKey(Employee, on_delete=models.RESTRICT,
                                               db_column='agent_id')
    transaction_at         = models.DateTimeField(auto_now_add=True)
    agreed_price           = models.DecimalField(max_digits=14, decimal_places=2)
    buyer_commission_rate  = models.DecimalField(max_digits=4,  decimal_places=3, default=0.005)
    seller_commission_rate = models.DecimalField(max_digits=4,  decimal_places=3, default=0.030)
    closing_date           = models.DateField(null=True, blank=True)
    comments               = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'transaction'
        managed  = False
        ordering = ['-closing_date']

    def __str__(self):
        return f"Txn #{self.transaction_id}"

    def get_buyer_commission(self):
        return round(float(self.agreed_price) * float(self.buyer_commission_rate), 2)

    def get_seller_commission(self):
        return round(float(self.agreed_price) * float(self.seller_commission_rate), 2)

    def get_total_office_commission(self):
        return round(float(self.agreed_price) *
                     (float(self.buyer_commission_rate) + float(self.seller_commission_rate)), 2)
