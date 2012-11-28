from django import forms
from tinymce.widgets import TinyMCE
from fields import ReCaptchaField


class BranchForm(forms.Form):
    text = forms.CharField(widget=TinyMCE(attrs={'cols': 80, 'rows': 15}),
                           max_length=1000)
    recaptcha = ReCaptchaField()
