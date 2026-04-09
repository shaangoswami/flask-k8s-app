pipeline {
    agent any

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
           
            steps {
                echo 'Hello World'
            }
        }
        stage('Deploy') {
            steps {
                echo 'Deploying the project'
            }
        }
        
    }
}
