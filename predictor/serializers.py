from rest_framework import serializers
from .models import Prediction

class PredictionSerializer(serializers.ModelSerializer):
    result = serializers.IntegerField(read_only=True)

    class Meta:
        model = Prediction
        exclude = ['student', 'created_at']
