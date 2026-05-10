"""
results/forms.py
Forms for result upload, manual entry, and filtering.
"""
from django import forms
from .models import Result, Subject, Batch


class ResultUploadForm(forms.Form):
    """CSV / Excel file upload form."""
    file = forms.FileField(
        label='Upload CSV or Excel file',
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls',
        }),
        help_text='Columns required: roll_number, subject_code, semester, batch_name, marks_obtained'
    )


class ResultFilterForm(forms.Form):
    """Smart filter form — all fields optional."""
    semester = forms.ChoiceField(
        required=False,
        choices=[('', 'All Semesters')] + [(i, f'Semester {i}') for i in range(1, 11)],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        required=False,
        empty_label='All Subjects',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    batch = forms.ModelChoiceField(
        queryset=Batch.objects.all(),
        required=False,
        empty_label='All Batches',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    grade = forms.ChoiceField(
        required=False,
        choices=[('', 'All Grades')] + Result.GRADE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )


class ManualResultForm(forms.ModelForm):
    """Faculty can add individual results manually."""
    class Meta:
        model  = Result
        fields = ['student', 'subject', 'batch', 'semester', 'marks_obtained', 'remarks']
        widgets = {
            'student':        forms.Select(attrs={'class': 'form-select'}),
            'subject':        forms.Select(attrs={'class': 'form-select'}),
            'batch':          forms.Select(attrs={'class': 'form-select'}),
            'semester':       forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'marks_obtained': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'remarks':        forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class SubjectForm(forms.ModelForm):
    class Meta:
        model  = Subject
        fields = ['name', 'code', 'department', 'semester', 'max_marks', 'pass_marks', 'credits']
        widgets = {f: forms.TextInput(attrs={'class': 'form-control'}) for f in
                   ['name', 'code', 'department']}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ['semester', 'max_marks', 'pass_marks', 'credits']:
            self.fields[f].widget.attrs.update({'class': 'form-control'})


class BatchForm(forms.ModelForm):
    class Meta:
        model  = Batch
        fields = ['name', 'department', 'start_year', 'end_year']
        widgets = {f: forms.TextInput(attrs={'class': 'form-control'}) for f in
                   ['name', 'department']}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ['start_year', 'end_year']:
            self.fields[f].widget.attrs.update({'class': 'form-control'})
