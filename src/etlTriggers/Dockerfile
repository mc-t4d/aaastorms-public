FROM public.ecr.aws/lambda/python:3.9

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m pip install -r /tmp/requirements.txt

COPY etlTriggers_main.py ./
COPY parse_storms.py ./
COPY utils.py ./

CMD [ "etlTriggers_main.handler" ]