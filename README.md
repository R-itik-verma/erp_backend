# ERP Hiring Assignment (Backend – Django)

A simplified ERP backend built with **Django 5** and **Django REST Framework** supporting Departments, Employees, Projects, role-based access, reports, pagination/search, JWT auth, and CSV/Excel exports.

## Features
- Models: Department, Employee, Project
- Relationships: Employee → Department (FK), Project → Department (FK), Project ↔ Employees (M2M)
- CRUD for all entities via DRF ViewSets
- Role-based access: Admin (all), Manager (own dept), Employee (self & assigned projects)
- Reports:
  - Employees by department
  - Salary cost per department
  - Active projects list
- JWT auth (SimpleJWT)
- Pagination, search, ordering, filtering
- Export CSV (employees) and Excel (salary by department)

## Quick Start

```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py seed_data  # creates admin/manager/employee sample data
# Admin:    admin / admin123
# Manager:  manager1 / manager123
# Employee: employee1 / employee123
python manage.py runserver
```

## Auth
- Obtain token: `POST /api/token/` with `{ "username": "admin", "password": "admin123" }`
- Use `Authorization: Bearer <access>` header for all API requests.

## API Endpoints (key)
```
/api/departments/              (GET, POST)  [Admin create/update]
/api/departments/{id}/         (GET, PUT, PATCH, DELETE)

/api/employees/                (GET, POST)  [Admin; Manager limited to own dept]
/api/employees/{id}/           (GET, PUT, PATCH, DELETE)

/api/projects/                 (GET, POST)
/api/projects/{id}/            (GET, PUT, PATCH, DELETE)

/api/reports/employees_by_department/
/api/reports/salary_cost_per_department/
/api/reports/active_projects/

/api/reports/export/employees.csv/
/api/reports/export/salary.xlsx/
```

### Filtering & Search
- Employees: `?search=evan&min_salary=700000&department=Engineering&ordering=-salary`
- Projects: `?department=Engineering&is_active=true&search=ERP&ordering=name`

### Notes
- Managers must also have an `Employee` profile to tie them to a department; the seed command sets this up.
- In production, turn `DEBUG=False`, set `ALLOWED_HOSTS`, and configure a real DB.
