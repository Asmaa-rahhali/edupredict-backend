from django.db import models
from django.conf import settings

class Prediction(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='predictions')

    study_hours_per_day = models.FloatField()
    social_media_hours = models.FloatField()
    netflix_hours = models.FloatField()
    sleep_hours = models.FloatField()
    mental_health_rating = models.IntegerField()
    attendance_percentage = models.FloatField()
    part_time_job = models.BooleanField()
    extracurricular_participation = models.BooleanField()

    result = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prédiction de {self.student.full_name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
