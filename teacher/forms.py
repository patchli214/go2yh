from django import forms

class PicForm(forms.Form):
    tid = forms.CharField(widget=forms.HiddenInput())
    picFile = forms.ImageField()