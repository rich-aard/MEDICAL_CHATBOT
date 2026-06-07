pipeline {
    agent any

    options {
        timeout(time: 20, unit: 'MINUTES') 
    }

    environment {
        REGISTRY_CREDS_ID = 'docker-token' 
        REGISTRY_USER     = 'thefool23'              
        IMAGE_NAME        = 'medical-chatbot'
        IMAGE_TAG         = "${BUILD_NUMBER}"  
        DOCKER_BUILDKIT   = '1'      
    }

    stages {
        stage('Checkout Code') {
            steps {
                echo 'Fetching the latest source code from GitHub...'
                checkout scmGit(
                    branches: [[name: '*/main']], 
                    extensions: [], 
                    userRemoteConfigs: [[credentialsId: 'github-token', url: 'https://github.com/rich-aard/MEDICAL_CHATBOT.git']]
                )
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "Compiling application image: ${REGISTRY_USER}/${IMAGE_NAME}:${IMAGE_TAG}"
                sh "docker build -t ${REGISTRY_USER}/${IMAGE_NAME}:${IMAGE_TAG} ."
                sh "docker tag ${REGISTRY_USER}/${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY_USER}/${IMAGE_NAME}:latest"
            }
        }

        stage('Push to Container Registry') {
            steps {
                echo 'Authenticating and pushing artifacts to Docker Hub...'
                withCredentials([usernamePassword(credentialsId: "${REGISTRY_CREDS_ID}", usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh 'echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin'
                    sh "docker push ${REGISTRY_USER}/${IMAGE_NAME}:${IMAGE_TAG}"
                    sh "docker push ${REGISTRY_USER}/${IMAGE_NAME}:latest"
                }
            } 
        }

        stage('Workspace Cleanup') {
            steps {
                echo 'Cleaning up intermediate local images...'
                sh "docker rmi ${REGISTRY_USER}/${IMAGE_NAME}:${IMAGE_TAG} || true"
            }
        }
    }

    post {
        success {
            echo "Build #${BUILD_NUMBER} compiled and pushed successfully!"
        }
        failure {
            echo "Pipeline failed at build #${BUILD_NUMBER}."
        }
    }
}