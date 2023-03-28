from rest_framework import serializers
from django_testing.settings import MAX_STUDENTS_PER_COURSE
from students.models import Course


class CourseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Course
        fields = ("id", "name", "students")
    def create(self, validated_data):

        return super().create(validated_data)
    
    def validate(self, data):
        method = self.context['request'].method
        len_students = len(data.get('students', []))

        if method == 'POST' and len_students > MAX_STUDENTS_PER_COURSE:
            raise serializers.ValidationError('Превышен лимит студентов курса')

        return data
