"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from apps.elicitation.pipelines import ElicitationPipeline

class SimpleTest(TestCase):
    def test_pipeline_load(self):
        ep = ElicitationPipeline()
        prompt_file_uri = "/home/taylor/workspace_csaesrengine/csaesrapp/resources/rm1partialprompts.snr"
        #This takes a while
        ep.load_PromptSource_RawToList(prompt_file_uri)
        self.assertEquals(1,1)
