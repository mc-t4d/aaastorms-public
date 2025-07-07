FROM public.ecr.aws/lambda/python:3.9

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m pip install -r /tmp/requirements.txt

COPY report_main.py ./
COPY reporting.py ./
COPY config.py ./
COPY templates ./templates

CMD [ "report_main.handler" ]