
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
                    set -eu
                    python3 -m venv .venv
                    .venv/bin/python -m pip install --upgrade pip
                    .venv/bin/python -m pip install -r requirements-dev.txt
                    mkdir -p reports
                '''
            }
        }

        stage('Build Wheel') {
            steps {
                sh '''
                    set -eu
                    .venv/bin/python -m build --wheel
                    ls -lh dist/
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                sh '''
                    set -eu
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
                    set -eu
                    .venv/bin/python -m pytest tests/test_functional.py \
                        --junitxml=reports/functional-results.xml
                '''
            }
        }

        stage('SonarQube Analysis') {
            steps {
                script {
                    def scannerHome = tool 'SonarScanner'

                    withCredentials([
                        string(
                            credentialsId: 'python-sonar-token',
                            variable: 'SONAR_TOKEN'
                        )
                    ]) {
                        withSonarQubeEnv('SonarQube') {
                            sh '''
                                set -eu
                                "$SONAR_SCANNER_HOME/bin/sonar-scanner" \
                                    -Dsonar.token="$SONAR_TOKEN"
                            '''
                        }
                    }
                }
            }
        }

        stage('Performance Tests') {
            steps {
                sh '''
                    set -eu
                    mkdir -p reports

                    .venv/bin/uvicorn app.main:app \
                        --host 127.0.0.1 \
                        --port 8000 \
                        > reports/uvicorn.log 2>&1 &

                    APP_PID=$!
                    trap 'kill "$APP_PID" 2>/dev/null || true' EXIT

                    .venv/bin/python - <<'PY'
import time
import urllib.request

url = "http://127.0.0.1:8000/health"

for attempt in range(30):
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            if response.status == 200:
                print("Application is ready")
                break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit(
        "Application failed to start; check reports/uvicorn.log"
    )
PY

                    .venv/bin/locust \
                        -f performance/locustfile.py \
                        --headless \
                        --host http://127.0.0.1:8000 \
                        --users 10 \
                        --spawn-rate 2 \
                        --run-time 30s \
                        --csv reports/locust \
                        --html reports/locust-report.html
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

            archiveArtifacts artifacts: 'reports/locust*',
                allowEmptyArchive: true

            archiveArtifacts artifacts: 'reports/uvicorn.log',
                allowEmptyArchive: true

            cleanWs()
        }
    }
}
