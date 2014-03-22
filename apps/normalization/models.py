from django.db import models
from djangotoolbox.fields import ListField, SetField

from apps.common.models import StateModel

class NormalizationMethod(StateModel):
    summary = models.TextField()
    func_names = SetField(models.TextField())
    
class NormalizedWords(StateModel):
    normalization_method = models.ForeignKey(NormalizationMethod)
    original_words = ListField(models.TextField())
    normalized_words = ListField(models.TextField())
    
