FROM python:3.12-alpine

RUN adduser -D appuser

WORKDIR /app

COPY --chown=appuser:appuser app.py .

USER appuser

EXPOSE 8000

CMD ["python", "-u", "app.py"]
