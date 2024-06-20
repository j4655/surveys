from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse

from .models import Survey
from .models import Survey_key
from .models import Response_type
from .models import Question
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
    
    response = {'survey_key': id, 'key': key, 'questions': {'question_id': [], 'question_text': [],  'options': [], 'response_type': [], 'static_options': []}}
    qs_questions = Question.objects.filter(survey_id=id)
    for row in qs_questions:
      response['questions']['question_id'].append(row.id)
      response['questions']['question_text'].append(row.text)
      response['questions']['options'].append(row.options)
      response['questions']['response_type'].append(row.response_type.name)
      response['questions']['static_options'].append(row.response_type.static_options)
    return JsonResponse(response)
  else:
    return HttpResponse('Key was not given')
