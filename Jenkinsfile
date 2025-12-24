pipeline {
    agent any

    environment {
        // Docker Hub credentials (configured in Jenkins)
        DOCKER_HUB_USER = 'shaangoswami'
        IMAGE_NAME = 'flask-app'
        IMAGE_TAG = "t1"
        FULL_IMAGE = "${DOCKER_HUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}"
        
        // Minikube on your PC - use a dedicated kubeconfig
        MINIKUBE_KUBECONFIG = '~/.kube/minikube-config'  // path on Jenkins agent
        APP_NAMESPACE = 'flask-app'
    }

    stages {
        stage('Build Docker Image') {
            steps {
                dir('flaskServer/webserver') {
                    sh """
                        echo "Building ${FULL_IMAGE}..."
                        docker build -t ${FULL_IMAGE} .
                        docker tag ${FULL_IMAGE} ${DOCKER_HUB_USER}/${IMAGE_NAME}:latest
                    """
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', 
                                                 passwordVariable: 'DOCKER_PASS', 
                                                 usernameVariable: 'DOCKER_USER')]) {
                    sh """
                        echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin
                        docker push ${FULL_IMAGE}
                        docker push ${DOCKER_HUB_USER}/${IMAGE_NAME}:latest
                    """
                }
            }
        }

        stage('Test Application') {
            steps {
                script {
                    // Run containerized tests
                    sh """
                        docker run --rm ${FULL_IMAGE} python -c "
                            from app import app
                            import requests
                            with app.test_client() as client:
                                response = client.get('/')
                                assert response.status_code == 200
                                print('Basic Flask test passed!')
                        "
                    """
                }
            }
        }

        stage('Deploy') {
            steps {
                withKubeConfig([credentialsId: 'minikube-kubeconfig', context: 'minikube']) {
                    sh """
                        # Create namespace
                        kubectl create namespace ${APP_NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

                        # Update image tag in deployment YAML dynamically
                        sed -i 's|image: .*|image: ${FULL_IMAGE}|g' k8s/webserver-deployment.yaml
                        sed -i '/image:/a\          imagePullPolicy: Always' k8s/webserver-deployment.yaml

                        # Deploy full stack to Minikube
                        echo 'Deploying MySQL...'
                        kubectl apply -n ${APP_NAMESPACE} -f k8s/mysql-pvc.yaml
                        kubectl apply -n ${APP_NAMESPACE} -f k8s/mysql-deployment.yaml
                        kubectl apply -n ${APP_NAMESPACE} -f k8s/mysql-service.yaml

                        echo 'Deploying Flask app...'
                        kubectl apply -n ${APP_NAMESPACE} -f k8s/webserver-deployment.yaml
                        kubectl apply -n ${APP_NAMESPACE} -f k8s/webserver-service.yaml

                        echo 'Optional components...'
                        [ -f k8s/phpmyadmin-deployment.yaml ] && kubectl apply -n ${APP_NAMESPACE} -f k8s/phpmyadmin-deployment.yaml
                        [ -f k8s/phpmyadmin-service.yaml ]    && kubectl apply -n ${APP_NAMESPACE} -f k8s/phpmyadmin-service.yaml

                        echo 'Waiting for rollout...'
                        kubectl rollout status deployment/webserver -n ${APP_NAMESPACE} --timeout=300s
                    """
                }
            }
        }
    }

    post {
        always {
            withKubeConfig([credentialsId: 'minikube-kubeconfig', context: 'minikube']) {
                sh 'kubectl get pods,svc -n ${APP_NAMESPACE}'
            }
        }
        success {
            echo "✅ Deployed ${FULL_IMAGE} to Minikube successfully!"
        }
        failure {
            echo "❌ Pipeline failed. Check logs above."
        }
    }
}
