FROM public.ecr.aws/lambda/python:3.8

RUN yum install -y gcc gcc-c++ make
RUN pip install --upgrade pip setuptools
RUN pip install scikit-learn

COPY iris_model.sav .
COPY lambda_function.py .

CMD [ "lambda_function.lambda_handler" ]