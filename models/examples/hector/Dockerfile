# build from the base model image (required)
FROM simon-model:latest

# install dependencies
RUN apt-get update && apt-get install -y libboost-filesystem-dev libboost-system-dev
ENV LC_ALL C.UTF-8
RUN pip3 install pybind11
RUN pip3 install pyhector==2.1.0.0

# run the inner wrapper (required)
CMD ["python3", "/opt/src/inner_wrapper.py"]
