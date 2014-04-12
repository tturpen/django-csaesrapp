"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.conf import settings
from apps.elicitation.pipelines import ElicitationPipeline
import os

class SimpleTest(TestCase):
    def setUp(self):
        self.ep = ElicitationPipeline()
        
    def test_pipeline_enqueue_and_hit(self):
#        self.ep.enqueue_prompts_and_generate_hits()
        pass
        
    def test_pipeline_load(self):
        prompt_file_uri = settings.PROMPT_FILE
        #This takes a while
        self.ep.load_PromptSource_RawToList(prompt_file_uri)
        self.ep.enqueue_prompts_and_generate_hits()
        self.assertEquals(1,1)