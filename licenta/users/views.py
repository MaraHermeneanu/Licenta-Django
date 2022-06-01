
import base64
import json
import os
import pickle

import cv2
import face_recognition
import numpy as np
import PIL.ExifTags
import PIL.Image
from cv2 import CAP_PROP_FRAME_WIDTH
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordChangeView
from django.core.mail import BadHeaderError, send_mail
from django.http import (FileResponse, Http404, HttpResponse, JsonResponse,
                         StreamingHttpResponse)
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .forms import (FaceLoginForm, ImageUploadForm, ProfileUpdateForm,
                    StereoImageUploadForm, UserRegisterForm, UserUpdateForm)
from .models import (CameraParameters, ChessboardImage, StereoCameraParameters,
                     User)


class PasswordsChangeView(PasswordChangeView):
    form_class = PasswordChangeForm
    succes_url = reverse_lazy('password_success')


def password_reset_request(request):
    if request.method == "POST":
        
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():

            data = password_reset_form.cleaned_data['email']
            
            if User.objects.filter(email=data).exists():
                user = User.objects.get(email=data) #unique email for user
                
                subject = "Password Reset Requested"
                email_template_name = "password/password_reset_email.txt"

                content = {
                "email":user.email,
                'domain':'127.0.0.1:8000',
                'site_name': 'Rekon',
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "user": user,
                'token': default_token_generator.make_token(user),
                'protocol': 'http',
                }

                email = render_to_string(email_template_name, content)

                try:
                    send_mail(subject, email, settings.EMAIL_HOST_USER , [user.email], fail_silently=False)
                except BadHeaderError:
                    return HttpResponse('Invalid header found.')

                return redirect ("/password_reset/done/")
                
            else:
                messages.warning(request, f"There is no account with the email you provided. Please try again.")
                return redirect('password_reset')
                

    password_reset_form = PasswordResetForm()
    return render(request=request, template_name="password/password_reset.html", context={"password_reset_form":password_reset_form})


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)

        email = form['email'].value()
        username = form['username'].value()

        if User.objects.filter(username=username).exists():
            messages.warning(request, f"There is already an account with the username you provided.")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.warning(request, f"There is already an account with the email you provided.")
            return redirect('register')

        if form.is_valid():

            form.save() 
            messages.success(request, f'Your account has been created! You are now able to log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()

    context = {'form': form}
    return render(request, 'users/register.html', context)


def face_login(request): ##TODO check error handling here
    if request.method == 'POST':
        form = FaceLoginForm(request.POST)
        username=form['username'].value()

        #get the user with the unique username
        if not(User.objects.filter(username=username).exists()):
            messages.warning(request, f"There is no account with the username you provided.")
            return redirect('face_login')

        user=User.objects.get(username=username) #unique username
        #take photo 
        try:
            cam = cv2.VideoCapture(0) 
        except:
            messages.warning(request,f"There was an error while taking your photo. Make sure that your camera isn't already in use or shut.")
            return redirect('face_login')

        retval, img = cam.read()
        if retval:   #check if the reading was successful
            
            #get user's profile picture path
            profile=user.profile
            # print(type(profile.image))
            profile_image_path=profile.image.path
            # print(profile_image_path)

            #load the profile picture from specific location and encode
            profile_image = face_recognition.load_image_file(profile_image_path)

            try: 
                profile_face_encoding = face_recognition.face_encodings(profile_image)[0]

                #convert the webcam photo to rgb 
                img_rgb = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)

                #locate face in the webcam photo and encode
                face_locations = face_recognition.face_locations(img_rgb)
                face_encodings = face_recognition.face_encodings(img_rgb, face_locations)

                #compare the two images/faces
                
                check=face_recognition.compare_faces(profile_face_encoding, face_encodings)
            except:
                messages.info(request, f"Couldn't identify a face in one of the photos. Please try again and make sure that your face is showing in your profile picture.")
                return redirect('face_login')

            print(check)

            if check[0]:
                #the user can be authenticated
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, f'You have been successfully authenticated! ')
                return redirect('home')
                
            else:
                messages.warning(request, f"We couldn't verify your identity. Authentication failed.")
                return redirect('face_login')
                
        else:
            messages.warning(request,f"There was an error while taking your photo. Make sure that your camera isn't already in use or shut.")
            return redirect('face_login')
        
    else:
        form = FaceLoginForm()
        context = {'form': form}
        return render(request, 'users/face_login.html', context)


@login_required
def profile(request, username): ##TODO
    if (User.objects.filter(username = username).exists()):
        user = User.objects.filter(username = username)[0] #unique id 

        if (user == request.user): #render editable profile page 
            pass
        else: ##render display only profile page
            pass

        if request.method == 'POST':
            
            u_form = UserUpdateForm(request.POST, instance=user)
            p_form = ProfileUpdateForm(request.POST,
                                    request.FILES,
                                    instance=user.profile)
            if u_form.is_valid() and p_form.is_valid():
                u_form.save()
                p_form.save()
                messages.success(request, f'Your account has been updated!')
                return redirect('profile')

        else:
            u_form = UserUpdateForm(instance=user)
            p_form = ProfileUpdateForm(instance=user.profile)

        context = {
            'user': user,
            'u_form': u_form,
            'p_form': p_form
        }

        return render(request, 'users/profile.html', context)
    else:
        return render(request, "application/404.html")


@login_required
def password_change_done(request):
    return render(request, 'password/password_change_done.html',{})


CHESSBOARD_SIZE = (8,5)
COUNT_IMAGES_CHESSBOARD = 10

def list2string(array):
    listToStr = ' '.join([str(elem) for elem in array])

    return listToStr

@login_required
def camera_calibration(request): ##TODO error handling
    
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)

        #check if name/title already exists
        title = form['title'].value()
        if CameraParameters.objects.filter(name=title, user=request.user).exists():
            messages.warning(request, f"There is already a configuration with the title you provided. Retry")
            return redirect('camera_calibration')


        if form.is_valid():
            
            chessboardCaptured = 0

            #Define arrays to save detected points
            obj_points = [] #3D points in real world space 
            img_points = [] #3D points in image plane
            #Prepare grid and points to display
            objp = np.zeros((np.prod(CHESSBOARD_SIZE),3),dtype=np.float32)
            objp[:,:2] = np.mgrid[0:CHESSBOARD_SIZE[0], 0:CHESSBOARD_SIZE[1]].T.reshape(-1,2) * 0.03

            #termination criteria for subpixel accuracy
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

            focal_length = None
            First = True

            for img in request.FILES.getlist('images'):
                Image = ChessboardImage.objects.create(image=img)
                
                #verify the file extension - must be png or jpg
                extension = Image.image.path[-3:]
                if extension.lower() != 'png' and extension.lower() != 'jpg':
                    messages.warning(request, f'You must only upload .png or .jpg files. Please try again.')
                    return redirect('camera_calibration')


                current_image = cv2.imread(Image.image.path)

                ##TODO check shape

                if First:
                    exif_image = PIL.Image.open(Image.image.path)
                    exif = { PIL.ExifTags.TAGS[k]: v for k, v in exif_image._getexif().items() if k in PIL.ExifTags.TAGS }
                    focal_length = exif['FocalLength']
                    First = False

                gray_image = cv2.cvtColor(current_image, cv2.COLOR_BGR2GRAY)


                ret,corners = cv2.findChessboardCorners(gray_image, CHESSBOARD_SIZE, None)
                if ret == True:
                    print("Chessboard detected!") 
                    chessboardCaptured+=1

                    #refine corner location (to subpixel accuracy) based on criteria
                    cornersA = cv2.cornerSubPix(gray_image, corners, (11,11), (-1,-1), criteria) #winsize (5,5) ?
                    obj_points.append(objp) 
                    img_points.append(cornersA)

                else:
                    print("Chessboard not detected!")
                
                Image.delete()

            if chessboardCaptured < COUNT_IMAGES_CHESSBOARD:
                messages.warning(request, f'You must upload at least 20 images of the chessboard pattern.')
                return redirect('camera_calibration')
            else:
                messages.success(request, f'Images uploaded successfully.')

            
            #calibrate - obtain the camera parameters
            ret, K, dist, rvecs, tvecs = cv2.calibrateCamera(obj_points, img_points, gray_image.shape[::-1], None, None)
            print("RMS", ret)

            print("K",K)
            print("dist", dist)

            # print("rvecs",rvecs)
            # print("tvecs",tvecs) 

            print("FL",focal_length)


            #create camera parameters model
            CameraParameters.objects.create(name=title,user=request.user,K=base64.b64encode(pickle.dumps(K)),dist=base64.b64encode(pickle.dumps(dist)),focal_length=focal_length)
            messages.success(request,f'New camera configuration added!')
            
            CameraParamObjs = CameraParameters.objects.filter(user=request.user)

            for camera in CameraParamObjs:
                
                k = pickle.loads(base64.b64decode(camera.K))
                dist = pickle.loads(base64.b64decode(camera.dist))
                camera.K = list2string(k)
                camera.dist = list2string(dist)


            context={'form':form, 'CameraParamObjs':CameraParamObjs}
            return redirect('camera_calibration')
            

    form = ImageUploadForm()
    CameraParamObjs = CameraParameters.objects.filter(user=request.user) 

    for camera in CameraParamObjs:
        k = pickle.loads(base64.b64decode(camera.K))
        dist = pickle.loads(base64.b64decode(camera.dist))
        camera.K = str(k)
        # print("context K", list2string(k))
        camera.dist = str(dist)

    context={'form':form, 'CameraParamObjs':CameraParamObjs}

    return render(request, 'users/camera_calibration.html', context)

@login_required
def delete_camera_config(request):
    if request.method == 'POST':
        title = request.POST.get('select')
        cam_config = CameraParameters.objects.get(name=title, user=request.user)
        cam_config.delete()
        messages.success(request,f'Configuration deleted successfully!')
        return redirect('camera_calibration')
    return redirect('camera_calibration')


@login_required
def stereo_calibration(request): ##TODO error handling
    if request.method == 'POST':
        form = StereoImageUploadForm(request.user, request.POST, request.FILES)

        #check if name/title already exists
        title = form['title'].value()
        if StereoCameraParameters.objects.filter(name=title, user=request.user).exists():
            messages.warning(request, f"There is already a configuration with the title you provided. Retry.")
            return redirect('stereo_calibration')


        if form.is_valid():
            
            chessboardCaptured = 0

            #Define arrays to save detected points
            obj_points = [] #3D points in real world space 
            left_img_points = [] #3D points in image plane
            right_img_points = [] #3D points in image plane


            #Prepare grid and points to display
            objp = np.zeros((np.prod(CHESSBOARD_SIZE),3),dtype=np.float32)
            objp[:,:2] = np.mgrid[0:CHESSBOARD_SIZE[0], 0:CHESSBOARD_SIZE[1]].T.reshape(-1,2)

            #termination criteria for subpixel accuracy
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

            focal_length = None
            First = True

            ##TODO check no of imgs, check shape

            for img_left, img_right in zip(request.FILES.getlist('images_left'),request.FILES.getlist('images_right')) :
                ImageL = ChessboardImage.objects.create(image=img_left)
                ImageR = ChessboardImage.objects.create(image=img_right)
                
                #verify the file extension - must be png or jpg
                extensionL = ImageL.image.path[-3:]
                extensionR = ImageL.image.path[-3:]

                if (extensionL.lower() != 'png' and extensionL.lower() != 'jpg') or (extensionR.lower() != 'png' and extensionR.lower() != 'jpg'):
                    messages.warning(request, f'You must only upload .png or .jpg files. Please try again.')
                    return redirect('stereo_calibration')
                
                current_imageL = cv2.imread(ImageL.image.path)
                current_imageR = cv2.imread(ImageR.image.path)

                if First:
                    ##TODO error handling here
                    exif_image = PIL.Image.open(ImageL.image.path)
                    try:
                        exif = { PIL.ExifTags.TAGS[k]: v for k, v in exif_image._getexif().items() if k in PIL.ExifTags.TAGS }
                        focal_length = exif['FocalLength']
                    except:
                        focal_length = 0.0
                    
                    First = False

                gray_imageL = cv2.cvtColor(current_imageL, cv2.COLOR_BGR2GRAY)
                gray_imageR = cv2.cvtColor(current_imageR, cv2.COLOR_BGR2GRAY)


                retL,cornersL = cv2.findChessboardCorners(gray_imageL, CHESSBOARD_SIZE, None)
                retR,cornersR = cv2.findChessboardCorners(gray_imageR, CHESSBOARD_SIZE, None)

                if retL and retR:
                    print("Chessboard detected!") 
                    chessboardCaptured+=1

                    #refine corner location (to subpixel accuracy) based on criteria
                    cornersLA = cv2.cornerSubPix(gray_imageL, cornersL, (11,11), (-1,-1), criteria) #winsize (5,5) ?
                    cornersRA = cv2.cornerSubPix(gray_imageR, cornersR, (11,11), (-1,-1), criteria) #winsize (5,5) ?

                    obj_points.append(objp) 
                    left_img_points.append(cornersLA)
                    right_img_points.append(cornersRA)

                else:
                    print("Chessboard not detected!")
                
                ImageL.delete()
                ImageR.delete()


            if chessboardCaptured < COUNT_IMAGES_CHESSBOARD:
                messages.warning(request, f'You must upload at least 20 images of the chessboard pattern.')
                return redirect('stereo_calibration')
            else:
                messages.success(request, f'Images uploaded successfully.')


            camLConfigPk = form['left_camera_config'].value()
            camLConfigObj = CameraParameters.objects.get(pk=camLConfigPk)
            K1 = pickle.loads(base64.b64decode(camLConfigObj.K))
            D1 = pickle.loads(base64.b64decode(camLConfigObj.dist))

            camRConfigPk = form['right_camera_config'].value()
            camRConfigObj = CameraParameters.objects.get(pk=camRConfigPk)
            K2 = pickle.loads(base64.b64decode(camRConfigObj.K))
            D2 = pickle.loads(base64.b64decode(camRConfigObj.dist))

            aImageSize = gray_imageL.shape 


            nRMS, K1, D1, K2, D2, R, T, E, F = cv2.stereoCalibrate(obj_points, left_img_points, right_img_points, K1, D1, K2, D2, aImageSize, flags=cv2.CALIB_FIX_INTRINSIC | cv2.CALIB_SAME_FOCAL_LENGTH)
            print("Stereo calibration RMS: ", nRMS)
            R1, R2, P1, P2, Q, roiLeft, roiRigth = cv2.stereoRectify(K1, D1, K2, D2, aImageSize, R, T, flags=cv2.CALIB_ZERO_DISPARITY, alpha=0.0)\

            print("K1", K1)
            print("D1", D1)
            print("K2", K2)
            print("D2", D2)
            print("R", R)
            print("T", T)
            print("E", E)
            print("F", F)
            print("R1", R1)
            print("R2",R2)
            print("P1", P1)
            print("P2", P2)
            print("Q", Q)

            #create camera parameters model
            StereoCameraParameters.objects.create(name=title,user=request.user,
            K1=base64.b64encode(pickle.dumps(K1)),D1=base64.b64encode(pickle.dumps(D1)),
            K2=base64.b64encode(pickle.dumps(K2)),D2=base64.b64encode(pickle.dumps(D2)),
            R=base64.b64encode(pickle.dumps(R)),T=base64.b64encode(pickle.dumps(T)),
            E=base64.b64encode(pickle.dumps(E)),F=base64.b64encode(pickle.dumps(F)),
            R1=base64.b64encode(pickle.dumps(R1)),R2=base64.b64encode(pickle.dumps(R2)),
            P1=base64.b64encode(pickle.dumps(P1)),P2=base64.b64encode(pickle.dumps(P2)),
            Q=base64.b64encode(pickle.dumps(Q)),focal_length=focal_length)


            messages.success(request,f'New stereo camera configuration added!')
            
            StereoCameraParametersObjs = StereoCameraParameters.objects.filter(user=request.user)

            for camera in StereoCameraParametersObjs:
                
                k1 = pickle.loads(base64.b64decode(camera.K1))
                k2 = pickle.loads(base64.b64decode(camera.K2))
                d1 = pickle.loads(base64.b64decode(camera.D1))
                d2 = pickle.loads(base64.b64decode(camera.D2))
                q = pickle.loads(base64.b64decode(camera.Q))

                camera.K1 = str(k1)
                camera.D1 = str(d1)
                camera.K2 = str(k2)
                camera.D2 = str(d2)
                camera.Q = str(q)


            context={'form':form, 'StereoCameraParametersObjs':StereoCameraParametersObjs}
            return redirect('camera_calibration')


    ###GET       

    form = StereoImageUploadForm(user=request.user)
    StereoCameraParametersObjs = StereoCameraParameters.objects.filter(user=request.user) 

    for camera in StereoCameraParametersObjs:
        
        k1 = pickle.loads(base64.b64decode(camera.K1))
        k2 = pickle.loads(base64.b64decode(camera.K2))
        d1 = pickle.loads(base64.b64decode(camera.D1))
        d2 = pickle.loads(base64.b64decode(camera.D2))
        q = pickle.loads(base64.b64decode(camera.Q))

        camera.K1 = str(k1)
        camera.D1 = str(d1)
        camera.K2 = str(k2)
        camera.D2 = str(d2)
        camera.Q = str(q)

        # print(camera.K1)
        # print(camera.D1)
        # print(camera.K2)
        # print(camera.D2)


    context={'form':form, 'StereoCameraParametersObjs': StereoCameraParametersObjs}

    return render(request, 'users/stereo_calibration.html', context)


@login_required
def delete_stereo_config(request):
    if request.method == 'POST':
        title = request.POST.get('select')
        cam_config = StereoCameraParameters.objects.get(name=title, user=request.user)
        cam_config.delete()
        messages.success(request,f'Configuration deleted successfully!')
        return redirect('stereo_calibration')
    return redirect('stereo_calibration')



 


