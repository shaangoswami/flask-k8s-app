pipeline {
    agent any

    parameters {
        choice(name: 'VERSION', choices: ['1.1.0', '1.1.1'], description: 'Select version')
        booleanParam(name: 'EXECUTE_TESTS', defaultValue: false, description: 'Run tests?')
    }

    stages {
        stage('Build') {
            when {
                branch 'main'
            }
            steps {
                echo 'building the app'
            }
        }

        stage('Test') {
            when {
                expression {
                    return params.EXECUTE_TESTS
                }
            }
            steps {
                echo 'Running tests...'
            }
        }

        stage('Deploy') {
            steps {
                echo 'Deploying the project'
                echo "Deploying version ${params.VERSION}"
            }
        }
    }
}
