import os
import joblib
import numpy as np
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from django.http import FileResponse
from django.utils.timezone import now
from .models import Prediction
from .serializers import PredictionSerializer
from reportlab.lib.colors import HexColor

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'gradient_boosting.pkl')
try:
    model = joblib.load(MODEL_PATH)
except Exception as e:
    raise RuntimeError(f"Erreur lors du chargement du modèle ML: {e}")

def get_advice(data, prediction):
    study = data.get("study_hours_per_day")
    social = data.get("social_media_hours")
    netflix = data.get("netflix_hours")
    sleep = data.get("sleep_hours")
    mental = data.get("mental_health_rating")
    attendance = data.get("attendance_percentage")
    part_time = data.get("part_time_job")
    extra = data.get("extracurricular_participation")

    advice_lines = []

    if prediction == 1:
        advice_lines.append("Vous semblez en difficulté. Voici une analyse personnalisée de vos habitudes :")
    else:
        advice_lines.append("Vous n'êtes pas en difficulté. Voici une évaluation de vos habitudes :")

    if study < 2:
        advice_lines.append("- Vous étudiez peu. Essayez d’atteindre au moins 2 à 3h/jour.")
    elif 2 <= study <= 4:
        advice_lines.append("- Temps d’étude modéré, c’est une bonne base.")
    else:
        advice_lines.append("- Vous étudiez beaucoup. Attention au surmenage, ménagez-vous.")

    total_screen = social + netflix
    if total_screen == 0:
        advice_lines.append("- Aucun écran détecté. Si c’est volontaire, parfait ! Sinon, n’hésitez pas à vous accorder du temps libre sainement.")
    elif total_screen <= 3:
        advice_lines.append(f"- Temps d’écran modéré. Restez vigilant à l'équilibre.")
    else:
        advice_lines.append(f"- Temps d’écran élevé. Réduisez un peu pour ne pas impacter vos performances.")

    if sleep < 6:
        advice_lines.append(f"- Sommeil insuffisant. Essayez d’atteindre 7-8h pour mieux apprendre.")
    elif 6 <= sleep <= 8:
        advice_lines.append(f"- Sommeil correct. Continuez à bien dormir.")
    else:
        advice_lines.append(f"- Sommeil long. Assurez-vous qu’il ne remplace pas du temps d’étude.")

    if mental <= 3:
        advice_lines.append("- Votre état mental est bas. N'hésitez pas à en parler à un adulte ou un professionnel.")
    elif 4 <= mental <= 6:
        advice_lines.append("- Santé mentale moyenne. Prenez soin de vous et accordez-vous des pauses.")
    else:
        advice_lines.append("- Très bonne santé mentale. C’est un point fort à maintenir.")

    if attendance >= 90:
        advice_lines.append("- Très bonne présence en classe. Cela favorise vos apprentissages.")
    else:
        advice_lines.append("- Présence en classe moyenne ou faible. Essayez d'être plus régulier.")

    if part_time:
        advice_lines.append("- Vous avez un job à côté. Pensez à bien gérer votre énergie et votre emploi du temps.")

    if extra:
        advice_lines.append("- Vous participez à des activités. Cela renforce l’équilibre et la motivation.")
    else:
        advice_lines.append("- Vous n'avez pas d'activités extérieures. Envisagez-en une pour vous aérer l’esprit.")

    return "\n".join(advice_lines)


class PredictView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PredictionSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data

            input_data = np.array([[ 
                data['study_hours_per_day'],
                data['social_media_hours'],
                data['netflix_hours'],
                data['sleep_hours'],
                data['mental_health_rating'],
                data['attendance_percentage'],
                int(data['part_time_job']),
                int(data['extracurricular_participation']),
            ]])

            prediction = model.predict(input_data)[0]
            result = "Vous risquez d'être en difficulté" if prediction == 1 else "Vous n'êtes pas en difficulté"

            Prediction.objects.create(
                student=request.user,
                result=prediction,
                **data
            )

            advice = get_advice(data, prediction)

            return Response({
                "prediction": result,
                "raw": int(prediction),
                "advice": advice
            })

        return Response({
            "error": "Les données envoyées sont invalides.",
            "details": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        predictions = Prediction.objects.filter(student=user).order_by('-created_at')

        total = predictions.count()
        difficulte = predictions.filter(result=1).count()
        non_difficulte = predictions.filter(result=0).count()

        history = [
    {
        "created_at": p.created_at.strftime("%d/%m/%Y à %H:%M"),
        "result": p.result
    }
    for p in predictions
]

        return Response({
            "total": total,
            "difficulte": difficulte,
            "non_difficulte": non_difficulte,
            "history": list(history)
        })
    
def generate_prediction_pdf(user, prediction, advice, inputs):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    blue = HexColor("#0d6efd")

    
    p.setFont("Helvetica-Bold", 16)
    p.setFillColor(blue)
    p.drawString(50, height - 50, "EduPredict - Rapport de prédiction scolaire")

    p.setFont("Helvetica", 12)
    p.setFillColor("black")
    p.drawString(50, height - 90, f"Nom : {user.full_name}")
    p.drawString(50, height - 110, f"Email : {user.email}")
    p.drawString(50, height - 130, f"Date : {now().strftime('%d/%m/%Y à %H:%M')}")

    p.setFont("Helvetica-Bold", 14)
    p.setFillColor(blue)
    p.drawString(50, height - 170, "Résultat de la prédiction :")
    p.setFont("Helvetica", 12)
    p.setFillColor("black")
    p.drawString(70, height - 190, prediction)

    p.setFont("Helvetica-Bold", 14)
    p.setFillColor(blue)
    p.drawString(50, height - 230, "Résumé des données saisies :")

    y = height - 250
    p.setFont("Helvetica", 11)
    p.setFillColor("black")

    for label, value in {
        "Heures d’étude par jour": inputs.get("study_hours_per_day"),
        "Heures sur les réseaux sociaux": inputs.get("social_media_hours"),
        "Heures de Netflix": inputs.get("netflix_hours"),
        "Heures de sommeil": inputs.get("sleep_hours"),
        "État de santé mentale": inputs.get("mental_health_rating"),
        "Présence en classe (%)": inputs.get("attendance_percentage"),
        "Travail à temps partiel": "Oui" if inputs.get("part_time_job") else "Non",
        "Activités extrascolaires": "Oui" if inputs.get("extracurricular_participation") else "Non",
    }.items():
        p.drawString(70, y, f"- {label} : {value}")
        y -= 18
        if y < 70:
            p.showPage()
            y = height - 50

    p.setFont("Helvetica-Bold", 14)
    p.setFillColor(blue)
    p.drawString(50, y - 20, "Conseils pratiques :")
    y -= 40
    p.setFont("Helvetica", 11)
    p.setFillColor("black")
    for line in advice.split('\n'):
        p.drawString(70, y, line.strip())
        y -= 18
        if y < 50:
            p.showPage()
            y = height - 50

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

class DownloadReportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        prediction_text = request.data.get("prediction")
        advice = request.data.get("advice")
        inputs = request.data.get("inputs")

        if not prediction_text or not advice or not isinstance(inputs, dict):
            return Response({"error": "Champs requis manquants ou invalides."}, status=400)
        pdf_buffer = generate_prediction_pdf(request.user, prediction_text, advice, inputs)
        filename = f"rapport_pred_{request.user.id}.pdf"
        return FileResponse(pdf_buffer, as_attachment=True, filename=filename)