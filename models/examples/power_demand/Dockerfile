FROM simon-model:latest
COPY requirements.txt /
RUN pip3 install -r /requirements.txt
CMD ["python3", "/opt/src/inner_wrapper.py"]
