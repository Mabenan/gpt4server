FROM python:3-slim

EXPOSE 5000
ENV APP_DATA_LOC=/app/appData
ENV WEB_SERVER_THREADS=2
ENV SECRET_KEY=sfawag
COPY ./ /app
WORKDIR /app
RUN mkdir ./appData
RUN pip install -r requirements.txt
RUN chmod +x ./start.sh
CMD [ "/bin/sh", "-c", "/app/start.sh" ]