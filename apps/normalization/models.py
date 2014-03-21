from django.db import models
from djangotoolbox.fields import ListField, SetField

class NormalizationMethod(models.Model):
    summary = models.TextField()
    func_names = SetField(models.TextField())
    
class NormalizedWords(models.Model):
    normalization_method = models.ForeignKey(NormalizationMethod)
    original_words = ListField(models.TextField())
    normalized_words = ListField(models.TextField())
    
