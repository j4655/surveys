from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.db.models import Q
# from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

from . import config
from .models import Question
from .models import Submission
from .models import Survey
from .models import Survey_key
from .models import Response
from .models import Response_type
from .models import Language

import pandas as pd
from datetime import datetime
from urllib.parse import quote, unquote
import os

if config.USE_GOOGLE_TRANSLATE == True:
  # Will need to make this an optional dependency at some point
  from google.cloud import translate_v2 as translate
  from .models import Question_translation




### The term object used in the comments can refer to a dictionary. It is basicly JSON. ###

def survey_logout(request):
  logout(request)
  return redirect('select')

def survey_login(request):
  if(request.user.is_authenticated == False):
    if(request.method == 'POST'):
      username = request.POST["username"]
      password = request.POST["password"]
      user = authenticate(request, username=username, password=password)
      if(user is not None):
        login(request, user)
        return redirect('select')
      else:
        # possibly add context object for indicating the login failure to user when template renders
        # possibly add additional functionality where user accounts get locked after multiple login failures
        return render(request, 'surveys/login.html')
    else:
      return render(request, 'surveys/login.html')
  else:
    return redirect('select')

'''
Deny access if user is not authenticated.
Render the survey creation form if the request method IS NOT POST.
Create a new survey and questions in the request method IS POST.
'''
def createSurvey(request):
  if(request.user.is_authenticated == False):
    return redirect('survey_login')
  if(request.method == 'POST'):
    # Reformat the POST data into JSON
    uinput = {}
    for key, value in request.POST.items():
      uinput[key] = value

    # Create the survey record
    new_survey = Survey()
    new_survey.name = uinput['survey-name']
    if(uinput['survey-start'] != "" and uinput['survey-end'] != ""):
      new_survey.start = uinput['survey-start']
      new_survey.end = uinput['survey-end']
    if ('survey-is-open' in uinput ):
      new_survey.is_open = True
    else:
      new_survey.is_open = False

    # Clean and save survey record
    new_survey.clean()
    new_survey.save()

    # Parse the input and format question data
    new_questions = {'q_id': [], 'field': [], 'number': [], 'value': []}
    for key, value in uinput.items():
      if len(key.split('question-')) > 1:
        q_data = key.split('-')
        new_questions['q_id'].append(int(q_data[1]))
        new_questions['field'].append(q_data[2])
        if len(q_data) >= 4:
          new_questions['number'].append(int(q_data[3]))
        else:
          new_questions['number'].append(0)
        new_questions['value'].append(value)
    q = pd.DataFrame(new_questions)

    # Create the question records
    for i in q['q_id'].unique():
      new_question = Question()
      # set Survey FK
      new_question.survey = new_survey
      # set question text
      new_question.text = q[(q['q_id'] == i) & (q['field'] == 'text')].iat[0,3]
      # set question Response Type FK
      new_question.response_type = Response_type.objects.get(pk=q[ (q['q_id'] == i) & (q['field'] == 'response_type')].iat[0,3])
      # set question Required to True or False depending on if the required checkbox was checked
      if(len(q[ (q['q_id'] == i) & (q['field'] == 'required') ]['value']) == 0):
        new_question.required = False
      else:
        new_question.required = True
      # set question options
      options_df = q[ (q['q_id'] == i) & (q['field'] == 'option') ].sort_values(by='number')
      options = ''
      for option in options_df['value']:
        options = options + quote(str(option)) + ','
      if len(options) > 0:
        options = options[0:-1]
        new_question.options = options

      # clean and save each question
      new_question.clean()
      new_question.save()

    # Redirect to the success page
    return render(request, 'surveys/success.html', context={'success_msg': 'Your survey was successfully created.'})
    # return JsonResponse(new_questions)
    # return JsonResponse(uinput)
  else:
    context = {'response_types': []}
    for x in Response_type.objects.all():
      context['response_types'].append({'id': x.id, 'name': x.name})
    return render(request, 'surveys/create_survey.html', context=context)


'''
Returns a queryset containing all surveys that are open and active.
The is_open field needs to be set to True and the start and end date
either need to both be null or the current datetime needs to be between them.
The end date effectively expires a survey at 12 am of the date it is set to.
'''
def getOpenSurveys():
  now = datetime.now()
  surveys = Survey.objects.filter(
    Q(is_open=True) & (
      (
        Q(start__lte=now) & Q(end__gt=now)
      )
      |
      (
        Q(start__isnull=True) & Q(end__isnull=True)
      )
    )
  )
  return(surveys)


'''
Takes the id of a Survey object and returns true if the survey is open and active (contained within the queryset
returned by the getOpenSurveys function).
It returns false if the Survey is not open or active.
'''
def isSurveyOpen(id):
  try:
    survey = getOpenSurveys().get(pk=id)
    return True
  except Survey.DoesNotExist:
    return False
  

'''
Checks if a key exists for the given survey. If it does not the function returns False.
If the survey key exists, then True or False is returned depending on whether or not
the given survey is open.
'''
def isKeyValid(key, survey_id):
  try:
    Survey_key.objects.get(survey_id=survey_id, key=key)
    return isSurveyOpen(survey_id)
  except Survey_key.DoesNotExist:
    return False


'''
This view runs when the user enters the main page of the application (home page / index).
It only collects survey records that are marked as open.
It creates a context object that contains an array of surveys,
with each element in that array being a survey object containing a name and id.
The context is passed to the survey_list template for rendering.
'''
def selectSurvey(request):
  response = {'surveys': []}
  surveys = getOpenSurveys()
  survey_q = surveys.order_by('name')
  for x in survey_q:
    row = {'name': x.name, 'id': x.id}
    response['surveys'].append(row)
  return render(request, 'surveys/survey_list.html', context=response)


'''

'''
def getLang(request, id):
  key = request.POST.get('key')

  if(isKeyValid(key, id) == False):
    raise Http404
  # else:
  #   survey_key = Survey_key.objects.get(survey_id=id, key=key)
  
  context = {'survey_id': id, 'key': key, 'default_languages': [], 'other_languages': []}
  default_languages = Language.objects.filter(is_default=True)
  other_languages = Language.objects.filter(is_default=False)
  for x in default_languages:
    lang = {'id': x.id, 'display': str(x)}
    context['default_languages'].append(lang)
  for x in other_languages:
    lang = {'id': x.id, 'display': str(x)}
    context['other_languages'].append(lang)
  return render(request, 'surveys/select_language.html', context=context)


'''
This view runs when the user selects a survey from the list on the home page
or when they visit the root of the application with '/[survey_id]' at the end of the URL.
It checks if the survey is open and active, and if it is not it will raise a 404 error.
If the survey is valid, then it will render a page where it will ask for a survey key.
'''
def getKey(request, id):
  response = {'survey_name': '', 'survey_id': id}
  try:
    survey = getOpenSurveys().get(pk=id)
  except Survey.DoesNotExist:
    raise Http404
  response['survey_name'] = survey.name
  return render(request, 'surveys/get_key.html', context=response)


'''
This view takes POST data containing a survey key, along with a survey, id as input.
It will return 404 if the survey trying to be accessed is not open or active.
It will return 404 if no survey key was given.
It will return 403 if the survey key that was given is not valid for the survey attempted to access.
If everything is successfully validated, then the questions for the survey are formatted into a
context object and passed to the response template to be rendered.
'''
def surveyResponse(request, id):
  key = request.POST.get('key')
  lang_id = request.POST.get('language_select')
  
  if(isKeyValid(key, id) == False):
    raise Http404
  else:
    survey_key = Survey_key.objects.get(survey_id=id, key=key)
  try:
    lang = Language.objects.get(pk=lang_id)
  except Language.DoesNotExist:
    raise Http404

  response = {'survey_name': survey_key.survey.name,'survey': id, 'key': key, 'questions': []}
  qs_questions = Question.objects.filter(survey_id=id).order_by('id')

   # If the language is not English, we will check if all questions
   # translations stored for the given language.
   # If there are any translations missing, Google API will be used
   # to attempt translation of the missing questions.
   # If there are still any missing translations, questions with
   # missing translations will be rendered
   # with the default question text (English). 
   # We will display whatever we can in the selected language.
  if lang.name == 'English' or config.USE_GOOGLE_TRANSLATE == False:
    needs_translation = False
    for row in qs_questions:
      option_objects = []
      if (
          (row.response_type.name == "Options-Single" or row.response_type.name == "Options-Multi")
          and row.options is not None
          ):
        options_list = row.options.split(',')
        for i in range(len(options_list)):
          option_obj = {'option_number': i+1, 'option_text': unquote(options_list[i])}
          option_objects.append(option_obj)
      q = {
        'question_id': row.id, 
        'question_text': row.text, 
        'options': option_objects, 
        'required': row.required,
        'response_type': row.response_type.name, 
        'static_options': row.response_type.static_options.split(',')}
      response['questions'].append(q)
  else:
    needs_translation = True
    t_client = translate.Client()
    translations = []
    for row in qs_questions:
      try:
        qs_trans = Question_translation.objects.get(language=lang, question=row)
        translations.append(qs_trans)
      except Question_translation.DoesNotExist:
        # Has to get translation vie API
        translation = t_client.translate(row.text, source_language=config.TRANSLATE_SOURCE, target_language=lang.code)
        if(len(translation['translatedText']) > 0):
          qs_trans = Question_translation()
          qs_trans.question = row
          qs_trans.language = lang
          qs_trans.text = translation['translatedText']
          if row.options is not None:
            trans_options = ''
            for option in row.options.split(','):
              option_text = unquote(option)
              option_trans = t_client.translate(option_text, source_language=config.TRANSLATE_SOURCE, target_language=lang.code)
              if(len(option_trans['translatedText']) > 0):
                #continue
                trans_options += quote(option_trans['translatedText']) + ','
              else:
                # ERROR
                return HttpResponse('There was an issue translating one of the question options')
            qs_trans.options = trans_options[0:-1]
          qs_trans.clean()
          qs_trans.save()
          translations.append(qs_trans)
        else:
          # ERROR
          return HttpResponse('There was an issue with translating the question text')
      
    # Process the questions for rendering now
    for row in translations:
      option_objects = []
      if (
          (row.question.response_type.name == "Options-Single" or row.question.response_type.name == "Options-Multi")
          and row.options is not None
          ):
        options_list = row.options.split(',')
        for i in range(len(options_list)):
          option_obj = {'option_number': i+1, 'option_text': unquote(options_list[i])}
          option_objects.append(option_obj)
      q = {
        'question_id': row.question.id, 
        'question_text': row.text, 
        'options': option_objects, 
        'required': row.question.required,
        'response_type': row.question.response_type.name, 
        'static_options': row.question.response_type.static_options.split(',')}
      response['questions'].append(q)
  # return JsonResponse(response)
  return render(request, 'surveys/response.html', context=response)


'''
This view validates the survey id and survey key that are posted along with the question responses.
If either the survey or key is invalid, 403 is returned.
If validation is successful, then responses are parsed, a submission is created, and then the response
records are created using the newly created submission's ID.
'''
def submitResponse(request):
  # FIXME: need to add functionality to support the new Question field "required,"
  # since this field is stored in a question record as a field, and not a property of a
  # model field, we will need to build our own validation to enforce the response requirement.
  # This functionality will be to protect against bypassing the html "required" property on the input elements

  if(isKeyValid(request.POST['key'], request.POST['survey']) == False):
    raise PermissionDenied
  
  survey = request.POST['survey']
  survey_key = Survey_key.objects.get(survey=Survey.objects.get(pk=survey), key=request.POST['key'])

  data = {'key': [], 'question-number': [], 'value': []}
  multi_option_data = {'key_map': {}, 'value_map': {}}
  for key, value in request.POST.items():
    if ( key[:9] == 'question-' and len(key.split('-')) == 2 ):
      data['key'].append(key)
      data['question-number'].append(int(key[9::]))
      data['value'].append(value)
    elif ( len(key.split('-')) == 3 ):
        multi_option = key.split('-')
        multi_option_data['key_map'][multi_option[1]] = key
        if ( multi_option[1] in multi_option_data['value_map'] ):
          multi_option_data['value_map'][multi_option[1]] = str(multi_option_data['value_map'][multi_option[1]]) + ',' + quote(str(value))
        else:
          multi_option_data['value_map'][multi_option[1]] = quote(str(value))
  for q in multi_option_data['key_map']:
    # { question_8 -> key_1, question_8 -> 'this,that,other' }
    data['key'].append(multi_option_data['key_map'][q])
    data['question-number'].append(q)
    data['value'].append(multi_option_data['value_map'][q])

  submission = Submission(language='English', ts=datetime.now(), survey_key=survey_key)
  submission.save()

  for i in range(len(data['question-number'])):
    try:
      question = Question.objects.filter(survey=survey).get(pk=data['question-number'][i])
    except question.DoesNotExist:
      return HttpResponse('None was returned')
    response = Response(question=question, submission=submission, response=(data['value'][i]) )
    response.save()
  return render(request, 'surveys/success.html', context={'success_msg': 'Your survey response was successfully submitted.'})
    
