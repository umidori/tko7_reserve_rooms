from django import forms
from django.forms import CheckboxSelectMultiple

from reservations.models import Facility, Building


class RoomSearchForm(forms.Form):
    """F-08: 会議室絞り込み検索フォーム"""

    capacity = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(
            attrs={
                "class": "search-input",
                "placeholder": "10",
                "min": "1",
            }
        ),
    )

    facility = forms.ModelMultipleChoiceField(
        queryset=Facility.objects.all(),
        required=False,
        widget=CheckboxSelectMultiple,
    )

    building = forms.ModelChoiceField(
        queryset=Building.objects.all(),
        required=False,
        empty_label="（すべて）",
        widget=forms.Select(attrs={"class": "search-select"}),
    )

    floor = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "search-input",
                "min": "1",
            }
        ),
    )
