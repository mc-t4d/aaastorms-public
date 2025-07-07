FROM public.ecr.aws/lambda/python:3.9

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m pip install -r /tmp/requirements.txt

COPY etl_main.py ./
COPY parse_storms.py ./
COPY utils.py ./

CMD [ "etl_main.handler" ]