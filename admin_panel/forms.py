from django import forms
from accounts.models import Department
from reservations.models import Building, Facility, Room, RoomFacility, DepartmentRoom


class RoomForm(forms.ModelForm):
    """会議室登録・編集フォーム（F-18）"""

    # ── 設備（T-06 room_facilities 経由の M2N）──────────────────
    # ManyToManyField with through= は ModelForm が自動生成しないため手動定義する
    facilities = forms.ModelMultipleChoiceField(
        queryset=Facility.objects.all().order_by('name'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='設備',
    )

    # ── 所属別表示設定（T-07 department_rooms 経由の M2N）─────────
    departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.all().order_by('name'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='所属別表示設定',
    )

    class Meta:
        model = Room
        # facilities / departments は through= M2N なので Meta.fields には含めない
        fields = ['name', 'capacity', 'facilities', 'building', 'floor', 'departments', 'is_active']
        labels = {
            'name':      '室名',
            'capacity':  '収容人数',
            'building':  '建物',
            'floor':     '階数',
            'is_active': '利用可能',
        }
        widgets = {
            'name':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例：第1会議室'}),
            'capacity':  forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'building':  forms.Select(attrs={'class': 'form-control'}),
            'floor':     forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '例：3'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 編集時：既存の設備・所属別表示設定を初期選択状態にする
        if self.instance.pk:
            self.fields['facilities'].initial = self.instance.facilities.all()
            self.fields['departments'].initial = self.instance.departments.all()
        # building の空選択ラベルを設定
        self.fields['building'].empty_label = '（未設定）'

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

    def save(self, commit=True):
        room = super().save(commit=commit)
        if commit:
            # ── 設備の更新（既存レコードを入れ替え）──────────────
            RoomFacility.objects.filter(room=room).delete()
            for facility in self.cleaned_data.get('facilities', []):
                RoomFacility.objects.create(room=room, facility=facility)

            # ── 所属別表示設定の更新（既存レコードを入れ替え）──────
            DepartmentRoom.objects.filter(room=room).delete()
            for dept in self.cleaned_data.get('departments', []):
                DepartmentRoom.objects.create(room=room, department=dept)
        return room
