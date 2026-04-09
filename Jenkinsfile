CODE_CHANGES = getGitChanges()
pipeline {
    agent any

    stages {
        stage('Build') {
             when {
                expression {
                    BRANCH_NAME == 'main' && CODE_CHANGES == true
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
