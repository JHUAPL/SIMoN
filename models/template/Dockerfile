# build from the base model image (required)
FROM simon-model:latest

# install dependencies
RUN pip3 install numpy pandas

# run the inner wrapper (required)
CMD ["python3", "/opt/src/inner_wrapper.py"]
