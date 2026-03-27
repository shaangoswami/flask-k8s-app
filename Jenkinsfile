pipeline {
    agent { label 'kubectl-agent' }
    
    triggers {
        githubPush()
    }
    
    options {
        timeout(time: 30, unit: 'MINUTES')
        githubProjectProperty(projectUrlStr: 'https://github.com/shaangoswami/flask-k8s-app')
        // Prevent concurrent builds of the same job
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
                    
                    // Update the commit ID in the HTML template
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
                        echo "🔐 Logging in to Docker Hub..."
                        echo "${DOCKERHUB_CREDENTIALS_PSW}" | docker login -u "${DOCKERHUB_CREDENTIALS_USR}" --password-stdin
                        echo "⬆️ Pushing image to Docker Hub..."
                        docker push ${IMAGE_NAME}
                        echo "✅ Image pushed: ${IMAGE_NAME}"
                        docker logout
                    """
                }
            }
        }
        
        stage('Pre-deployment Checks') {
            steps {
                script {
                    echo "🔍 Checking current cluster state..."
                    sh """
                        echo "=== Current Pods ==="
                        microk8s kubectl get pods -n ${APP_NS} -o wide
                        
                        echo ""
                        echo "=== Current ReplicaSets ==="
                        microk8s kubectl get rs -n ${APP_NS} -l app=webserver
                    """
                }
            }
        }
        
        stage('Pull Image to K8s Node') {
            steps {
                sh """
                    echo "⬇️ Pre-pulling image from Docker Hub into MicroK8s..."
                    microk8s.ctr --namespace k8s.io image pull docker.io/${IMAGE_NAME} || {
                        echo "⚠️ Image pull failed, will rely on node's image cache"
                    }
                    echo "✅ Image pre-pulled (or will be pulled on schedule)"
                """
            }
        }
        
        stage('Deploy to K8s') {
            steps {
                sh """
                    echo "🚀 Starting deployment of ${IMAGE_NAME}..."
                    
                    echo ""
                    echo "1️⃣ Setting deployment image..."
                    microk8s kubectl set image deployment/webserver webserver=docker.io/${IMAGE_NAME} -n ${APP_NS}
                    
                    echo ""
                    echo "2️⃣ Applying service configuration..."
                    microk8s kubectl apply -n ${APP_NS} -f ${K8S_DIR}/webserver-service.yaml
                    
                    echo ""
                    echo "3️⃣ Waiting for rollout to complete..."
                    # Use polling instead of direct rollout status for better reliability
                    timeout=180
                    elapsed=0
                    interval=5
                    
                    while [ \$elapsed -lt \$timeout ]; do
                        # Check if the deployment has the correct image
                        current_image=\$(microk8s kubectl get deployment webserver -n ${APP_NS} -o jsonpath='{.spec.template.spec.containers[0].image}')
                        available=\$(microk8s kubectl get deployment webserver -n ${APP_NS} -o jsonpath='{.status.availableReplicas}')
                        
                        echo "   Current image: \$current_image"
                        echo "   Available replicas: \$available"
                        
                        if [[ "\$current_image" == *"${COMMIT_ID}"* ]] && [[ "\$available" == "1" ]]; then
                            echo "✅ Deployment successful! Image updated and pod is available."
                            exit 0
                        fi
                        
                        # Check for failed pods
                        failed_pods=\$(microk8s kubectl get pods -n ${APP_NS} -l app=webserver --field-selector=status.phase!=Running -o jsonpath='{.items[*].metadata.name}')
                        if [ -n "\$failed_pods" ]; then
                            echo "⚠️ Found non-running pods: \$failed_pods"
                            microk8s kubectl describe pod \$failed_pods -n ${APP_NS} | tail -20
                        fi
                        
                        sleep \$interval
                        elapsed=\$((elapsed + interval))
                        echo "   Waiting... (\$elapsed/\$timeout seconds)"
                    done
                    
                    echo "❌ Rollout timed out after \$timeout seconds"
                    echo "=== Debug Information ==="
                    microk8s kubectl get pods -n ${APP_NS} -l app=webserver
                    microk8s kubectl describe deployment webserver -n ${APP_NS}
                    microk8s kubectl logs -n ${APP_NS} -l app=webserver --tail=30 || true
                    exit 1
                """
            }
        }
        
        stage('Verify Deployment') {
            steps {
                script {
                    echo "✅ Verifying deployment health..."
                    sh """
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
                echo "=== Deployment Description ==="
                microk8s kubectl describe deployment/webserver -n ${APP_NS} || true
                
                echo ""
                echo "=== Pod Events ==="
                microk8s kubectl get events -n ${APP_NS} --sort-by='.lastTimestamp' | tail -20 || true
                
                echo ""
                echo "=== Pod Logs ==="
                microk8s kubectl logs -n ${APP_NS} -l app=webserver --tail=50 || true
                
                echo ""
                echo "=== Node Status ==="
                microk8s kubectl get nodes -o wide || true
            """
        }
        success {
            echo "🎉 Deployment completed successfully!"
        }
    }
}

// pipeline { 
//     agent { label 'kubectl-agent' } 

//     triggers {
//         githubPush()
//     }
    
//     options {
//         timeout(time: 30, unit: 'MINUTES')
//         // GitHub project URL helps with webhook identifications
//         githubProjectProperty(projectUrlStr: 'https://github.com/shaangoswami/flask-k8s-app')
//     }
    
//     environment { 
//         K8S_DIR = "k8s" 
//         APP_NS = "flask-app"
//         IMAGE_NAME = "flask-webserver:v1"  // Removed space after colon
//         DOCKERFILE_DIR = "flaskServer/webserver"
//     } 
  
//     stages { 
//         stage('Checkout') { 
//             steps { 
//                 checkout scm
//                  } 
//         }
//         stage('Capture Commit ID') {
//             steps {
//                 script {
//                     def commitId = env.GIT_COMMIT
//                     sh """
//                         sed -i 's/__COMMIT_ID__/${commitId}/g' flaskServer/webserver/templates/index.html
//                     """
//                     }
//                 }
//         }
//         stage('Build') { 
//             agent { label 'jenkins-agent' }
            
//             steps { 
//                 container('docker') {
//                     dir(DOCKERFILE_DIR) {
//                         sh """  
//                         docker build -t ${IMAGE_NAME} .
//                     """
//                 }
//             }
//             } 
//         }

//         stage('Test') { 
//             agent { label 'jenkins-agent' }
//             steps { 
//                 container('docker') {
//                     sh """
//                         echo "🧪 Testing image..."
//                         docker run --rm ${IMAGE_NAME} python --version
//                         echo "✅ Python version check passed"
//                         echo "📦 Checking installed packages..."
//                         docker run --rm ${IMAGE_NAME} pip list | grep -i flask || echo "Flask package not found"
//                     """    
//                 }
//             } 
//         }

//         stage('Import to K8s') { 
            
//             steps { 
                
//                     sh """
//                         echo "⬆️ Importing to MicroK8s..."
//                     docker save ${IMAGE_NAME} -o /tmp/flask-image.tar
//                     microk8s.ctr --namespace k8s.io image rm ${IMAGE_NAME} || true
//                     microk8s.ctr --namespace k8s.io image import /tmp/flask-image.tar
//                     rm -f /tmp/flask-image.tar
                    
//                     echo "✅ Available images: "
//                     microk8s.ctr --namespace k8s.io images ls | grep flask-webserver
//                 """
//                 } 
            
//         }

//         stage('Deploy') { 
//             steps { 
//                 sh """
//                     echo "Verifying generated yaml" 
//                     sed "s|image:.*|image: ${IMAGE_NAME}|g" ${K8S_DIR}/webserver-deployment.yaml | kubectl apply -n ${APP_NS} -f -
                    
//                     echo "2️⃣ Deploying Webserver..."
//                     kubectl apply -n ${APP_NS} -f ${K8S_DIR}/webserver-deployment.yaml
//                     kubectl apply -n ${APP_NS} -f ${K8S_DIR}/webserver-service.yaml

//                     echo "3️⃣ Forcing cleanup of any 'ghost' or 'stuck' pods"
//                     # This deletes pods that are Terminating, Error, or ImagePullBackOff
//                     kubectl get pods -n flask-app | grep -v 'Running' | awk '{print \$1}' | xargs kubectl delete pod -n flask-app --force --grace-period=0 || true
                   
//                     echo "4️⃣ Monitoring Rollout (3-minute timeout)"
//                     if ! kubectl rollout status deployment/webserver -n flask-app --timeout=180s; then
//                         echo "❌ Rollout timed out! Forcing a restart..."
//                         kubectl rollout restart deployment/webserver -n flask-app
//                         exit 1
//                     fi
//                     echo "✅ All deployments complete!"
//                 """
//             } 
//         }
        
//         stage('Print Commit Details') {
//             steps {
//                 script {
//                     // Get all changes in this build
//                     def changeLogSets = currentBuild.changeSets
//                     for (int i = 0; i < changeLogSets.size(); i++) {
//                         def entries = changeLogSets[i].items
//                         for (int j = 0; j < entries.length; j++) {
//                             def entry = entries[j]
//                             echo "📝 Commit: [${entry.commitId.take(7)}] by ${entry.author}: ${entry.msg}"
//                         }
//                     }    
//                 }
//             }
//         }
//     } 
  
//     post { 
//         always { 
//             echo "📊 Deployment Status: "
//             sh """
//                 kubectl get pods -n ${APP_NS}
//                 echo ""
//                 kubectl get svc -n ${APP_NS}
//             """
//             sh "docker rmi ${IMAGE_NAME} 2>/dev/null || true"
//         }
//         failure {
//             echo "❌ Pipeline failed!"
//             sh """
//                 echo "=== Debug info ==="
//                 kubectl describe deployment/webserver -n ${APP_NS}
//                 echo ""
//                 kubectl logs -n ${APP_NS} deployment/webserver --tail=20
//             """
//         }
//     } 
// }
