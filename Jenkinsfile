pipeline {
    agent { label 'kubectl-agent' }

    environment {
        K8S_DIR = "k8s"
        APP_NS  = "default"   // or your namespace
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Deploy using local image') {
            steps {
                sh """
                    echo 'Applying MySQL resources...'
                    kubectl apply -n ${APP_NS} -f ${K8S_DIR}/mysql-pvc.yaml
                    kubectl apply -n ${APP_NS} -f ${K8S_DIR}/mysql-deployment.yaml
                    kubectl apply -n ${APP_NS} -f ${K8S_DIR}/mysql-service.yaml

                    echo 'Applying webserver resources...'
                    kubectl apply -n ${APP_NS} -f ${K8S_DIR}/webserver-deployment.yaml
                    kubectl apply -n ${APP_NS} -f ${K8S_DIR}/webserver-service.yaml

                    echo 'Optional components...'
                    [ -f ${K8S_DIR}/phpmyadmin-deployment.yaml ] && kubectl apply -n ${APP_NS} -f ${K8S_DIR}/phpmyadmin-deployment.yaml
                    [ -f ${K8S_DIR}/phpmyadmin-service.yaml ]    && kubectl apply -n ${APP_NS} -f ${K8S_DIR}/phpmyadmin-service.yaml
                    [ -f ${K8S_DIR}/flask-ingress.yaml ]         && kubectl apply -n ${APP_NS} -f ${K8S_DIR}/flask-ingress.yaml

                    echo 'Wait for webserver rollout...'
                    kubectl rollout status deployment/webserver -n ${APP_NS}
                """
            }
        }
    }

    post {
        always {
            sh 'kubectl get pods,svc -n ${APP_NS}'
        }
    }
}
