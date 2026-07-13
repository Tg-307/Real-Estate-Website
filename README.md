# UrbanRoots Homes -- Real Estate Management System

A full-stack **Real Estate Management System** built using **Django**,
**MySQL**, and **Django REST Framework**. The application provides a
secure, role-based platform for administrators, branch managers, and
field agents to manage properties, customers, transactions, and business
analytics through a modern web interface.

------------------------------------------------------------------------

## Features

### Role-Based Access Control (RBAC)

-   Admin, Manager, and Agent roles
-   View-level authorization
-   Session authentication and JWT-protected REST APIs

### Property Management

-   Create, update, and manage residential properties
-   Support for sale and rental listings
-   Address management and image support
-   Property availability tracking

### Customer & Buyer Management

-   Seller verification using Aadhaar
-   Potential buyer registration
-   Buyer interest tracking
-   Advanced search and filtering

### Transaction Management

-   Multi-step transaction workflow
-   Automatic customer resolution
-   Atomic database updates
-   Business rule validation
-   Automatic cleanup of buyer interest records

### Analytics & Dashboards

-   Agent performance analytics
-   Branch revenue analysis
-   Property statistics
-   Transaction history

------------------------------------------------------------------------

## Tech Stack

  Category         Technologies
  ---------------- -----------------------------------------
  Backend          Python, Django 4.2
  Database         MySQL 8.x
  API              Django REST Framework
  Authentication   Session Authentication, JWT
  Frontend         Django Templates, HTML, CSS, JavaScript

------------------------------------------------------------------------

## Architecture

-   Django integrated with an existing MySQL schema
-   ORM mapping without schema modification
-   Raw SQL used where composite primary keys required
-   REST APIs for programmatic access
-   Server-side validation for business constraints

------------------------------------------------------------------------

## Project Structure

``` text
├── real_estate_project/
├── website/
├── templates/
├── static/
├── api/
├── populate_data.sql
├── requirements.txt
└── manage.py
```

------------------------------------------------------------------------

## Installation

``` bash
git clone <repository-url>
cd UrbanRoots-Homes

python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### Configure Database

1.  Create a MySQL database.
2.  Update database credentials in `settings.py`.
3.  Import `populate_data.sql`.

Run the server:

``` bash
python manage.py runserver
```

Open:

``` text
http://127.0.0.1:8000/
```

------------------------------------------------------------------------

## Highlights

-   Enterprise-style RBAC architecture
-   Secure authentication
-   REST API integration
-   Transaction-safe workflows
-   Business rule enforcement
-   Analytics dashboards
-   Production-oriented database design

------------------------------------------------------------------------

## Future Improvements

-   Cloud deployment
-   Email notifications
-   Payment gateway integration
-   Elasticsearch-based property search
-   Docker support
-   CI/CD pipeline

------------------------------------------------------------------------

## Contributors

-   Tanishk Gupta
-   Parth Pande
-   Vidhi Garg
-   Praneet Sunkari

------------------------------------------------------------------------

## License

This project was developed as part of the **CS241 -- Database Management
Systems** course at **IIIT Guwahati**.
