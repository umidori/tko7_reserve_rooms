from django import forms
from django.core.exceptions import ValidationError
from .models import Room, Reservation
from datetime import datetime, timedelta


def time_choices():
    choices = []
    current = datetime.strptime("00:00", "%H:%M")
    end = datetime.strptime("23:30", "%H:%M")

    while current <= end:
        value = current.strftime("%H:%M")
        label = f"{current.hour}:{current.strftime('%M')}"
        choices.append((value, label))
        current += timedelta(minutes=30)

    return choices


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

class ReservationForm(forms.ModelForm):
    reserve_date = forms.DateField(
        label='日付',
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control',
            }
        ),
    )

    start_time = forms.ChoiceField(
        label='開始時刻',
        choices=time_choices(),
        widget=forms.Select(
            attrs={
                'class': 'form-select',
            }
        ),
    )

    end_time = forms.ChoiceField(
        label='終了時刻',
        choices=time_choices(),
        widget=forms.Select(
            attrs={
                'class': 'form-select',
            }
        ),
    )

    class Meta:
        model = Reservation
        fields = [
            'room',
            'title',
            'participants',
            'notes',
        ]

        widgets = {
            'room': forms.Select(attrs={
                'class': 'form-select',
                'id': 'roomSelect',
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'participants': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['reserve_date'].initial = self.instance.start_at.date()
            self.fields['start_time'].initial = self.instance.start_at.strftime('%H:%M')
            self.fields['end_time'].initial = self.instance.end_at.strftime('%H:%M')
        else:
            start_at = self.initial.get('start_at')
            end_at = self.initial.get('end_at')

            if start_at:
                self.fields['reserve_date'].initial = start_at.date()
                self.fields['start_time'].initial = start_at.strftime('%H:%M')

            if end_at:
                self.fields['end_time'].initial = end_at.strftime('%H:%M')

    def clean(self):
        cleaned_data = super().clean()

        room = cleaned_data.get('room')
        reserve_date = cleaned_data.get('reserve_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if not reserve_date or not start_time or not end_time:
            return cleaned_data

        start = datetime.strptime(
            f'{reserve_date} {start_time}',
            '%Y-%m-%d %H:%M'
        )
        end = datetime.strptime(
            f'{reserve_date} {end_time}',
            '%Y-%m-%d %H:%M'
        )

        cleaned_data['start_at'] = start
        cleaned_data['end_at'] = end

        if start >= end:
            raise ValidationError("終了時刻は開始時刻より後にしてください")

        if room:
            exists = Reservation.objects.filter(
                room=room,
                is_cancelled=False,
                start_at__lt=end,
                end_at__gt=start,
            )

            if self.instance.pk:
                exists = exists.exclude(pk=self.instance.pk)

            if exists.exists():
                raise ValidationError("その時間帯は既に予約されています")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.start_at = self.cleaned_data['start_at']
        instance.end_at = self.cleaned_data['end_at']

        if commit:
            instance.save()

        return instance