"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

#     def test_cer_wer(self):
#         ref = ["Humpty","dumpty","broke","his","head."]
#         hyp = ["Humpty","dumpty","broke","his","nose",""]#"on","the","sidewalk","by","the","church."]
#         
#         ref2 = ['is', "lockwood's", 'destination', 'the', 'same', 'as', 'the', "mcclusky's"]
#         hyp2 = ['is', 'lockwoods', 'destination', 'the', 'same', 'as', 'the', 'macloskeys']
#         
#         hyp3 = ['list', 'confidences', 'threats.']
#         ref3 = ['list', "confidence's", 'threats']
#         
#         print(cer_wer(ref2,hyp2))
#         print(wer(ref,hyp))