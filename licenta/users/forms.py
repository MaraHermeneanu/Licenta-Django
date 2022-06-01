from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, CameraParameters


class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)

    username = forms.EmailField(widget=forms.TextInput(
        attrs={'class': 'form-control',
                'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            'class': 'form-control',
            'placeholder': 'Password'}
))

class FaceLoginForm(forms.Form):
    username = forms.CharField(label='Username')


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name','email', 'password1', 'password2']
    

class UserUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['username','email' ]


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image']

class ImageUploadForm(forms.Form):
    title = forms.CharField(label="Title")
    images = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))


class StereoImageUploadForm(forms.Form): ##TODO filter comboboxes
    title = forms.CharField(label="Title", widget=forms.TextInput(attrs={'placeholder': 'New configuration'}))
    images_left = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    images_right = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))

    left_camera_config = forms.ModelChoiceField(label='',queryset=CameraParameters.objects.all(), empty_label='Select Left Camera Configuration*', widget=forms.Select(attrs={'class':'form-select'}))
    right_camera_config = forms.ModelChoiceField(label='',queryset=CameraParameters.objects.all(), empty_label='Select Right Camera Configuration*', widget=forms.Select(attrs={'class':'form-select'}))

    def __init__(self,user, *args, **kwargs):
        super(StereoImageUploadForm, self).__init__(*args, **kwargs)
        if user is not None:
            self.fields['left_camera_config'].queryset = CameraParameters.objects.filter(user=user)
            self.fields['right_camera_config'].queryset = CameraParameters.objects.filter(user=user)







    