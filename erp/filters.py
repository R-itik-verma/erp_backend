import django_filters
from .models import Employee, Project

class EmployeeFilter(django_filters.FilterSet):
    min_salary = django_filters.NumberFilter(field_name='salary', lookup_expr='gte')
    max_salary = django_filters.NumberFilter(field_name='salary', lookup_expr='lte')
    department = django_filters.CharFilter(field_name='department__name', lookup_expr='icontains')

    class Meta:
        model = Employee
        fields = ['department', 'min_salary', 'max_salary', 'job_title']

class ProjectFilter(django_filters.FilterSet):
    department = django_filters.CharFilter(field_name='department__name', lookup_expr='icontains')
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = Project
        fields = ['department', 'is_active']
