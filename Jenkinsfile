pipeline {
    agent any

    stages {
        stage('Build and Run') {
            steps {
                sh 'docker compose up -d --build'
            }
        }
    }
}
