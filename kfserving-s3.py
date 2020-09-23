from kubernetes import client

from kfserving import KFServingClient
from kfserving import constants
from kfserving import utils
from kfserving import V1alpha2EndpointSpec
from kfserving import V1alpha2PredictorSpec
from kfserving import V1alpha2TensorflowSpec
from kfserving import V1alpha2InferenceServiceSpec
from kfserving import V1alpha2InferenceService
from kubernetes.client import V1ResourceRequirements

namespace = utils.get_default_target_namespace()

api_version = constants.KFSERVING_GROUP + "/" + constants.KFSERVING_VERSION
default_endpoint_spec = V1alpha2EndpointSpec(
                          predictor=V1alpha2PredictorSpec(
                            tensorflow=V1alpha2TensorflowSpec(
                              storage_uri="s3://anonymous-model-result/result/saved_model",
                              resources=V1ResourceRequirements(
                                  requests={"cpu":"100m","memory":"1Gi"},
                                  limits={"cpu":"100m", "memory":"1Gi"}))))
    
isvc = V1alpha2InferenceService(api_version=api_version,
                          kind=constants.KFSERVING_KIND,
                          metadata=client.V1ObjectMeta(
                              name="mnist-kfserving", namespace=namespace),
                          spec=V1alpha2InferenceServiceSpec(default=default_endpoint_spec))
                          
KFServing = KFServingClient()
KFServing.set_credentials(storage_type="S3", 
                          namespace='anonymous',
                          credentials_file='credentials',
                          s3_profile="default",
                          s3_endpoint="minio-service.kubeflow.svc.cluster.local:9000",
                          s3_region="us-west-1",
                          s3_use_https="0",
                          s3_verify_ssl="0")
                          
KFServing.create(isvc)                          
