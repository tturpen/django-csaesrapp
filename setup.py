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
import os
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__),'README.md')).read()

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__),os.pardir)))

setup(
      name='csaesrapp',
      version='0.1',
      packages=['csaesrapp'],
      include_package_data=True,
      license='BSD 2-clause License',
      description='An app for submitting elicitation hits via Amazon Mechanical Turk',
      long_description=README,
      url='https://github.com/tturpen/django-csaesrapp',
      author='taylor turpen',
      author_email='taylor.turpen@gmail.com',
      install_requires=['pymongo'],
      classifiers=[
                    'Environment :: Web Environment',
                    'Framework :: Django',
                    'Intended Audience :: Developers',
                    'License :: OSI Approved :: BSD License', # example license
                    'Operating System :: OS Independent',
                    'Programming Language :: Python',
                    'Programming Language :: Python :: 2.6',
                    'Programming Language :: Python :: 2.7',
                    'Topic :: Internet :: WWW/HTTP',
                    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        ],      
      )