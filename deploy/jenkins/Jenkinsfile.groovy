#!/usr/bin/env groovy

pipeline {
    agent any

    options {
        timeout(time: 1, unit: 'HOURS')
    }

    stages {
        stage('Initial checks') {
            steps {
                sh 'mkdir -p /tmp/pip-cache && chmod go+w /tmp/pip-cache'
            }
        }

        stage('Build wheel package') {
            steps {
                sh './deploy/scripts/build_wheel.sh'
            }
        }

        stage('Run unit tests') {
            parallel {
                stage('ubuntu16.04-py35') {
                    agent {
                        docker {
                            image 'mauvilsa/pagexml:runtime-ubuntu16.04-py35'
                            args '-v ${WORKSPACE}:/mnt -w /mnt -e HOME=/tmp -v /tmp/pip-cache:/tmp/pip-cache'
                            reuseNode true
                        }
                    }
                    steps {
                        sh './deploy/scripts/test_wheel.sh --venv venv_test-py35 --cache /tmp/pip-cache'
                    }
                }
                stage('ubuntu18.04-py36') {
                    agent {
                        docker {
                            image 'mauvilsa/pagexml:runtime-ubuntu18.04-py36'
                            args '-v ${WORKSPACE}:/mnt -w /mnt -e HOME=/tmp -v /tmp/pip-cache:/tmp/pip-cache'
                            reuseNode true
                        }
                    }
                    steps {
                        sh './deploy/scripts/test_wheel.sh --venv venv_test-py36 --cache /tmp/pip-cache'
                    }
                }
            }
        }

        stage('Push wheel package to pypi.omnius.com') {
            when { tag 'v*' }
            steps {
                sh 'twine upload --repository-url https://pypi.omnius.com --username jenkins --password "" dist/*.whl'
            }
        }
    }

    post {
        always {
          deleteDir()
        }
    }
}
