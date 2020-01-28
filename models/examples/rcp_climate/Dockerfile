FROM simon-model:latest
COPY requirements.txt /
RUN pip3 install -r /requirements.txt
COPY src/weights.json /opt/src/
CMD ["python3", "/opt/src/inner_wrapper.py"]
