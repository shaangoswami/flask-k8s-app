pipeline { 
    agent { label 'kubectl-agent' } 

    options { 
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
    }
    
    triggers {
        // Alternative declarative syntax
        githubPush()
    }
    
    environment { 
        K8S_DIR = "k8s" 
        APP_NS = "flask-app"
        IMAGE_NAME = "flask-webserver:${BUILD_NUMBER}"
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

        stage('Verify Namespace') { 
            steps { 
                sh """
                    echo "🔍 Verifying namespace: ${APP_NS}"
                    kubectl get namespace ${APP_NS} || {
                        echo "❌ ERROR: Namespace ${APP_NS} not found!"
                        echo "Create it manually with: kubectl create namespace ${APP_NS}"
                        exit 1
                    }
                    echo "✅ Namespace ${APP_NS} exists"
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
                    microk8s.ctr --namespace k8s.io image rm ${IMAGE_NAME} || true
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
                    

                    echo "2️⃣ Deploying Webserver..."
                    # Update image in deployment
                    
                    sed "s|image:.*|image: ${IMAGE_NAME}|g" ${K8S_DIR}/webserver-deployment.yaml | kubectl apply -n ${APP_NS} -f -
                    kubectl apply -n ${APP_NS} -f ${K8S_DIR}/webserver-deployment.yaml
                    kubectl apply -n ${APP_NS} -f ${K8S_DIR}/webserver-service.yaml


                    

                   

                    echo "6️⃣ Waiting for Webserver rollout..."
                    kubectl rollout status deployment/webserver -n ${APP_NS} --timeout=180s

                   

                    echo "✅ All deployments complete!"
                """
            } 
        }
        stage('Print Commit Details') {
            steps {
                script {
            // Get all changes in this build
                    def changeLogSets = currentBuild.changeSets
                    for (int i = 0; i < changeLogSets.size(); i++) {
                        def entries = changeLogSets[i].items
                        for (int j = 0; j < entries.length; j++) {
                                def entry = entries[j]
                                echo "📝 Commit: [${entry.commitId.substring(0,7)}] by ${entry.author}: ${entry.msg}"
                        }
                    }    
                }
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
