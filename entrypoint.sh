/opt/conda/bin/jupyter notebook --generate-config
cp /root/.bashrc /home/jovyan/
cp /root/.profile /home/jovyan/
/opt/conda/bin/jupyter lab --notebook-dir=/home/jovyan --ip=0.0.0.0 --no-browser --allow-root --port=8888 --LabApp.token='' --LabApp.password='' --LabApp.allow_origin='*' --LabApp.base_url=${NB_PREFIX}
