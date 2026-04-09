pipeline {
    agent any
    parameters {
        choice(name: 'VERSION', choices : ['1.1.0', '1.1.1'], description: '')
        booleanParam(name: 'VERSION', defaultValue: false, description: '')
    }
    stages {
        stage('Build') {
             when {
                expression {
                    return env.BRANCH_NAME == 'main'
                }
            }
            steps {
                echo 'building the app'
            }
        }
        stage('Test') {
           when {
               expression {
                   params.executeTests
               }
           }   
            steps {
                echo 'Hello World'
            }
        }
        stage('Deploy') {
            steps {
                echo 'Deploying the project'
                echo "deploying ${params.VERSION}"
                }
            }
        }
        
    }
}
