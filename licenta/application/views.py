import base64
import datetime
from doctest import FAIL_FAST
import os
import pickle

import cv2
import magic
import numpy as np
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.core.mail import BadHeaderError, send_mail
from django.http import Http404, HttpResponse, FileResponse
from django.http.response import JsonResponse
from django.shortcuts import redirect, render
from users.models import  StereoCameraParameters

from .forms import ImgPairUploadForm
from .models import ImagePair, Project


def home(request):
    return render(request, 'application/home.html')

def about(request):
    return render(request, 'application/about.html')

def dashboard(request):
    ProjectsObjs = Project.objects.filter(private=False)
    context = {'ProjectsObjs': ProjectsObjs}
    return render(request, 'application/dashboard.html', context)

@login_required
##TODO
def projects(request):
    if request.method == 'POST':
        form = ImgPairUploadForm(request.user,request.POST, request.FILES)
        
        if form.is_valid():
            #get title
            title = form['title'].value()
            print(title)

            #create ImagePair object with the two images
            ImgPair = ImagePair.objects.create(left_image=request.FILES.getlist('left_image')[0], right_image=request.FILES.getlist('right_image')[0])
            
            leftImgPath = ImgPair.left_image.path
            rightImgPath = ImgPair.right_image.path

            #check file extension - must be jpg/png
            leftExtension = leftImgPath[-3:]
            rightExtension = rightImgPath[-3:]
            if (leftExtension.lower() != 'png' and leftExtension.lower() != 'jpg') or (rightExtension.lower() != 'png' and rightExtension.lower() != 'jpg'):
                messages.warning(request, f'You must only upload .png or .jpg files. Please try again.')
                return redirect('projects')
            
            #load images
            leftImg = cv2.imread(leftImgPath)
            rightImg = cv2.imread(rightImgPath)


            #check image dimensions - must be the same
            if leftImg.shape != rightImg.shape:
                messages.warning(request, f'The images must have the same dimensions. Please try again.')
                return redirect('projects')


            h,w=leftImg.shape[:2]

            # Convert images to grayscale
            gray_image_left = cv2.cvtColor(leftImg, cv2.COLOR_BGR2GRAY)
            gray_image_right = cv2.cvtColor(rightImg, cv2.COLOR_BGR2GRAY)

            # SGBM parameters 

            oLeftMatcher = cv2.StereoSGBM_create(
                minDisparity= int(form['min_disparity'].value()),
                numDisparities= int(form['num_disparities'].value()),  # max_disp has to be dividable by 16 f. E. HH 192, 256
                blockSize= int(form['window_size'].value()),
                P1=8 * 3 * int(form['window_size'].value())**2,
                P2=32 * 3 * int(form['window_size'].value())**2,
                disp12MaxDiff= int(form['disp_max_diff'].value()),
                uniquenessRatio= int(form['uniq_ratio'].value()),
                speckleWindowSize= int(form['speckle_window_size'].value()),
                speckleRange= int(form['speckle_range'].value()),
                preFilterCap= int(form['pre_filter_cap'].value()),
                mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY
            )
            
            disparity_map = oLeftMatcher.compute(gray_image_left, gray_image_right)
            disparity = cv2.normalize(src=disparity_map, dst=disparity_map, beta=0, alpha=255, norm_type=cv2.NORM_MINMAX);
            disparity = np.uint8(disparity)

            image_path = "media/disparity_pics/" + request.user.username + "-" + title  + ".jpg"
            cv2.imwrite(image_path, disparity)
            

            #get camera parameters
            camConfigPk = form['stereo_camera_config'].value()
            camConfigObj = StereoCameraParameters.objects.get(pk=camConfigPk)
            print(camConfigObj.name) 
            q = camConfigObj.Q
            print(q)
            Q = pickle.loads(base64.b64decode(q))

            ##TODO overwrite Q

            colors = cv2.imread(leftImgPath, cv2.COLOR_RGB2BGR)
            colors = cv2.cvtColor(colors, cv2.COLOR_RGB2BGR)
    
            mask = disparity > disparity.min()

            aReprojectedPoints = cv2.reprojectImageTo3D(disparity, Q)  

            final_points = aReprojectedPoints[mask]
            final_colors = colors[mask]

            path = "media/ply_models/" + request.user.username + "-" + title  + ".ply"
            final_colors = final_colors.reshape(-1,3)
            final_points = np.hstack([final_points.reshape(-1,3), final_colors])

            sPLYHeader = '''ply
                format ascii 1.0
                element vertex %(nVertices)d
                property float x
                property float y
                property float z
                property uchar red
                property uchar green
                property uchar blue
                end_header
                '''
            with open(path, 'w') as file:
                file.write(sPLYHeader %dict(nVertices=len(final_points)))
                np.savetxt(file, final_points, '%f %f %f %d %d %d')
            

            private = form['private'].value()
            ##Create Projects model/object
            project = Project.objects.create(name=title, user=request.user, private=private, date=datetime.datetime.now())
            project.disparity = "/disparity_pics/" + request.user.username + "-" + title  + ".jpg"
            project.file = "/ply_models/" + request.user.username + "-" + title  + ".ply"
            project.save()

            messages.success(request,f'New project added!')

            form = ImgPairUploadForm(user=request.user)
            ProjectsObjs = Project.objects.filter(user=request.user) 
            context = {'form':form, 'ProjectsObjs': ProjectsObjs}
            return render(request,'application/projects.html', context)
            


    form = ImgPairUploadForm(user=request.user)
    ProjectsObjs = Project.objects.filter(user=request.user) 
    context = {'form':form, 'ProjectsObjs': ProjectsObjs}
    return render(request,'application/projects.html', context)


@login_required
def delete_project(request): 
    if request.method == 'POST':
        title = request.POST.get('select')
        project = Project.objects.get(name=title, user=request.user)
        project.delete()
        messages.success(request,f'Project deleted successfully!')
        return redirect('projects')
    return redirect('projects')


def search_project(request):
    if request.method == 'POST':
        searched = request.POST['searched']
        ProjectsObjs = Project.objects.filter(name__contains=searched, private=False)
        context = {'ProjectsObjs': ProjectsObjs}
        return render(request, 'application/dashboard.html', context)
    return redirect('dashboard')
    

##TODO
def download_ply(request):
    try:
        file = request.GET.get('file', None)
        contents = bytes(file)
        response = HttpResponse(contents)
        response['content_type'] = "application/octet-stream"
        response['Content-Disposition'] = 'attachment; filename=model.ply'
        return response
    except Exception:
        raise Http404


def send_message(request):
    name = request.GET.get('name', None)
    email = request.GET.get('email', None)
    message = request.GET.get('message', None)

    subject = "Message from " + name + " (" + email + " )"
    
    try:
        send_mail(subject, message, settings.EMAIL_HOST_USER, ["hermeneanu.mara@gmail.com"], fail_silently=False)       
    except BadHeaderError:
        data = {"sent":  False}
        return JsonResponse(data)

    data = {"sent":  True}
    return JsonResponse(data)


def not_found(request, exception):
    return render(request, "application/404.html")
