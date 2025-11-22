pipeline {
    agent any

    environment {
        DOCKER_USERNAME       = '88tima'
        DOCKER_IMAGE_NAME     = 'case_change'
        DOCKER_IMAGE          = "${DOCKER_USERNAME}/${DOCKER_IMAGE_NAME}"
        TEST_CONTAINER_NAME   = "test-${env.DOCKER_IMAGE_NAME}"  
    }

    stages {
        stage('Build Docker Image') {
            steps {
                sh "docker build -t ${DOCKER_IMAGE} ."
            }
        }

        stage('Test Application') {
            steps {
                sh '''
                    docker run -d --name ${TEST_CONTAINER_NAME} -p 5001:5000 ${DOCKER_IMAGE}
                    sleep 5
                    if ! curl -s http://localhost:5001 | grep -q "Конвертер текста"; then
                        echo "❌ Тест провален: не найден заголовок 'Конвертер текста'"
                        docker logs ${TEST_CONTAINER_NAME}
                        exit 1
                    fi
                    echo "✅ Тест пройден: приложение отвечает корректно"
                    docker stop ${TEST_CONTAINER_NAME}
                    docker rm ${TEST_CONTAINER_NAME}
                '''
            }
        }

        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'docker-hub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_TOKEN'
                )]) {
                    sh '''
                        echo "$DOCKER_TOKEN" | docker login -u "$DOCKER_USER" --password-stdin
                        docker push $DOCKER_IMAGE
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "Pipeline completed successfully. Image pushed: ${env.DOCKER_IMAGE}"
        }
        failure {
            echo "Pipeline failed."
        }
        always {
            sh 'docker logout'
            sh "docker rm -f ${env.TEST_CONTAINER_NAME} || true"
        }
    }
}