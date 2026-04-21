from django import forms
from accounts.models import Department
from reservations.models import Building, Facility, Room, RoomFacility, DepartmentRoom


class RoomForm(forms.ModelForm):
    """会議室登録・編集フォーム（F-18）"""

    # ManyToManyField with through= は ModelForm が自動生成しないため手動定義
    facilities = forms.ModelMultipleChoiceField(
        queryset=Facility.objects.all().order_by('name'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='設備',
    )

    departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.all().order_by('name'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='所属別表示設定',
    )

    class Meta:
        model = Room
        # is_active は一覧の「利用停止/再開」ボタンで管理するためフォームに含めない
        fields = ['name', 'capacity', 'facilities', 'building', 'floor', 'departments']
        labels = {
            'name':     '室名',
            'capacity': '収容人数',
            'building': '建物',
            'floor':    '階数',
        }
        widgets = {
            'name':     forms.TextInput(attrs={'placeholder': 'ex: 104'}),
            'capacity': forms.NumberInput(attrs={'min': 1, 'placeholder': 'ex: 10'}),
            'building': forms.Select(),
            'floor':    forms.NumberInput(attrs={'placeholder': 'ex: 3'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['facilities'].initial = self.instance.facilities.all()
            self.fields['departments'].initial = self.instance.departments.all()
        self.fields['building'].empty_label = '---'

    def clean_capacity(self):
        capacity = self.cleaned_data.get('capacity')
        if capacity is not None and capacity < 1:
            raise forms.ValidationError('1以上の整数を入力してください')
        return capacity

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            return name
        qs = Room.objects.filter(name=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('この室名はすでに使用されています')
        return name

    def save(self, commit=True):
        room = super().save(commit=commit)
        if commit:
            RoomFacility.objects.filter(room=room).delete()
            for facility in self.cleaned_data.get('facilities', []):
                RoomFacility.objects.create(room=room, facility=facility)

            DepartmentRoom.objects.filter(room=room).delete()
            for dept in self.cleaned_data.get('departments', []):
                DepartmentRoom.objects.create(room=room, department=dept)
        return room
