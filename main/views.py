from django.shortcuts import render

from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

import streamlit as st

from .models import *
from .serializers import *
from .backend import *





class ResumeViewSet(viewsets.ModelViewSet) :
    queryset = Resume.objects.all()
    serializer_class = ResumeSerializer


    def list(self, request):
        queryset = Resume.objects.all()
        serializer = ResumeSerializer(queryset,many= True)
        # serializer = self.serializer_class
        return Response(
            {
                "data": serializer.data,
                "status" : "ok",
                "code" : 200,
                "message" : "All resume record",
            },
            status.HTTP_200_OK
        )


    def create(self, request):
        print(request.data)
        serializer_class = self.serializer_class
        serializer = serializer_class(data=request.data, context={'request' : request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "data": serializer.data,
                "status" : "ok",
                "code" : 200,
                "message" : "Successfully added resume record",
            },
            status.HTTP_200_OK
        )
        



class ResumeData(APIView):
    
           
    def post(self, request,format=None):
        data= request.FILES['file']
        print("ggg1",data.name)
        # print("ggg1",data.read())
        
        
        resume_segments, resume_lines = file_to_txt(
            data.read(),data.name
        )

        data = resume_details(resume_lines, resume_segments)
 
        return Response(
            {
                "data":data,
                "status" : "ok",
                "code" : 200,
                "message" : "resume detail record",
            },
            status.HTTP_200_OK
        )