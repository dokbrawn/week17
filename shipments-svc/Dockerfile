FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV GROUP=431
ENV STUDENT_ID=s01
ENV PROJECT_CODE=shipments-s01
EXPOSE 8130
CMD ["python", "app/server.py"]