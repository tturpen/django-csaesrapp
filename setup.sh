#!/bin/sh
#Manually install dependencies not handled by setuptools
#Comment and uncomment as needed, will try to install every time
#pip install git+https://github.com/django-nonrel/djangotoolbox/

#Automaticaly install dependencies handled by setuptools
python setup.py develop

#install application
pip install dist/csaesrapp-0.1.tar.gz

#Sync the database
python manage.py syncdb

#runserver
python manage.py runserver