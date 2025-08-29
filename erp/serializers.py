from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Department, Employee, Project

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role']
        read_only_fields = ['id']

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'budget']

class EmployeeSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    department_name = serializers.ReadOnlyField(source='department.name')

    class Meta:
        model = Employee
        fields = ['id', 'user', 'department', 'department_name', 'salary', 'job_title']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        password = user_data.pop('password', None)
        user = User.objects.create(**user_data)
        if password:
            user.set_password(password)
            user.save()
        employee = Employee.objects.create(user=user, **validated_data)
        return employee

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            for attr, value in user_data.items():
                if attr == 'password':
                    instance.user.set_password(value)
                else:
                    setattr(instance.user, attr, value)
            instance.user.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class ProjectSerializer(serializers.ModelSerializer):
    department_name = serializers.ReadOnlyField(source='department.name')
    employee_ids = serializers.PrimaryKeyRelatedField(
        source='employees', many=True, queryset=Employee.objects.all(), required=False
    )

    class Meta:
        model = Project
        fields = ['id', 'name', 'department', 'department_name', 'employee_ids', 'is_active', 'start_date', 'end_date']
