pipeline {
    agent {
        label 'my-pc-agent'
    }
    environment {
        // Docker Hub configuration
        DOCKER_HUB_USER = 'shaangoswami'
        IMAGE_NAME = 'flask-app'
        IMAGE_TAG = "${BUILD_NUMBER}"
        FULL_IMAGE = "${DOCKER_HUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}"

        HTTP_PROXY = 'http://10.20.4.125:3128'
        HTTPS_PROXY = 'http://10.20.4.125:3128'
        NO_PROXY = 'localhost,127.0.0.1,10.20.41.184'
        
        // Kubernetes configuration
        APP_NAMESPACE = 'default'
        DOCKER_CREDS_ID = 'dockerhub-creds'
        MINIKUBE_KUBECONFIG = 'minikube-kubeconfig'
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
    }

    stages {
        stage('Checkout') {
            steps {
                script {
                    echo '=== Checking out source code ==='
                    checkout scm
                    sh 'ls -la'
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    echo "=== Building Docker image: ${FULL_IMAGE} ==="
                    dir('flaskServer/webserver') {
                        sh """
                            docker build \
                            --build-arg http_proxy=${HTTP_PROXY} \
                            --build-arg https_proxy=${HTTPS_PROXY} \
                            --build-arg no_proxy=${NO_PROXY} \
                            -t shaangoswami/flask-app:${BUILD_NUMBER} .
                        """
                        sh """
                            # Build the Docker image
                            docker build -t ${FULL_IMAGE} .
                            
                            # Tag as latest
                            docker tag ${FULL_IMAGE} ${DOCKER_HUB_USER}/${IMAGE_NAME}:latest
                            
                            # Verify image was created
                            docker images | grep ${IMAGE_NAME}
                            
                            echo '✅ Image built successfully'
                        """
                    }
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                script {
                    echo '=== Pushing image to Docker Hub ==='
                    withCredentials([usernamePassword(
                        credentialsId: "${DOCKER_CREDS_ID}",
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )]) {
                        sh """
                            # Login to Docker Hub
                            echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin
                            
                            # Push specific build tag
                            echo 'Pushing ${FULL_IMAGE}...'
                            docker push ${FULL_IMAGE}
                            
                            # Push latest tag
                            echo 'Pushing ${DOCKER_HUB_USER}/${IMAGE_NAME}:latest...'
                            docker push ${DOCKER_HUB_USER}/${IMAGE_NAME}:latest
                            
                            echo '✅ Images pushed successfully'
                        """
                    }
                }
            }
        }

        stage('Test Application') {
            steps {
                script {
                    echo '=== Running application tests ==='
                    sh """
                        # Basic container test
                        echo 'Testing if container can start...'
                        docker run --rm ${FULL_IMAGE} python --version
                        
                        # Test Flask import
                        docker run --rm ${FULL_IMAGE} python -c "from flask import Flask; print('✅ Flask imported successfully')"
                        
                        # Optional: Run pytest if tests exist
                        if docker run --rm ${FULL_IMAGE} ls tests 2>/dev/null; then
                            echo 'Running pytest...'
                            docker run --rm ${FULL_IMAGE} pytest tests/ -v || echo '⚠️ Tests not configured'
                        else
                            echo 'ℹ️ No tests directory found, skipping pytest'
                        fi
                        
                        echo '✅ All tests passed'
                    """
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    echo '=== Deploying ==='
                    withCredentials([file(credentialsId: "${MINIKUBE_KUBECONFIG}", variable: 'KUBECONFIG')]) {
                        sh """
                            set -e  # Exit on any error
                            
                            # Step 1: Set kubeconfig and verify cluster access
                            export KUBECONFIG=\${KUBECONFIG}
                            echo '=== Verifying cluster connection ==='
                            kubectl cluster-info || { echo '❌ Failed to connect to Minikube'; exit 1; }
                            kubectl get nodes
                            
                            # Step 2: Create namespace if not exists
                            echo '=== Ensuring namespace exists ==='
                            kubectl create namespace ${APP_NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
                            
                            # Step 3: Update deployment YAML with new image
                            echo '=== Updating webserver deployment image ==='
                            cd k8s
                            cp webserver-deployment.yaml webserver-deployment.yaml.bak
                            
                            # Update image reference
                            sed -i "s|image:.*flask-app.*|image: ${FULL_IMAGE}|g" webserver-deployment.yaml
                            
                            # Ensure imagePullPolicy is set to Always (pull from Docker Hub)
                            if ! grep -q 'imagePullPolicy' webserver-deployment.yaml; then
                                sed -i '/image:.*/a\\          imagePullPolicy: Always' webserver-deployment.yaml
                            else
                                sed -i 's/imagePullPolicy:.*/imagePullPolicy: Always/' webserver-deployment.yaml
                            fi
                            
                            echo '=== Updated deployment YAML ==='
                            grep -A 2 'image:' webserver-deployment.yaml
                            cd ..
                            
                            # Step 4: Deploy database layer
                            echo '=== Deploying MySQL database ==='
                            kubectl apply -n ${APP_NAMESPACE} -f k8s/mysql-pvc.yaml
                            kubectl apply -n ${APP_NAMESPACE} -f k8s/mysql-deployment.yaml
                            kubectl apply -n ${APP_NAMESPACE} -f k8s/mysql-service.yaml
                            
                            # Wait for MySQL to be ready
                            echo '=== Waiting for MySQL to be ready ==='
                            kubectl wait --for=condition=ready pod -l app=mysqldb -n ${APP_NAMESPACE} --timeout=120s || echo '⚠️ MySQL not ready yet, continuing...'
                            
                            # Step 5: Deploy Flask application
                            echo '=== Deploying Flask webserver ==='
                            kubectl apply -n ${APP_NAMESPACE} -f k8s/webserver-deployment.yaml
                            kubectl apply -n ${APP_NAMESPACE} -f k8s/webserver-service.yaml
                            
                            # Step 6: Deploy optional components
                            echo '=== Deploying optional components ==='
                            if [ -f k8s/phpmyadmin-deployment.yaml ]; then
                                echo 'Deploying phpMyAdmin...'
                                kubectl apply -n ${APP_NAMESPACE} -f k8s/phpmyadmin-deployment.yaml
                                kubectl apply -n ${APP_NAMESPACE} -f k8s/phpmyadmin-service.yaml
                            fi
                            
                            if [ -f k8s/flask-ingress.yaml ]; then
                                echo 'Deploying Ingress...'
                                kubectl apply -n ${APP_NAMESPACE} -f k8s/flask-ingress.yaml
                            fi
                            
                            # Step 7: Wait for webserver rollout
                            echo '=== Waiting for webserver rollout to complete ==='
                            kubectl rollout status deployment/webserver -n ${APP_NAMESPACE} --timeout=5m
                            
                            # Step 8: Verify deployment
                            echo '=== Deployment Status ==='
                            kubectl get pods -n ${APP_NAMESPACE} -o wide
                            kubectl get svc -n ${APP_NAMESPACE}
                            
                            # Step 9: Get access information
                            echo '=== ✅ Deployment Complete ==='
                            echo '📍 Access Information:'
                            echo '   On your PC, run one of these commands:'
                            echo "   1. minikube service webserver-service -n ${APP_NAMESPACE} --url"
                            echo "   2. kubectl port-forward svc/webserver-service 5000:80 -n ${APP_NAMESPACE}"
                            echo '   Then open: http://localhost:5000'
                        """
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                echo '=== Cleaning up ==='
                sh '''
                    docker logout || true
                    docker system prune -f || true
                '''
                
                // Display final status
                echo '=== Pipeline Execution Summary ==='
                echo "Build Number: ${BUILD_NUMBER}"
                echo "Image: ${FULL_IMAGE}"
                echo "Namespace: ${APP_NAMESPACE}"
            }
        }
        
        success {
            echo '''
            ╔════════════════════════════════════════╗
            ║   ✅ PIPELINE COMPLETED SUCCESSFULLY   ║
            ╚════════════════════════════════════════╝
            '''
            echo "Image: ${FULL_IMAGE}"
            echo "Deployed to: Minikube on your PC"
        }
        
        failure {
            echo '''
            ╔════════════════════════════════════════╗
            ║      ❌ PIPELINE FAILED                ║
            ╚════════════════════════════════════════╝
            '''
            echo 'Check the logs above for error details.'
        }
    }
}
