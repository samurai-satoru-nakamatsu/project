from django import forms
from .models import Video

class VideoForm(forms.ModelForm):
    class Meta:
        model= Video
        fields= ["name", "videofile"]


class ContactForm1(forms.Form):
    subject = forms.CharField(max_length=100)
    sender = forms.EmailField()
    file = forms.FileField(widget=forms.FileInput(attrs={'accept': 'image/*'}))


class ContactForm2(forms.Form):
    message = forms.CharField(widget=forms.Textarea)
    file = forms.FileField(widget=forms.FileInput(attrs={'accept': 'image/*'}))

    def __init__(self, *args, **kwargs):
        step1_file = kwargs.pop('step1_file')
        super().__init__(*args, **kwargs)
        if step1_file:
            self.fields['file'].required = False