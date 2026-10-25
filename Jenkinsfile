
pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/kunals30/python-devops-pipeline.git'
            }
        }

        stage('Setup Python') {
            steps {
                sh '''
                    python3 -m venv .venv
                    .venv/bin/python -m pip install --upgrade pip
                    .venv/bin/python -m pip install -r requirements-dev.txt
                '''
            }
        }

        stage('Build Wheel') {
            steps {
                sh '''
                    .venv/bin/python -m build --wheel
                    ls -lh dist/
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                sh '''
                    .venv/bin/python -m pytest tests/test_unit.py \
                        --junitxml=reports/unit-results.xml \
                        --cov=app \
                        --cov-report=xml:reports/coverage.xml \
                        --cov-report=term
                '''
            }
        }

        stage('Functional Tests') {
            steps {
                sh '''
                    .venv/bin/python -m pytest tests/test_functional.py \
                        --junitxml=reports/functional-results.xml
                '''
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true,
                testResults: 'reports/*-results.xml'

            archiveArtifacts artifacts: 'dist/*.whl',
                allowEmptyArchive: true

            archiveArtifacts artifacts: 'reports/coverage.xml',
                allowEmptyArchive: true

            cleanWs()
        }
    }
}
