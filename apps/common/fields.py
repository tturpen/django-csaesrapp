""""Create elicitation fields here."""
# Copyright (C) 2014 Taylor Turpen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from djangotoolbox.fields import SetField, ListField

from django import forms
from django.db import models

from apps.common.widgets import SetFieldWidget


class CseasrSetField(SetField):
    def formfield(self, **kwargs):
        return SetFieldForm(**kwargs)
    
class CseasrListField(ListField):
    def formfield(self,**kwargs):
        return models.Field.formfield(self, StringListField, **kwargs)
    
class SetFieldForm(forms.MultipleChoiceField):
    """Custom form field to display set field fields in models.
    """
    wiget = SetFieldWidget
    
    def clean(self,value):
        return value
    
class StringListField(forms.CharField):
    def prepare_value(self, value):
        return ', '.join(value)

    def to_python(self, value):
        if not value:
            return []
        return [item.strip() for item in value.split(',')]
    