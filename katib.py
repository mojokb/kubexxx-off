import os
import argparse
import kubeflow.katib as kc
from datetime import datetime
from kubernetes.client import V1ObjectMeta

class KatibJob(object):
    def get_experiment_name(self, experiment_name):
        now = datetime.now()
        return "-" + experiment_name + now.strftime("%Y%m%d%S")
    
    def train(self):
        parser= argparse.ArgumentParser()
        parser.add_argument("--dataset_filename", required=False, default="Sloshing_200702.csv")
        parser.add_argument("--loss", required=False, default=1)
        parser.add_argument("--image_name", required=False, default='kubeflow-registry.default.svc.cluster.local:30000/sloshing-train-job:236C3225')
        args = parser.parse_args()
 
        #katibe description
        metadata = V1ObjectMeta(
          name = self.get_experiment_name("sloshing"),
          namespace = "shi"  
        )

        algorithm_spec = kc.V1alpha3AlgorithmSpec(
          algorithm_name = "random"
        )
        
        objective_spec = kc.V1alpha3ObjectiveSpec(
          type = "minimize",
          goal = args.loss,
          objective_metric_name = "loss"
        )
        
        parameters = [
            kc.V1alpha3ParameterSpec(
              name = "--epoch",
              parameter_type = "int",
              feasible_space = kc.V1alpha3FeasibleSpace(
                 min = "10",
                 max = "30" 
              )  
            )
        ]
        
        go_template = kc.V1alpha3GoTemplate(
          raw_template =   "apiVersion: \"batch/v1\"\nkind: Job\nmetadata:\n  name: {{.Trial}}\n  namespace: shi\nspec:\n  template:\n    spec:\n      containers:\n      - name: {{.Trial}}\n        image: " 
            + args.image_name + "\n        command:\n        - \"python\"\n        - \"/app/sloshing_for_train.py\"\n        - \"--filename="
            + args.dataset_filename + "\"\n        {{- with .HyperParameters}}\n        {{- range .}}\n        - \"{{.Name}}={{.Value}}\"\n        {{- end}}\n        {{- end}}\n      restartPolicy: Never"
        )   
        
        trial_template= kc.V1alpha3TrialTemplate(go_template=go_template)

        
        experiment = kc.V1alpha3Experiment(
          api_version = "kubeflow.org/v1alpha3",
          kind = "Experiment",
          metadata = metadata,
          spec = kc.V1alpha3ExperimentSpec(
            max_trial_count = 12,
            parallel_trial_count = 3,
            max_failed_trial_count = 3,
            algorithm = algorithm_spec,
            objective = objective_spec,
            parameters = parameters,  
            trial_template = trial_template
          )  
        )
        
        kclient = kc.KatibClient()
        kclient.create_experiment(experiment)
        
        
if __name__=="__main__":
    if os.getenv('FAIRING_RUNTIME', None) is None:
        
        from kubeflow import fairing
        from kubeflow.fairing.kubernetes import utils as k8s_utils

        DOCKER_REGISTRY = 'kubeflow-registry.default.svc.cluster.local:30000'
        fairing.config.set_builder(
            'append',
            image_name='katib-job',
            base_image='brightfly/katib-sdk:0.0.1',
            registry=DOCKER_REGISTRY,
            push=True)
        # cpu 1, memory 1GiB
        fairing.config.set_deployer('job',
                                    namespace='amaramusic'
                                    )
        # python3
        #fairing.config.set_preprocessor('python', input_files=[__file__])
        fairing.config.run()        
        
    else:
        sloshing = KatibJob()
        sloshing.train()
