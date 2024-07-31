FROM repos.doc.network/cache/chainguard/python:current

USER root
WORKDIR /buddy

COPY ./source .

RUN pip install -r requirements.txt


USER nonroot

EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "buddy.py", "--server.port=8501", "--server.address=0.0.0.0"]
