FROM gcr.io/distroless/python3-debian12:nonroot
COPY app/* /app/app.py
WORKDIR /app
CMD ["app.py"]