FROM python:3.11-slim as build

RUN apt-get update && apt-get install -y \
    git

RUN pip install git+https://github.com/RaubCamaioni/cot_pydantic

FROM gcr.io/distroless/python3-debian12:nonroot

COPY --from=build /usr/local/lib /usr/local/lib
COPY --from=build /usr/local/bin /usr/local/bin
COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

ENTRYPOINT ["cot-listener"]
