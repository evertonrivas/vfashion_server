FROM python:latest

WORKDIR /usr/app/backend
COPY ./ /usr/app/backend
RUN pip install -r requirements.txt
ENV FLASK_APP="app.py"
ENV FLASK_RUN_HOST=0.0.0.0
#EXPOSE 5000
CMD ["python", "app.py"]