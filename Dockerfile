FROM python:3.12-slim

WORKDIR /app

# Copy application files
COPY . .

# pmtiles comes in as a declared dependency
RUN pip install --no-cache-dir .

# /data  — mount your input/output tile files here
# /tmp   — mount a fast disk here for large conversions (e.g. -v /fast/disk:/tmp)
RUN mkdir -p /data
VOLUME /data
VOLUME /tmp

WORKDIR /data

ENTRYPOINT ["pmtiles-mbtiles-util"]
