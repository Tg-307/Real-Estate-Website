from django.urls import path
from . import views

urlpatterns = [
    path('',                              views.landing,                       name='landing'),
    path('login/',                        views.login_view,                    name='login'),
    path('logout/',                       views.logout_view,                   name='logout'),
    path('dashboard/',                    views.dashboard,                     name='dashboard'),

    # Admin
    path('dashboard/admin/',              views.admin_dashboard,               name='admin_dashboard'),
    path('dashboard/admin/add-manager/',  views.admin_add_manager,             name='admin_add_manager'),
    path('dashboard/admin/users/',        views.admin_users,                   name='admin_users'),
    path('dashboard/admin/users/<int:uid>/toggle/', views.admin_toggle_user,   name='admin_toggle_user'),

    # Manager
    path('dashboard/manager/',            views.manager_dashboard,             name='manager_dashboard'),
    path('dashboard/manager/add-agent/',  views.manager_add_agent,             name='manager_add_agent'),
    path('dashboard/manager/deactivate-agent/<int:agent_id>/', views.manager_deactivate_agent, name='manager_deactivate_agent'),
    path('dashboard/manager/reassign-properties/', views.manager_reassign_properties, name='manager_reassign_properties'),
    path('dashboard/manager/branch-analysis/', views.branch_analysis,          name='branch_analysis'),
    path('dashboard/manager/agent-analysis/', views.manager_agent_analysis,    name='manager_agent_analysis'),
    path('dashboard/manager/transaction/<int:txn_id>/', views.transaction_detail, name='transaction_detail'),

    # Agent
    path('dashboard/agent/',              views.agent_dashboard,               name='agent_dashboard'),
    path('dashboard/agent/add-buyer/',    views.agent_add_buyer,               name='agent_add_buyer'),
    path('dashboard/agent/add-property/', views.agent_add_property,            name='agent_add_property'),
    path('dashboard/agent/potential-buyers/', views.potential_buyers_list,     name='potential_buyers_list'),

    # Shared / Properties
    path('properties/',                   views.property_search,               name='property_search'),
    path('properties/<int:pk>/',          views.property_detail,               name='property_detail'),
    path('properties/<int:prop_id>/bid/', views.agent_add_bid,                 name='agent_add_bid'),
    path('properties/<int:prop_id>/transaction/', views.agent_create_transaction, name='agent_create_transaction'),
    path('properties/<int:prop_id>/availability/', views.agent_update_availability, name='agent_update_availability'),
    path('analytics/',                    views.agent_analytics,               name='agent_analytics'),

    # Update interfaces
    path('profile/update/',               views.update_employee_profile,       name='update_employee_profile'),
    path('properties/<int:prop_id>/edit/', views.update_property,               name='update_property'),

    # AJAX helpers
    path('ajax/check-aadhar/',            views.ajax_check_aadhar,             name='ajax_check_aadhar'),
    path('ajax/seller-lookup/',           views.ajax_seller_lookup,            name='ajax_seller_lookup'),
]
