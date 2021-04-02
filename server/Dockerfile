FROM python:3.8
WORKDIR /app
RUN pip install dash dash-daq pandas
COPY ./ ./
CMD ["python", "./app.py"]
EXPOSE 8050