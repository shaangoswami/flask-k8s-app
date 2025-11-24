pipeline {
    agent any

    environment {
        // Your Docker Hub Username
        DOCKER_HUB_USER = 'shaangoswami' 
        // The image name matches what is in your deployment yaml (without the tag)
        IMAGE_NAME = 'flask-app'
        // Create a unique tag based on the Jenkins Build Number
        IMAGE_TAG = "${BUILD_NUMBER}"
        // Combine them for the full image reference
        FULL_IMAGE = "${DOCKER_HUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}"
        
        // Credentials IDs configured in Jenkins
        DOCKER_CREDS_ID = 'dockerhub-creds'
        KUBECONFIG_ID = 'k8s-kubeconfig'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    // Navigate to the folder containing the Dockerfile and requirements.txt
                    dir('flaskServer/webserver') {
                        echo "Building image: ${FULL_IMAGE}"
                        // Build the image with the unique tag
                        sh "docker build -t ${FULL_IMAGE} ."
                    }
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                script {
                    // Log in to Docker Hub using Jenkins credentials
                    withCredentials([usernamePassword(credentialsId: DOCKER_CREDS_ID, passwordVariable: 'DOCKER_PASS', usernameVariable: 'DOCKER_USER')]) {
                        sh "echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin"
                        
                        // Push the specific tag built in the previous step
                        sh "docker push ${FULL_IMAGE}"
                        
                        // Optional: Also push 'latest' so manual pulls are easy
                        sh "docker tag ${FULL_IMAGE} ${DOCKER_HUB_USER}/${IMAGE_NAME}:latest"
                        sh "docker push ${DOCKER_HUB_USER}/${IMAGE_NAME}:latest"
                    }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                script {
                    withKubeConfig([credentialsId: KUBECONFIG_ID]) {
                        // 1. Apply static services (Database & Admin)
                        // These don't change often, so we just apply them as-is
                        sh "kubectl apply -f k8s/mysql-pvc.yaml"
                        sh "kubectl apply -f k8s/mysql-deployment.yaml" 
                        sh "kubectl apply -f k8s/mysql-service.yaml"
                        sh "kubectl apply -f k8s/phpmyadmin-deployment.yaml"
                        sh "kubectl apply -f k8s/phpmyadmin-service.yaml"

                        // 2. Update the Webserver Deployment with the NEW image tag
                        // Your YAML currently says: image: shaangoswami/flask-app:v1
                        // We need it to say: image: shaangoswami/flask-app:5 (or whatever the build number is)
                        
                        dir('k8s') {
                            // Use sed to replace the image tag in the file dynamically
                            sh "sed -i 's|shaangoswami/flask-app:v1|${FULL_IMAGE}|g' webserver-deployment.yaml"
                            
                            // Apply the updated manifest
                            sh "kubectl apply -f webserver-deployment.yaml"
                            sh "kubectl apply -f webserver-service.yaml"
                            
                            // (Optional) Force a rollout to ensure pods restart if the tag didn't change but content did
                            sh "kubectl rollout status deployment/webserver"
                        }
                    }
                }
            }
        }
    }
}
