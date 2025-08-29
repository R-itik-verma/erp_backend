from collections import defaultdict
from decimal import Decimal
from django.db.models import Sum
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Department, Employee, Project, User
from .serializers import DepartmentSerializer, EmployeeSerializer, ProjectSerializer
from .permissions import IsAdmin, IsManager
from .filters import EmployeeFilter, ProjectFilter

import csv
from io import BytesIO
try:
    import openpyxl
except Exception:
    openpyxl = None

class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def is_admin(self):
        return self.request.user.role == User.Roles.ADMIN

    def is_manager(self):
        return self.request.user.role == User.Roles.MANAGER

    def manager_department(self):
        emp = getattr(self.request.user, 'employee_profile', None)
        return getattr(emp, 'department', None)

class DepartmentViewSet(BaseViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    search_fields = ['name']
    ordering_fields = ['name', 'budget']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdmin()]

class EmployeeViewSet(BaseViewSet):
    queryset = Employee.objects.select_related('user', 'department').all()
    serializer_class = EmployeeSerializer
    filterset_class = EmployeeFilter
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'job_title']
    ordering_fields = ['salary', 'user__username']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == User.Roles.ADMIN:
            return qs
        if user.role == User.Roles.MANAGER:
            dept = self.manager_department()
            if dept:
                return qs.filter(department=dept)
            return qs.none()
        # Employee: can see self only
        return qs.filter(user=user)

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Admin full; Manager limited to own department
            if self.is_admin():
                return [IsAuthenticated(), IsAdmin()]
            if self.is_manager():
                return [IsAuthenticated(), IsManager()]
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        # Managers can only create in their own department
        if self.is_manager():
            dept = self.manager_department()
            serializer.save(department=dept)
        else:
            serializer.save()

    def perform_update(self, serializer):
        if self.is_manager():
            dept = self.manager_department()
            serializer.save(department=dept)
        else:
            serializer.save()

class ProjectViewSet(BaseViewSet):
    queryset = Project.objects.select_related('department').prefetch_related('employees').all()
    serializer_class = ProjectSerializer
    filterset_class = ProjectFilter
    search_fields = ['name', 'department__name']
    ordering_fields = ['name', 'start_date', 'end_date']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == User.Roles.ADMIN:
            return qs
        if user.role == User.Roles.MANAGER:
            dept = self.manager_department()
            if dept:
                return qs.filter(department=dept)
            return qs.none()
        # Employee: projects where assigned
        emp = getattr(user, 'employee_profile', None)
        if emp:
            return qs.filter(employees=emp)
        return qs.none()

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            if self.is_admin():
                return [IsAuthenticated(), IsAdmin()]
            if self.is_manager():
                return [IsAuthenticated(), IsManager()]
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        if self.is_manager():
            dept = self.manager_department()
            serializer.save(department=dept)
        else:
            serializer.save()

    def perform_update(self, serializer):
        if self.is_manager():
            dept = self.manager_department()
            serializer.save(department=dept)
        else:
            serializer.save()

class ReportsViewSet(BaseViewSet):
    http_method_names = ['get']

    @action(detail=False, methods=['get'])
    def employees_by_department(self, request):
        data = []
        qs = Employee.objects.select_related('department', 'user')
        if self.is_manager():
            dept = self.manager_department()
            qs = qs.filter(department=dept)
        for emp in qs:
            data.append({
                'department': emp.department.name if emp.department else None,
                'employee': emp.user.get_full_name() or emp.user.username,
                'salary': str(emp.salary),
                'job_title': emp.job_title,
            })
        return Response(data)

    @action(detail=False, methods=['get'])
    def salary_cost_per_department(self, request):
        qs = Employee.objects.values('department__name').annotate(total_salary=Sum('salary')).order_by('department__name')
        if self.is_manager():
            dept = self.manager_department()
            qs = qs.filter(department__name=dept.name) if dept else qs.none()
        data = [{
            'department': row['department__name'],
            'total_salary': str(row['total_salary'] or Decimal('0')),
        } for row in qs]
        return Response(data)

    @action(detail=False, methods=['get'])
    def active_projects(self, request):
        qs = Project.objects.filter(is_active=True)
        if self.is_manager():
            dept = self.manager_department()
            qs = qs.filter(department=dept)
        data = [{
            'id': p.id,
            'name': p.name,
            'department': p.department.name,
            'start_date': p.start_date,
            'end_date': p.end_date,
        } for p in qs]
        return Response(data)

    # CSV/Excel Exports
    @action(detail=False, methods=['get'], url_path='export/employees.csv')
    def export_employees_csv(self, request):
        qs = Employee.objects.select_related('department', 'user')
        if self.is_manager():
            dept = self.manager_department()
            qs = qs.filter(department=dept)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="employees.csv"'
        writer = csv.writer(response)
        writer.writerow(['Employee', 'Department', 'Salary', 'Job Title'])
        for e in qs:
            writer.writerow([
                e.user.get_full_name() or e.user.username,
                e.department.name if e.department else '',
                e.salary,
                e.job_title,
            ])
        return response

    @action(detail=False, methods=['get'], url_path='export/salary.xlsx')
    def export_salary_excel(self, request):
        if openpyxl is None:
            return Response({'detail': 'openpyxl not installed on server.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        qs = Employee.objects.values('department__name').annotate(total_salary=Sum('salary')).order_by('department__name')
        if self.is_manager():
            dept = self.manager_department()
            qs = qs.filter(department__name=dept.name) if dept else qs.none()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Salary Cost'
        ws.append(['Department', 'Total Salary'])
        for row in qs:
            ws.append([row['department__name'], float(row['total_salary'] or 0)])
        bio = BytesIO()
        wb.save(bio)
        bio.seek(0)
        response = HttpResponse(bio.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="salary_cost_per_department.xlsx"'
        return response
