FROM repos.doc.network/cache/chainguard/python:current

USER root
WORKDIR /buddy
COPY ./source .
RUN pip install -r requirements.txt
COPY ./media ./media

USER nonroot

EXPOSE 8501
EXPOSE 80

ENTRYPOINT ["streamlit", "run", "buddy.py", "--server.address=0.0.0.0", "--server.headless=true"]
