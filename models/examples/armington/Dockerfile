# build from the base model image (required)
FROM simon-model:latest

# install dependencies
RUN pip3 install numpy==1.16.4 scipy==1.3.0 bokeh pymongo

# run the inner wrapper (required)
CMD ["python3", "/opt/src/inner_wrapper.py"]
