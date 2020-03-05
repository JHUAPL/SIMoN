# build from the base model image (required)
FROM simon-model:latest

# install dependencies
COPY requirements.txt /
RUN pip3 install -r /requirements.txt

# run the inner wrapper (required)
CMD ["python3", "/opt/src/inner_wrapper.py"]
