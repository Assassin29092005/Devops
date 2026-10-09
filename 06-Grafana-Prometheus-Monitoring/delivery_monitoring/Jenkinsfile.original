pipeline {
    agent any
    stages {
        stage('Pre-check Docker') {
            steps {
                script {
                    try {
                        // Check if Docker is installed
                        def dockerVersion = sh(script: 'docker --version', returnStdout: true).trim()
                        if (!dockerVersion) {
                            error "Docker is not installed or not in the PATH. Please install Docker."
                        }

                        // Check if Docker daemon is running
                        def dockerInfo = sh(script: 'docker info', returnStatus: true)
                        if (dockerInfo != 0) {
                            error "Docker daemon is not running. Please start the Docker service."
                        }

                        echo "Docker is available and running: ${dockerVersion}"
                    } catch (Exception e) {
                        error "Pre-check failed: ${e.message}"
                    }
                }
            }
        }
        stage('Setup Workspace') {
            steps {
                script {
                    // Define the local source path where the files are located
                    def localSourcePath = '/path/to/your/local/files' // Replace with your actual path
                    def workspacePath = env.WORKSPACE

                    // Copy necessary files into the Jenkins workspace
                    sh """
                    cp ${localSourcePath}/delivery_metrics.py ${workspacePath}/
                    cp ${localSourcePath}/prometheus.yml ${workspacePath}/
                    cp ${localSourcePath}/alert_rules.yml ${workspacePath}/
                    """
                }
            }
        }
        stage('Build Docker Image') {
            steps {
                sh 'docker build -t delivery_metrics .'
            }
        }
        stage('Run Application') {
            steps {
                sh 'docker run -d -p 8000:8000 --name delivery_metrics delivery_metrics'
            }
        }
        stage('Run Prometheus & Grafana') {
            steps {
                sh '''
                docker run -d --name prometheus -p 9090:9090 \
                  -v $WORKSPACE/prometheus.yml:/etc/prometheus/prometheus.yml \
                  -v $WORKSPACE/alert_rules.yml:/etc/prometheus/alert_rules.yml \
                  prom/prometheus
                docker run -d --name grafana -p 3000:3000 grafana/grafana
                '''
            }
        }
    }
}
