from minio import Minio
from minio.error import ResponseError
import json
import os

def export_object_storage(namespace, saved_model_path, tensorboard_log):
    print("Send result to object storage")    
    # minio part
    tensorboard_bucket_name = namespace + "-tensorboard"
    model_bucket_name = namespace + "-model-result"

    minioClient = Minio("minio-service.kubeflow.svc.cluster.local:9000",
          access_key="minio",
          secret_key="minio123",
          secure=False)     

    # saved model to object storage
    found = minioClient.bucket_exists(model_bucket_name)
    if not found:
        minioClient.make_bucket(model_bucket_name)

    for currentpath, folders, files in os.walk(saved_model_path):
        for file in files: 
            print(os.path.join(currentpath, file))
            log_file = str(os.path.join(currentpath, file))
            minioClient.fput_object(model_bucket_name, log_file[1:], log_file)


    # tensorboard log to object storage
    found = minioClient.bucket_exists(tensorboard_bucket_name)
    if not found:
        minioClient.make_bucket(tensorboard_bucket_name)

    for currentpath, folders, files in os.walk(tensorboard_log):
        for file in files: 
            print(os.path.join(currentpath, file))
            log_file = str(os.path.join(currentpath, file))
            minioClient.fput_object(tensorboard_bucket_name, log_file[1:], log_file)

    # for Tensorboard artifact minio:// s3:// :<
    metadata = {
        "outputs": [{
            "type": "tensorboard",
            "source": "s3://" + tensorboard_bucket_name + tensorboard_log
        }]
    }

    with open("/mlpipeline-ui-metadata.json", "w") as f:
      json.dump(metadata, f)   
