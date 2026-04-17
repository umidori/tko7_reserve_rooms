from django import forms
from .models import Room


class RoomForm(forms.ModelForm):
    """会議室登録・編集フォーム（F-18）"""

    class Meta:
        model = Room
        fields = ['name', 'capacity', 'building', 'floor', 'is_active']
        labels = {
            'name':      '室名',
            'capacity':  '収容人数',
            'building':  '建物',
            'floor':     '階数',
            'is_active': '利用可能',
        }
        widgets = {
            'name':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例：第1会議室'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'building': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例：本館'}),
            'floor':    forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '例：3'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
        }

    def clean_capacity(self):
        capacity = self.cleaned_data.get('capacity')
        if capacity is not None and capacity < 1:
            raise forms.ValidationError('1以上の整数を入力してください')
        return capacity

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            return name
        # 編集時は自分自身を除いて重複チェック
        qs = Room.objects.filter(name=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('この室名はすでに使用されています')
        return name
