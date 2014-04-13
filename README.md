### Dependencies
- [Nose](https://pypi.python.org/pypi/django-nose)
- [boto](https://github.com/boto/boto )
- [pymongo](http://api.mongodb.org/python/current/installation.html)
- sph2pipe ([I got it here](https://github.com/foundintranslation/Kaldi/blob/master/tools/sph2pipe_v2.5/sph2pipe))
- [Django-nonrel](https://github.com/django-nonrel/django/tree/nonrel-1.3) For use with mongodb, You will need to install this manually:
 - pip install git+https://github.com/django-nonrel/django
- [MongoDB](http://docs.mongodb.org/manual/tutorial/install-mongodb-on-ubuntu/)
 

### Motivations
- Why use django
  * Django is a web-ready, well documented, object oriented, pure python programming environment with a database backend. It is literally perfect for MTurk projects.
- How is Django web-ready?
  * The Django server environment runs out of the box, meaning you can be visualizing and managing your data via a web-browser in minutes.
- Why use a database backend
  * Backups for your data not only preserver the state of your data, but also the relations between them.
- Why use MongoDB
  * As a non-relational database MongoDB has great support for strings of arbitrary lengths, which makes it ideal for natural language processing.

### Relevant Settings Values
- See csaesrapp.settings
* DATABASES
  - I suggest a dev and production version of your database
  - Set the database name```python
        DATABASES = {
            'default': {
                'ENGINE': 'django_mongodb_engine',
                'TEST_NAME': 'cseasr_app_test_db',
                'NAME' : 'dev_csaesrapp'
            }
        } 
    ```
  - When you are ready to submit actual HITs, change the database name to something like production_csaesrapp

- TEST_NAME is the name of the temporary database created by the Nose testrunner
- RECORDING_DIR the directory you want to record all the elicitations

- MTURK_HOST
  - The two possible values are mechanicalturk.amazonaws.com and mechanicalturk.sandbox.amazonaws.com
  - For development use the sandbox, for production use the other one

### Requirements Before Starting Csaesrapp for the first time
* A running instance of mongodb```$mongod --dbpath ~/whatever --bind_ip 127.0.0.1```

### Environment Variables
- Make sure you have the bash environment variables AWS_ACCESS_KEY_ID and AWS_ACCESS_KEY
- In settings.py make sure all os.environ['whatever'] variables are defined in your bash environment

### Starting Up Your Csaesrapp Installation for the first time
* In the root directory, 
 * $python manage.py syncdb
 * You will be prompted to create an admin user and password. Don't worry, django isn't externally accessible out of the box so the admin user is a formality.
* In the root directory,
 * $python manage.py runserver

### Running Csaesrapp Administration
* In a web browser navigate to localhost:8000/admin
* If you completed all the previous steps, you should be prompted to input your admin user credentials

### Steps to Create Elicitation Hits
1. Upload a prompt source (csaesrapp currently only accepts CMU pronunciation dictionary formatted files. It is capable of accepting RM prompt files but you need to plug in apps.elicitation.adapters.ResourceManagementAdapter)
 * Click on Prompt sources
 * Click 'add prompt source' in the top right corner
 * Select the CMU dictionary file from your filesystem
 * If you 
1. Select the prompt source from the list of prompt sources
2. From the dropdown Action menu select "create most hits possible from prompt source"
3. Wait for the page to finish loading and then navigate to Elicitation Hits!
* Caveats:
 * It does not currently work to simply "add hit elicitation hit" via the admin interface. You can only create hits via a prompt source.

### Steps to get Submitted Assignments
1. Navigate to the Elicitation Hits page
1. Select all the hits via the checkbox at the top of the list
1. Select "Get hit submitted assignments" from the dropdown Action menu.
1. Wait for the page to finish loading and navigate to the Elicitation Assignments page
* Caveats:
 *You cannot currently approve assignments via the app, that's next on my list of TODOs

Project Stuff
-------------
### CseasrApp Structure
- Django encourages modularity by allowing an arbitrary number of helper apps
- CsaesrApp contains a number of utility apps within itself, for example:
 * the mturk app (apps.mturk) handles all operations with respect to MTurk (via boto commands)
 * the audio app (apps.audio) handles all operations dealing with audio files
- Most importantly, the common app contains the common operations between the transcription and elicitation pipelines
 * apps.common.pipelines.MturkPipeline contains all the 
#### Models in CsaesrApp
- Django uses "model" as an extension for a classic "object".
- Model definitions contain "field" data members
- Because every model inheret's from Django's generic model definition, every model also comes with a very nice "form" (synonomous with an HTML form) that can easily be used to create new models!
#### Model States in CsaesrApp
- All models in csaesrapp inheret directly from StateModel, which means that they have an explicit state.
- Model states are defined functionally by boolean functions defined in elicitation.statemaps.ElicitationStateMap
- Model states are set after updating 
