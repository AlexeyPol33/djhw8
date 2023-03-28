import pytest
from django.contrib.auth.models import User
from model_bakery import baker
from students.models import Student, Course
from rest_framework.test import APIClient
from urllib.parse import quote
from django.test import override_settings, modify_settings
from rest_framework import serializers
import django_testing.settings as settings

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def course_factory():
    def factory(**kwargs):
        return baker.make("Course",**kwargs)
    return factory

@pytest.fixture
def student_factory():
    def factory(**kwargs):
        return baker.make("Student",**kwargs)
    return factory

@pytest.mark.django_db
def test_course_retrieve(api_client,course_factory,student_factory):
    student = student_factory(name='TestStudent')
    course = course_factory(name='TestCourse', students=[student])
    
    
    response = api_client.get(f'/api/v1/courses/{course.id}/')

    
    assert response.status_code == 200

    assert response.data['id'] == course.id
    assert response.data['name'] == course.name
    assert sorted(response.data['students']) == sorted([student.id for student in course.students.all()])

@pytest.mark.django_db
def test_course_list(api_client, course_factory):
    course_factory(name='TestCourse1')
    course_factory(name='TestCourse2')
    course_factory(name='TestCourse3')

    response = api_client.get('/api/v1/courses/')
    
    assert response.status_code == 200
    
    assert len(response.data) == 3
    assert response.data[0]['name'] == 'TestCourse1'
    assert response.data[1]['name'] == 'TestCourse2'
    assert response.data[2]['name'] == 'TestCourse3'

@pytest.mark.django_db
def test_course_filter_id(api_client, course_factory):
    course_factory(id=1,name='TestCourse1')
    course_factory(id=2,name='TestCourse2')
    course_factory(id=3,name='TestCourse3')
    course_factory(id=4,name='TestCourse4')
    course_factory(id=5,name='TestCourse5')

    response = api_client.get('/api/v1/courses/')

    assert response.status_code == 200
    response_len = len(response.data)

    for i in range(1, response_len + 1):
        response_two = api_client.get(f'/api/v1/courses/?id={i}')
        if i <= 5:
            assert response_two.status_code == 200
            assert len(response_two.data) == 1
            assert response_two.data[0]['id'] == i
        else:
            assert response_two.status_code == 404

@pytest.mark.django_db
def test_course_filter_name(api_client,course_factory):
    names = ['TestCourse1','TestCourse2','TestCourse3','TestCourse4','TestCourse5']
    for name in names:
        course_factory(name=name)

    response = api_client.get('/api/v1/courses/')

    assert response.status_code == 200

    for name in names:
        response_two = api_client.get(f"/api/v1/courses/?name={quote(name)}")
        assert response_two.status_code == 200

        assert response_two.data[0]['name'] == name

    response = api_client.get(f"/api/v1/courses/?name={quote('TestCourse7')}")
    assert response.status_code == 200
    assert len(response.data) == 0

@pytest.mark.django_db
def test_course_post(api_client, student_factory):
    student_factory(id=1,name='TestStudent1')
    student_factory(id=2,name='TestStudent2')
    data = {'name': 'TestCourse1', 'students': [1, 2]}

    response = api_client.post('/api/v1/courses/', data=data, format='json')
    students = Course.objects.get(name='TestCourse1').students.all()

    assert response.status_code == 201
    assert Course.objects.get(name='TestCourse1').name == 'TestCourse1'
    assert students.count() == 2
    assert students.filter(name='TestStudent1').exists()
    assert students.filter(name='TestStudent2').exists()
 
@pytest.mark.django_db
def test_course_patch(api_client,course_factory,student_factory):
    student_factory(id=1,name='TestStudent1')
    course_factory(id=1,name='TestCourse1')
    data = {'name': 'UpdateCourse', 'students': [1]}

    response = api_client.patch('/api/v1/courses/1/',data=data,format='json')

    assert response.status_code == 200
    assert Course.objects.get(id=1).name == 'UpdateCourse'
    assert Course.objects.get(id=1).students.all().count() == 1
    assert list(Course.objects.get(id=1).students.all()) == [Student.objects.get(id=1)]

@pytest.mark.django_db
def test_course_delete(api_client,course_factory):
    course_factory(id=1,name='TestCourse1')
    response = api_client.delete('/api/v1/courses/1/')

    assert response.status_code == 204
    assert len(Course.objects.all()) == 0



from unittest.mock import patch

@pytest.mark.django_db
def test_course_max_students(api_client, student_factory):
    student_factory(id=1, name='TestStudent1')
    student_factory(id=2, name='TestStudent2')
    data = {'name': 'TestCourse1', 'students': [1, 2]}

    with patch('django_testing.settings.MAX_STUDENTS_PER_COURSE', 0):
        response = api_client.post('/api/v1/courses/', data=data, format='json')
    print (settings.MAX_STUDENTS_PER_COURSE)
    assert response.status_code == 400
    assert len(Course.objects.all()) == 0
