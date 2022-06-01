from email.policy import default
from django import forms
from django.forms.models import ModelForm
from users.models import CameraParameters, StereoCameraParameters
from .models import ImagePair

class ImgPairUploadForm(ModelForm):
    title = forms.CharField(label='Title',widget=forms.TextInput(attrs={'placeholder': 'New project'}))
    stereo_camera_config = forms.ModelChoiceField(label='',queryset=StereoCameraParameters.objects.all(), empty_label='Select Stereo Camera Configuration*', widget=forms.Select(attrs={'class':'form-select'}))
    ##TODO set min max 
    window_size = forms.IntegerField(initial=3)
    min_disparity = forms.IntegerField(initial=-1)
    num_disparities = forms.IntegerField(initial=80)
    disp_max_diff = forms.IntegerField(initial=12)
    uniq_ratio = forms.IntegerField(initial=10)
    speckle_window_size = forms.IntegerField(initial=150)
    speckle_range = forms.IntegerField(initial=2)
    pre_filter_cap = forms.IntegerField(initial=63) 
    private = forms.BooleanField(required=False)

    def __init__(self,user, *args, **kwargs):
        super(ImgPairUploadForm, self).__init__(*args, **kwargs)
        if user is not None:
            self.fields['stereo_camera_config'].queryset = StereoCameraParameters.objects.filter(user=user) 

    class Meta:
        model = ImagePair
        fields = ['title', 'left_image', 'right_image', 'stereo_camera_config',
        'window_size','min_disparity','num_disparities','disp_max_diff','uniq_ratio','speckle_window_size','speckle_range','pre_filter_cap', 'private']