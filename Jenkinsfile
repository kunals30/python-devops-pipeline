
pipeline {
    agent any

    options {
        timestamps()
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
    }

    environment {
        APP_REPO = 'https://github.com/kunals30/python-devops-pipeline.git'
        GITOPS_REPO = 'git@github.com:kunals30/python-devops-gitops.git'
        GITOPS_BRANCH = 'main'

        NEXUS_REGISTRY = '10.0.1.212:8083'
        IMAGE_NAME = 'python-devops-api'
    }

    stages {

        // 1. Checkout application source code
        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: "${APP_REPO}"

                sh '''
                    echo "Application repository checked out"
                    git log -1 --oneline
                '''
            }
        }

        // 2. Set up Python environment
        stage('Setup Python') {
            steps {
                sh '''
                    set -eu

                    python3 --version
                    python3 -m venv .venv

                    .venv/bin/python -m pip install --upgrade pip
                    .venv/bin/python -m pip install \
                        -r requirements.txt \
                        -r requirements-dev.txt \
                        build

                    echo "Python environment ready"
                '''
            }
        }

        // 3. Build Python wheel
        stage('Build Wheel') {
            steps {
                sh '''
                    set -eu

                    rm -rf dist build
                    .venv/bin/python -m build --wheel --outdir dist

                    echo "Generated wheel:"
                    ls -lh dist/
                '''
            }
        }

        // 4. Unit tests and coverage
        stage('Unit Tests') {
            steps {
                sh '''
                    set -eu

                    .venv/bin/python -m pytest \
                        tests/test_unit.py \
                        --cov=app \
                        --cov-report=xml:coverage.xml \
                        --junitxml=unit-test-results.xml
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true,
                        testResults: 'unit-test-results.xml'
                }
            }
        }

        // 5. Functional tests
        stage('Functional Tests') {
            steps {
                sh '''
                    set -eu

                    .venv/bin/python -m pytest \
                        tests/test_functional.py \
                        --junitxml=functional-test-results.xml
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true,
                        testResults: 'functional-test-results.xml'
                }
            }
        }

        // 6. SonarQube static code analysis
        stage('SonarQube Analysis') {
            steps {
                script {
                    def scannerHome = tool 'SonarScanner'

                    withSonarQubeEnv('SonarQube') {
                        withCredentials([
                            string(
                                credentialsId: 'python-sonar-token',
                                variable: 'SONAR_TOKEN'
                            )
                        ]) {
                            withEnv([
                                "SCANNER_HOME=${scannerHome}"
                            ]) {
                                sh '''
                                    set -eu

                                    "$SCANNER_HOME/bin/sonar-scanner" \
                                        -Dsonar.token="$SONAR_TOKEN"
                                '''
                            }
                        }
                    }
                }
            }
        }

        // 7. Performance testing with Locust
        stage('Performance Tests') {
            steps {
                sh '''
                    set -eu

                    .venv/bin/uvicorn app.main:app \
                        --host 127.0.0.1 \
                        --port 8000 > app.log 2>&1 &

                    APP_PID=$!
                    trap 'kill "$APP_PID" 2>/dev/null || true' EXIT

                    READY=0

                    for i in $(seq 1 30); do
                        if curl -fsS \
                            http://127.0.0.1:8000/health \
                            >/dev/null; then
                            READY=1
                            break
                        fi

                        sleep 1
                    done

                    if [ "$READY" -ne 1 ]; then
                        echo "Application failed to start"
                        cat app.log
                        exit 1
                    fi

                    .venv/bin/locust \
                        -f performance/locustfile.py \
                        --headless \
                        --users 10 \
                        --spawn-rate 2 \
                        --run-time 30s \
                        --host http://127.0.0.1:8000 \
                        --html locust-report.html \
                        --csv locust-results

                    echo "Performance test completed"
                '''
            }
        }

        // 8. Archive reports and build artifacts
        stage('Archive Artifacts') {
            steps {
                archiveArtifacts(
                    artifacts: 'dist/*.whl,coverage.xml,*test-results.xml,locust-report.html,locust-results*.csv',
                    allowEmptyArchive: true
                )
            }
        }

        // 9. Build Docker image and push it to Nexus
        stage('Docker Build and Push') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'nexus-python-credentials',
                        usernameVariable: 'NEXUS_USER',
                        passwordVariable: 'NEXUS_PASSWORD'
                    )
                ]) {
                    sh '''
                        set -eu

                        IMAGE="${NEXUS_REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER}"

                        echo "$NEXUS_PASSWORD" | docker login \
                            "$NEXUS_REGISTRY" \
                            --username "$NEXUS_USER" \
                            --password-stdin

                        docker build -t "$IMAGE" .
                        docker push "$IMAGE"

                        docker logout "$NEXUS_REGISTRY"

                        echo "Successfully pushed: $IMAGE"
                    '''
                }
            }
        }

        // 10. Update the GitOps manifest and push to GitHub
        stage('Update GitOps Repository') {
            steps {
                withCredentials([
                    sshUserPrivateKey(
                        credentialsId: 'gitops-deploy-key',
                        keyFileVariable: 'GITOPS_SSH_KEY',
                        usernameVariable: 'GITOPS_SSH_USER'
                    )
                ]) {
                    sh '''
                        set -eu

                        export GIT_SSH_COMMAND="ssh -i ${GITOPS_SSH_KEY} -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"

                        rm -rf python-devops-gitops

                        git clone \
                            --branch "$GITOPS_BRANCH" \
                            "$GITOPS_REPO" \
                            python-devops-gitops

                        cd python-devops-gitops

                        git config user.name "Jenkins CI"
                        git config user.email "jenkins@localhost"

                        sed -E -i \
                            "s|(image: 10\\.0\\.1\\.212:8083/python-devops-api:).*|\\1${BUILD_NUMBER}|" \
                            apps/python-devops/deployment.yaml

                        echo "Deployment image after update:"
                        grep 'image:' apps/python-devops/deployment.yaml

                        git add apps/python-devops/deployment.yaml

                        if git diff --cached --quiet; then
                            echo "No GitOps changes to commit"
                        else
                            git commit \
                                -m "Deploy python-devops-api build ${BUILD_NUMBER}"

                            git push origin "$GITOPS_BRANCH"
                        fi

                        echo "GitOps repository update completed"
                    '''
                }
            }
        }
    }

    post {
        success {
            echo 'CI pipeline succeeded. The new image was pushed to Nexus and the GitOps repository was updated.'
            echo 'Argo CD should now detect the GitOps commit and synchronize the EKS deployment.'
        }

        failure {
            echo 'Pipeline failed. Check Console Output to identify the failing stage.'
        }

        always {
            echo "Pipeline finished for build ${BUILD_NUMBER}"
        }
    }
}
