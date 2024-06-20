from django.db import models

# Create your models here.
class Survey(models.Model):
  class Meta():
    constraints = [models.UniqueConstraint(fields=['name'], name='uniq_Survey')]
  name = models.CharField()
  is_open = models.BooleanField()
  start = models.DateField(blank=True, null=True)
  end = models.DateField(blank=True, null=True)
  def __str__(self):
    return self.name

class Response_type(models.Model):
  name = models.CharField()
  input_type = models.CharField()
  static_options = models.TextField(blank=True, null=True)
  def __str__(self):
    return self.name

class Question(models.Model):
  survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
  response_type = models.ForeignKey(Response_type, on_delete=models.PROTECT)
  text = models.TextField()
  options = models.TextField(blank=True, null=True)
  def __str__(self):
    return self.survey.name + ' > ' + self.response_type.name + ' > ' + self.text

class Question_translation(models.Model):
  question = models.ForeignKey(Question, on_delete=models.CASCADE)
  language = models.CharField()
  text = models.TextField()
  options = models.TextField(blank=True, null=True)
  def __str__(self):
    return self.question.survey.name + ' > ' + self.question.response_type.name + ' > Lang:' + self.language + ' > ' + self.question.text

class Survey_key(models.Model):
  class Meta():
    constraints = [models.UniqueConstraint(fields=['survey', 'key'], name='uniq_survey_key')]
  survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
  key = models.CharField()
  def __str__(self):
    return self.survey.name + ' > Key:' + self.key

class Submission(models.Model):
  survey_key = models.ForeignKey(Survey_key, on_delete=models.CASCADE)
  language = models.CharField()
  ts = models.DateTimeField()
  def __str__(self):
    return self.survey_key.survey.name + ' > Key:' + self.survey_key.key + ' > ID:' + str(self.id)

class Response(models.Model):
  question = models.ForeignKey(Question, on_delete=models.PROTECT)
  submission = models.ForeignKey(Submission, on_delete=models.PROTECT)
  response = models.TextField()
  def __str__(self):
    return self.question.survey.name + ' > Response:' + str(self.id)
