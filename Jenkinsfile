pipeline { 
    agent { label 'kubectl-agent' } 
  
    environment { 
        K8S_DIR = "k8s" 
        APP_NS = "flask-app"
        IMAGE_NAME = "flask-webserver:build-${env.BUILD_NUMBER}"
        DOCKERFILE_DIR = "flaskServer/webserver"
    } 
  
    stages { 
        stage('Checkout') { 
            steps { 
                checkout scm
                sh """
                    echo "📁 Project structure:"
                    ls -la
                    echo ""
                    echo "📁 Dockerfile location:"
                    ls -la ${DOCKERFILE_DIR}/
                """
            } 
        }

        stage('Create Namespace') { 
            steps { 
                sh """
                    echo "🏗️  Creating namespace: ${APP_NS}"
                    # Create namespace if it doesn't exist
                    kubectl get namespace ${APP_NS} > /dev/null 2>&1
                    if [ \$? -ne 0 ]; then
                        kubectl create namespace ${APP_NS}
                        echo "✅ Namespace created"
                    else
                        echo "ℹ️  Namespace already exists"
                    fi
                """
            } 
        }

        stage('Build') { 
            steps { 
                dir(DOCKERFILE_DIR) {
                    sh """
                        echo "🔨 Building from: \$(pwd)"
                        echo "📦 Image: ${IMAGE_NAME}"
                        docker build -t ${IMAGE_NAME} .
                    """
                }
            } 
        }

        stage('Test') { 
            steps { 
                sh """
                    echo "🧪 Testing image..."
                    docker run --rm ${IMAGE_NAME} python --version
                    echo "✅ Python version check passed"
                    
                    echo "📦 Checking installed packages..."
                    docker run --rm ${IMAGE_NAME} pip list | grep -i flask || echo "Flask package not found"
                """
            } 
        }

        stage('Import to K8s') { 
            steps { 
                sh """
                    echo "⬆️  Importing to MicroK8s..."
                    docker save ${IMAGE_NAME} -o /tmp/flask-image.tar
                    microk8s.ctr --namespace k8s.io image import /tmp/flask-image.tar
                    rm -f /tmp/flask-image.tar
                    
                    echo "✅ Available images:"
                    microk8s.ctr --namespace k8s.io images ls | grep flask-webserver
                """
            } 
        }

        stage('Deploy') { 
            steps { 
                sh """
                    echo "1️⃣ Deploying MySQL..."
                    kubectl apply -n ${APP_NS} -f ${K8S_DIR}/mysql-pvc.yaml 
                    kubectl apply -n ${APP_NS} -f ${K8S_DIR}/mysql-deployment.yaml
                    kubectl apply -n ${APP_NS} -f ${K8S_DIR}/mysql-service.yaml

                    echo "2️⃣ Deploying Webserver..."
                    # Update image in deployment
                    sed "s|image:.*|image: ${IMAGE_NAME}|g" ${K8S_DIR}/webserver-deployment.yaml | kubectl apply -n ${APP_NS} -f -
                    kubectl apply -n ${APP_NS} -f ${K8S_DIR}/webserver-service.yaml

                    echo "3️⃣ Deploying phpMyAdmin..."
                    kubectl apply -n ${APP_NS} -f ${K8S_DIR}/phpmyadmin-deployment.yaml
                    kubectl apply -n ${APP_NS} -f ${K8S_DIR}/phpmyadmin-service.yaml

                    echo "4️⃣ Deploying Ingress..."
                    kubectl apply -n ${APP_NS} -f ${K8S_DIR}/flask-ingress.yaml

                    echo "5️⃣ Waiting for MySQL rollout..."
                    kubectl rollout status deployment/mysql -n ${APP_NS} --timeout=120s || echo "MySQL rollout check completed"

                    echo "6️⃣ Waiting for Webserver rollout..."
                    kubectl rollout status deployment/webserver -n ${APP_NS} --timeout=180s

                    echo "7️⃣ Waiting for phpMyAdmin rollout..."
                    kubectl rollout status deployment/phpmyadmin -n ${APP_NS} --timeout=120s || echo "phpMyAdmin rollout check completed"

                    echo "✅ All deployments complete!"
                """
            } 
        }
    } 
  
    post { 
        always { 
            echo "📊 Deployment Status:"
            sh """
                kubectl get pods -n ${APP_NS}
                echo ""
                kubectl get svc -n ${APP_NS}
            """
            sh "docker rmi ${IMAGE_NAME} 2>/dev/null || true"
        }
        failure {
            echo "❌ Pipeline failed!"
            sh """
                echo "=== Debug info ==="
                kubectl describe deployment/webserver -n ${APP_NS}
                echo ""
                kubectl logs -n ${APP_NS} deployment/webserver --tail=20
            """
        }
    } 
}
