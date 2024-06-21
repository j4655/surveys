from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse

from .models import Survey
from .models import Survey_key
# from .models import Response_type
from .models import Question
from .models import Submission
from .models import Survey_key
from .models import Response
# import pandas as pd
from datetime import datetime

# Create your views here.

def selectSurvey(request):
  response = {'surveys': []}
  survey_q = Survey.objects.filter(is_open=True).order_by('name')
  for x in survey_q:
    row = {'name': x.name, 'id': x.id}
    response['surveys'].append(row)
  return render(request, 'surveys/survey_list.html', context=response)
  #return JsonResponse(response)

def getKey(request, id):
  response = {'survey_name': '', 'survey_id': id}
  try:
    survey = Survey.objects.get(pk=id)
  except Survey.DoesNotExist:
    return HttpResponse('None was returned')
  
  response['survey_name'] = survey.name
  return render(request, 'surveys/get_key.html', context=response)

def surveyResponse(request, id):
  key = request.POST.get('key')
  if (key is not None and key != '' ):
    try:
      survey_key = Survey_key.objects.filter(survey_id=id, key=key)
    except Survey_key.DoesNotExist:
      return HttpResponse('None was returned')
    
    response = {'survey': id, 'key': key, 'questions': []}
    qs_questions = Question.objects.filter(survey_id=id).order_by('id')
    for row in qs_questions:
      q = {'question_id': row.id, 'question_text': row.text, 'options': row.options, 'response_type': row.response_type.name, 'static_options': row.response_type.static_options.split(',')}
      response['questions'].append(q)
    #return JsonResponse(response)
    return render(request, 'surveys/response.html', context=response)
  else:
    return HttpResponse('Key was not given')

def submitResponse(request):
  survey = request.POST['survey']
  survey_key = Survey_key.objects.get(pk=request.POST['key'])
  data = {'key': [], 'question-number': [], 'value': []}
  for key, value in request.POST.items():
    if key[:9] == 'question-':
      data['key'].append(key)
      data['question-number'].append(int(key[9::]))
      data['value'].append(value)
  
  submission = Submission(language='English', ts=datetime.now(), survey_key=survey_key)
  submission.save()
  # return HttpResponse(submission.id)

  for i in range(len(data['question-number'])):
    try:
      question = Question.objects.filter(survey=survey).get(pk=data['question-number'][i])
    except question.DoesNotExist:
      return HttpResponse('None was returned')
    response = Response(question=question, submission=submission, response=(data['value'][i]) )
    response.save()
  return HttpResponse('Your survey response was successfully submitted.')
    
