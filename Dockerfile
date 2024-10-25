FROM python:3.11-slim AS build

RUN pip install cotdantic

FROM gcr.io/distroless/python3-debian12:nonroot

COPY --from=build /usr/local/lib /usr/local/lib
COPY --from=build /usr/local/bin /usr/local/bin
COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

ENTRYPOINT ["cotdantic"]
