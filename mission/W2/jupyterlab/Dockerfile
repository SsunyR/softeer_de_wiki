FROM jupyter/scipy-notebook

COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /home/jovyan

RUN rm /home/jovyan/requirements.txt

EXPOSE 8888

ENV PYDEVD_DISABLE_FILE_VALIDATION=1

CMD ["start-notebook.py", "--NotebookApp.token=", "--NotebookApp.ip=0.0.0.0", "--NotebookApp.allow_origin='*'", "--NotebookApp.allow_remote_access=True", "--allow-root"]