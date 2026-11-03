FROM python:3.12-alpine

RUN adduser -D appuser \
    && mkdir -p /data \
    && chown appuser:appuser /data

WORKDIR /app

COPY --chown=appuser:appuser app.py .
COPY --chown=appuser:appuser static ./static

USER appuser

EXPOSE 8000

CMD ["python", "-u", "app.py"]
