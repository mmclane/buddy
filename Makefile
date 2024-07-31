BUILDER:=podman
ECR=repos.doc.network
REPO=$(ECR)/m3test/buddy


login:
	aws sso login --profile hackathon
setup:
	pip install -r ./source/requirements.txt

build-container:
	podman build -t $(REPO):latest .
	podman tag $(REPO):latest $(REPO):current

push:
	podman push $(REPO):latest
	podman push $(REPO):current

build: build-container push

login-container: build-container
	$(BUILDER) run --rm -it --entrypoint /bin/sh $(REPO):latest

run-container: 
	$(BUILDER) run -p 8001:8501 $(REPO):latest
run-local:
	streamlit run ./source/buddy.py
	
