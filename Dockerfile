FROM python:latest

WORKDIR /usr/app/backend
COPY ./ /usr/app/backend
RUN pip install -r requirements.txt
ENV FLASK_APP="app.py"
#EXPOSE 5000
CMD ["python", "app.py"]