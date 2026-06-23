# Spinning Up in OpenScope — analysis container
#
# The core NWB/DANDI stack is pure-Python, so a slim base works everywhere.
# On the GB10 / DGX Spark, you can instead base on the NGC PyTorch image to get
# a CUDA stack for downstream modeling (the NWB tools don't need it):
#     FROM nvcr.io/nvidia/pytorch:26.04-py3
#
FROM python:3.10-slim

LABEL org.opencontainers.image.title="spinning-up-in-openscope"
LABEL org.opencontainers.image.description="OpenScope predictive-processing mouse-data analysis + EEG bridge"

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        git build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work
COPY requirements.txt /work/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Smoke-test the imports at build time
RUN python -c "import pynwb, dandi, h5py, remfile, mne; print('OpenScope stack OK')"

EXPOSE 8888
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
