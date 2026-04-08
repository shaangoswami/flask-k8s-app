pipeline {
    agent { label 'kubectl-agent' }
    
    triggers {
        githubPush()
    }
    
    options {
        timeout(time: 30, unit: 'MINUTES')
        githubProjectProperty(projectUrlStr: 'https://github.com/shaangoswami/flask-k8s-app')
        disableConcurrentBuilds()
    }
    
    environment {
        PATH = "/snap/bin:${env.PATH}"
        K8S_DIR = "k8s"
        APP_NS = "flask-app"
        IMAGE_REPO = "shaangoswami/flask-webserver"
        DOCKERFILE_DIR = "flaskServer/webserver"
        PROXY_URL = credentials('proxy-url')
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-creds')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Capture Commit ID') {
            steps {
                script {
                    env.COMMIT_ID = env.GIT_COMMIT.take(7)
                    env.IMAGE_NAME = "${env.IMAGE_REPO}:${env.COMMIT_ID}"
                    echo "🏷️ Image will be tagged as: ${env.IMAGE_NAME}"
                    
                    sh """
                        sed -i 's/__COMMIT_ID__/${env.COMMIT_ID}/g' flaskServer/webserver/templates/index.html
                    """
                }
            }
        }
        
        stage('Build') {
            agent {
                kubernetes {
                    inheritFrom 'docker-agent-v2'
                }
            }
            steps {
                container('jnlp') {
                    dir(DOCKERFILE_DIR) {
                        sh """
                            export DOCKER_BUILDKIT=0
                            docker build --network=host \
                                --build-arg HTTP_PROXY=${PROXY_URL} \
                                --build-arg HTTPS_PROXY=${PROXY_URL} \
                                -t ${IMAGE_NAME} .
                        """
                    }
                }
            }
        }
        
        stage('Test') {
            agent {
                kubernetes {
                    inheritFrom 'docker-agent-v2'
                }
            }
            steps {
                container('jnlp') {
                    sh """
                        echo "🧪 Testing image..."
                        docker run --rm ${IMAGE_NAME} python --version
                        echo "✅ Python version check passed"
                        echo "📦 Checking installed packages..."
                        docker run --rm ${IMAGE_NAME} pip list | grep -i flask || echo "Flask package not found"
                    """
                }
            }
        }
        
        stage('Push to Docker Hub') {
            agent {
                kubernetes {
                    inheritFrom 'docker-agent-v2'
                }
            }
            steps {
                container('jnlp') {
                    sh """
                        set -e
                        echo "🔐 Logging in to Docker Hub..."
                        echo "${DOCKERHUB_CREDENTIALS_PSW}" | docker login -u "${DOCKERHUB_CREDENTIALS_USR}" --password-stdin
                        
                        echo "⬆️ Pushing image to Docker Hub..."
                        docker push ${IMAGE_NAME}
                        
                        docker manifest inspect ${IMAGE_NAME} > /dev/null || {
                            echo "❌ Image push failed!"
                            exit 1
                        }
                        
                        echo "✅ Image pushed: ${IMAGE_NAME}"
                        docker logout
                    """
                }
            }
        }
        
        stage('Pre-deployment Checks') {
            steps {
                sh """
                    echo "🔍 Checking current cluster state..."
                    
                    echo "=== Current Pods ==="
                    microk8s kubectl get pods -n ${APP_NS} -o wide
                    
                    echo ""
                    echo "=== Current ReplicaSets ==="
                    microk8s kubectl get rs -n ${APP_NS} -l app=webserver
                """
            }
        }
        
        stage('Deploy to K8s') {
            steps {
                sh """
                    echo "🚀 Deploying ${IMAGE_NAME}..."
        
                    echo "📦 Applying deployment..."
                    microk8s kubectl apply -n ${APP_NS} -f ${K8S_DIR}/webserver-deployment.yaml
        
                    echo "📦 Applying service..."
                    microk8s kubectl apply -n ${APP_NS} -f ${K8S_DIR}/webserver-service.yaml
        
                    echo "🔄 Updating image..."
                    microk8s kubectl set image deployment/webserver \
                      webserver=${IMAGE_NAME} -n ${APP_NS}
        
                    echo "⏳ Waiting for rollout..."
                    microk8s kubectl rollout status deployment/webserver -n ${APP_NS} --timeout=180s
        
                    echo "📍 Pod placement:"
                    microk8s kubectl get pods -o wide -n ${APP_NS}
                """
            }
        }
        
        stage('Verify Deployment') {
            steps {
                sh """
                    echo "✅ Verifying deployment health..."
                    
                    echo "=== Pod Status ==="
                    microk8s kubectl get pods -n ${APP_NS} -l app=webserver -o wide
                    
                    echo ""
                    echo "=== Pod Logs ==="
                    microk8s kubectl logs -n ${APP_NS} -l app=webserver --tail=10
                    
                    echo ""
                    echo "=== Deployment Details ==="
                    microk8s kubectl get deployment webserver -n ${APP_NS}
                    
                    echo ""
                    echo "=== Service Details ==="
                    microk8s kubectl get svc -n ${APP_NS}
                """
            }
        }
        
        stage('Print Commit Details') {
            steps {
                script {
                    def changeLogSets = currentBuild.changeSets
                    for (int i = 0; i < changeLogSets.size(); i++) {
                        def entries = changeLogSets[i].items
                        for (int j = 0; j < entries.length; j++) {
                            def entry = entries[j]
                            echo "📝 Commit: [${entry.commitId.take(7)}] by ${entry.author}: ${entry.msg}"
                        }
                    }
                }
            }
        }
    }
    
    post {
        always {
            echo "📊 Final Deployment Status:"
            sh """
                microk8s kubectl get pods -n ${APP_NS} || true
                echo ""
                microk8s kubectl get svc -n ${APP_NS} || true
                echo ""
                microk8s kubectl get endpoints -n ${APP_NS} || true
            """
        }
        
        failure {
            echo "❌ Pipeline failed! Collecting debug information..."
            sh """
                echo "=== POD STATUS ==="
                microk8s kubectl get pods -n ${APP_NS} -o wide
                
                echo ""
                echo "=== EVENTS ==="
                microk8s kubectl get events -n ${APP_NS} --sort-by='.lastTimestamp' | tail -20
                
                echo ""
                echo "=== DESCRIBE POD ==="
                microk8s kubectl describe pod -n ${APP_NS} -l app=webserver
                
                echo ""
                echo "=== LOGS ==="
                microk8s kubectl logs -n ${APP_NS} -l app=webserver --tail=50 || true
                
                echo ""
                echo "=== NODE STATUS ==="
                microk8s kubectl get nodes -o wide || true
            """
        }
        
        success {
            echo "🎉 Deployment completed successfully!"
        }
    }
}
