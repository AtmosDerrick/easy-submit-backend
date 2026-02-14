from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import random
import string
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .serializer import SchoolCreateSerializer, SchoolSerializer, DepartmentSerializer
from .models import School, Department
from django.shortcuts import get_object_or_404
from django.http import Http404



def generate_school_code():
    """Generate a unique school code in format: 3 letters, 4 numbers, 1 letter"""
    while True:
        letters_part = ''.join(random.choices(string.ascii_uppercase, k=3))
        numbers_part = ''.join(random.choices(string.digits, k=4))
        final_letter = random.choice(string.ascii_uppercase)
        school_code = f"{letters_part}{numbers_part}{final_letter}"
        
        if not School.objects.filter(school_code=school_code).exists():
            return school_code

@api_view(['POST'])
def createSchool(request):
    user = request.user

    print(user, "user")
    try:
        user = request.user

        print(user, "user")
        if not user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        school_code = generate_school_code()
        request.data['school_code'] = school_code
        
        serializer = SchoolCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        newSchool = serializer.save(created_by=user)
        
        return Response({
            "message": "School created successfully",
            "school_code": school_code,
            "created_by": user.id,
            "school": SchoolCreateSerializer(newSchool).data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            "detail": "An error occurred while creating the school.",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_schools(request):
    try:
        all_schools = School.objects.all().order_by('name')
        
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 10)
        
        try:
            page_size = int(page_size)
        except ValueError:
            page_size = 10  
        
        if page_size < 1 or page_size > 100:
            page_size = 10  
        
        paginator = Paginator(all_schools, page_size)
        
        try:
            page_obj = paginator.page(int(page))
        except (PageNotAnInteger, ValueError):
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        serializer = SchoolSerializer(page_obj.object_list, many=True)
        
        return Response({
            "message": "Schools retrieved successfully",
            "total_schools": paginator.count,
            "total_pages": paginator.num_pages,
            "current_page": page_obj.number,
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous(),
            "next_page_number": page_obj.next_page_number() if page_obj.has_next() else None,
            "previous_page_number": page_obj.previous_page_number() if page_obj.has_previous() else None,
            "page_size": page_size,
            "schools": serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        
        return Response({
            "detail": "An error occurred while retrieving schools.",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def school(request, school_id):
    if not school_id:
        return Response({
            "detail": "School ID is required. Please provide 'school_id' parameter."
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        school = get_object_or_404(School, id=school_id)
        serializer = SchoolSerializer(school)
        
        return Response({
            "message": "School retrieved successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
        
    except Http404:
        return Response({
            "detail": "No school found with the provided ID"
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        return Response({
            "detail": "An error occurred while retrieving school",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def create_department(request):
    try:
        user = request.user
        user = request.user
        if not user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        serializer = DepartmentSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        new_department = serializer.save(created_by=user)

        return Response({
            "message":"Department created successfully",
            "created_by": user.id,
            "department":DepartmentSerializer(new_department).data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            "detail": "An error occurred while creating the department.",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET'])
def department(request, department_id):
    if not department_id:
        return Response({
                "detail": "School ID is required. Please provide 'school_id' parameter."
            }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        department = get_object_or_404(Department, id=department_id)
        serializer = SchoolSerializer(department)
        return Response({
            "message" : "School retrieved successfully",
            "data": serializer.data

        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({"details":"An error occured while retrieving school","error":str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    



    


