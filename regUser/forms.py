from django import forms

class PicForm(forms.Form):
    student_oid = forms.CharField(widget=forms.HiddenInput())
    type = forms.CharField(widget=forms.HiddenInput())
    teacher_oid = forms.CharField(widget=forms.HiddenInput())
    contractId = forms.CharField(widget=forms.HiddenInput())
    picFile = forms.ImageField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
