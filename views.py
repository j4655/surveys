from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.db.models import Q
# from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login

from .models import Question, Submission, Survey, Survey_key, Response, Response_type

# import pandas as pd
from datetime import datetime
from urllib.parse import quote, unquote




### The term object used in the comments can refer to a dictionary. It is basicly JSON. ###

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

def createSurvey(request):
  if(request.user.is_authenticated == False):
    raise PermissionDenied
  if(request.method == 'POST'):
    response = {}
    for key, value in request.POST.items():
      response[key] = value
    return JsonResponse(response)
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

  if(isKeyValid(key, id) == False):
    raise Http404
  else:
    survey_key = Survey_key.objects.get(survey_id=id, key=key)
    
  response = {'survey_name': survey_key.survey.name,'survey': id, 'key': key, 'questions': []}
  qs_questions = Question.objects.filter(survey_id=id).order_by('id')
  
  for row in qs_questions:
    option_objects = []
    if (row.response_type.name == "Options-Single" or row.response_type.name == "Options-Multi"):
      options_list = row.options.split(',')
      for i in range(len(options_list)):
        option_obj = {'option_number': i+1, 'option_text': options_list[i]}
        option_objects.append(option_obj)
    q = {
      'question_id': row.id, 
      'question_text': row.text, 
      'options': option_objects, 
      'required': row.required,
      'response_type': row.response_type.name, 
      'static_options': row.response_type.static_options.split(',')}
    response['questions'].append(q)

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
  return render(request, 'surveys/success.html')
    
