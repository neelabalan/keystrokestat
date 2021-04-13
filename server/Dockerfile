FROM python:3.8
WORKDIR /app
RUN pip install -r requirements.txt
COPY ./ ./
CMD ["python", "./app.py"]
EXPOSE 8050