import os
import argparse
import kubeflow.katib as kc
import json
from datetime import datetime
from kubernetes.client import V1ObjectMeta

class KatibJob(object):
    def get_experiment_name(self, experiment_name):
        now = datetime.now()
        return experiment_name + "-" + now.strftime("%Y%m%d%H%m%S")
        
    def train(self):
        parser= argparse.ArgumentParser()
        parser.add_argument("--max_failed_trial_count", required=False, type=int, default=3)
        parser.add_argument("--parallel_trial_count", required=False, type=int, default=1)        
        parser.add_argument("--max_trial_count", required=False, type=int, default=12)        
        parser.add_argument("--user_namespace", required=False, type=str, default="amaramusic")                
        parser.add_argument("--train_image_name", required=False, default='kubeflow-registry.default.svc.cluster.local:30000/mnist-train:B286FA83')
        args = parser.parse_args()
        
        user_namespace = args.user_namespace
 
        #katibe description
        metadata = V1ObjectMeta(
          name = self.get_experiment_name("mnist"),
          namespace = user_namespace  
        )

        algorithm_spec = kc.V1alpha3AlgorithmSpec(
          algorithm_name = "random"
        )
        
        objective_spec = kc.V1alpha3ObjectiveSpec(
          type = "maximize",
          goal = 0.99999,
          objective_metric_name = "val_acc"
        )
        
        parameters = [
            kc.V1alpha3ParameterSpec(
              name = "--epoch",
              parameter_type = "int",
              feasible_space = kc.V1alpha3FeasibleSpace(
                 min = "10",
                 max = "30" 
              )  
            ),
            kc.V1alpha3ParameterSpec(
              name = "--batch_size",
              parameter_type = "int",
              feasible_space = kc.V1alpha3FeasibleSpace(
                 min = "8",
                 max = "24" 
              )  
            ),
            kc.V1alpha3ParameterSpec(
              name = "--dropout_rate",
              parameter_type = "double",
              feasible_space = kc.V1alpha3FeasibleSpace(
                 min = "0.1",
                 max = "0.9" 
              )  
            )        
        ]
        
        go_template = kc.V1alpha3GoTemplate(
          raw_template =   
              "apiVersion: \"batch/v1\"\n" 
            + "kind: Job\n"
            + "metadata:\n"
            + "  name: {{.Trial}}\n"
            +f"  namespace: {user_namespace}\n"
            + "spec:\n"
            + "  template:\n" 
            + "    spec:\n"
            + "      containers:\n" 
            + "      - name: {{.Trial}}\n" 
            +f"        image: {args.train_image_name}\n" 
            + "        command:\n" 
            + "        - \"python\"\n" 
            + "        - \"/app/mnist_for_train.py\"\n"
            + "        {{- with .HyperParameters}}\n"
            + "        {{- range .}}\n"
            + "        - \"{{.Name}}={{.Value}}\"\n"
            + "        {{- end}}\n"
            + "        {{- end}}\n"
            + "        resources:\n"             
            + "          limits:\n"                         
            + "            cpu: 0.5\n"                         
            + "            memory: 2Gi\n"                                     
            + "      restartPolicy: Never"
        )   
        
        trial_template= kc.V1alpha3TrialTemplate(go_template=go_template)

        
        experiment = kc.V1alpha3Experiment(
          api_version = "kubeflow.org/v1alpha3",
          kind = "Experiment",
          metadata = metadata,
          spec = kc.V1alpha3ExperimentSpec(
            max_trial_count = args.max_trial_count,
            parallel_trial_count = args.parallel_trial_count,
            max_failed_trial_count = args.max_failed_trial_count,
            algorithm = algorithm_spec,
            objective = objective_spec,
            parameters = parameters,  
            trial_template = trial_template
          )  
        )
        kclient = kc.KatibClient()
        kclient.create_experiment(experiment)

        metrics = {
          'metrics': [{
              'experiment_name': metadata.name, # The name of the metric. Visualized as the column name in the runs table.
              'format': "raw"  # The optional format of the metric. Supported values are "RAW" (displayed in raw format) and "PERCENTAGE" (displayed in percentage format).
          }]
        }
        with open('/output.txt', "w") as output_f:
          output_f.write(metadata.name) 
        
        with open('/mlpipeline-metrics.json', 'w') as metric_f: 
          json.dump(metrics, metric_f)        
        
if __name__=="__main__":
    if os.getenv('FAIRING_RUNTIME', None) is None:

        from kubeflow import fairing
        from kubeflow.fairing.kubernetes import utils as k8s_utils

        DOCKER_REGISTRY = 'kubeflow-registry.default.svc.cluster.local:30000'
        fairing.config.set_builder(
            'append',
            image_name='mnist-katib-job',
            base_image='brightfly/katib-sdk:0.0.1',
            registry=DOCKER_REGISTRY,
            push=True)
        # cpu 1, memory 1GiB
        fairing.config.set_deployer('job',
                                    namespace='amaramusic'
                                    )
        fairing.config.run()        
        """
        from kubeflow.fairing.builders.append.append import AppendBuilder
        from kubeflow.fairing.preprocessors.converted_notebook import ConvertNotebookPreprocessor

        DOCKER_REGISTRY = 'kubeflow-registry.default.svc.cluster.local:30000'
        base_image='brightfly/katib-sdk:0.0.1'
        image_name='mnist-katib-job'

        builder = AppendBuilder(
            registry=DOCKER_REGISTRY,
            image_name=image_name,
            base_image=base_image,
            push=True,
            
            preprocessor=ConvertNotebookPreprocessor(
                notebook_file="mnist_for_katib.ipynb" )
            )
        builder.build()  
                """
    else:
        sloshing = KatibJob()
        sloshing.train()
