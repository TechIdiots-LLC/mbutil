FROM python:3.12-slim

WORKDIR /app

# Copy application files (PMTiles submodule must be initialized)
COPY . .

# Install mbutil and dependencies
RUN pip install --no-cache-dir .

# /data  — mount your input/output tile files here
# /tmp   — mount a fast disk here for large conversions (e.g. -v /fast/disk:/tmp)
RUN mkdir -p /data
VOLUME /data
VOLUME /tmp

WORKDIR /data

ENTRYPOINT ["mb-util"]
