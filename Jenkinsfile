def dockerFileToUseForBuild = 'Dockerfile.defaultbuild'
def PROJECT_INFO = [:]
def HAS_POE = false
def AVAILABLE_POE_TASKS = []
def IS_LOCAL_VERSION = false
def IS_PRERELEASE = false

pipeline {
    agent none
    options {
        buildDiscarder(
            logRotator(
                numToKeepStr: '100',
                artifactNumToKeepStr: '50'
            )
        )
    }
    parameters {
        string(name: 'GIT_LOCATION', description: 'location of project to build')
        string(name: 'GIT_BRANCH', defaultValue: 'main', description: 'branch of project to build')
        string(name: 'GIT_CREDS_ID', description: 'creds ID to use to pull project from remote')
        choice(name: 'TEST', description: 'how to run tests', choices: ['run', 'run but ignore result', 'skip'])
        booleanParam(name: 'BUILD', defaultValue: true, description: 'build the package')
        booleanParam(name: 'PYPI_RELEASE', defaultValue: true, description: 'release to PyPI')
        string(name: 'PYPI_SERVER', description: 'what PyPI server to release to; if empty, use the regular public PyPI')
        string(name: 'PYPI_CREDS_ID', description: 'creds ID to use to release project to PyPI')
        booleanParam(name: 'GITHUB_RELEASE', defaultValue: true, description: 'release to GitHub')
        text(name: 'RELEASE_NOTES', description: 'custom release notes (if empty, generate release notes)')
    }
    stages {
        stage('Checkout') {
            agent any
            steps {
                checkout(
                    [
                        $class: 'GitSCM',
                        branches: [
                            [
                                name: params.GIT_BRANCH
                            ]
                        ],
                        doGenerateSubmoduleConfigurations: false,
                        extensions: [
                            [
                                $class: 'RelativeTargetDirectory',
                                relativeTargetDir: '_project'
                            ]
                        ],
                        submoduleCfg: [],
                        userRemoteConfigs: [
                            [
                                credentialsId: params.GIT_CREDS_ID,
                                url: params.GIT_LOCATION
                            ]
                        ]
                    ]
                )
                stash(
                    name: 'source',
                    includes: '_project/**',
                    useDefaultExcludes: false
                )
            }
            post {
                cleanup {
                    cleanWs()
                }
            }
        }
        stage('Set vars') {
            agent {
                dockerfile {
                    filename "${dockerFileToUseForBuild}"
                    label 'hasdocker'
                }
            }
            steps {
                unstash('source')
                script {
                    def customDockerfileDotBuild = '_project/cicd/Dockerfile.build'
                    if (fileExists(customDockerfileDotBuild)) {
                        dockerFileToUseForBuild = customDockerfileDotBuild
                    }
                    else {
                        echo 'Defaulting to Dockerfile.defaultbuild for use in future stages'
                    }
                    dir('_project') {
                        if (!fileExists('.git')) {
                            sh(
                                script: 'git init > /dev/null',
                                label: 'Get back git info'
                            )
                        }
                        PROJECT_INFO = readJSON(
                            text: sh(
                                script: '''python -c 'from toml import load; from json import dumps; print(dumps(load("pyproject.toml")))' ''',
                                label: 'Get project info',
                                returnStdout: true
                            )
                        )
                        env.PROJECT_NAME = PROJECT_INFO['tool']['poetry']['name']
                        def gitCommit = sh(
                            script: 'git rev-parse --short HEAD',
                            returnStdout: true
                        ).trim()
                        currentBuild.displayName = "$env.PROJECT_NAME $gitCommit"
                    }
                }
            }
            post {
                failure {
                    cleanWs()
                }
                aborted {
                    cleanWs()
                }
            }
        }
        stage('Test, build, release') {
            agent {
                dockerfile {
                    filename "${dockerFileToUseForBuild}"
                    label 'hasdocker'
                }
            }
            stages {
                stage('Install') {
                    steps {
                        dir('_project') {
                            sh(
                                script: 'poetry install',
                                label: 'Install dependencies'
                            )
                        }
                    }
                }
                stage('Check for poe') {
                    steps {
                        script {
                            dir('_project') {
                                def rc = sh(
                                    script: 'poe -h > /dev/null 2>&1',
                                    returnStatus: true,
                                    label: 'Check for poe'
                                )
                                if (rc == 0) {
                                    HAS_POE = true
                                }
                                if (HAS_POE) {
                                    def out = sh(
                                        script: 'poe -h',
                                        label: 'Get tasks',
                                        returnStdout: true
                                    ).split('CONFIGURED TASKS', 2)
                                    if (out.size() != 1) {
                                        AVAILABLE_POE_TASKS = out[1].trim().split('\n').collect { it.trim() }
                                    }
                                }
                            }
                        }
                    }
                }
                stage('Test') {
                    when {
                        expression {
                            params.TEST != 'skip'
                        }
                    }
                    steps {
                        script {
                            def testsToRun = true
                            def testScript
                            if ('test' in AVAILABLE_POE_TASKS) {
                                testScript = 'poe test'
                            }
                            else {
                                if (fileExists('_project/tests')) {
                                    testScript = 'pytest -vv'
                                }
                                else {
                                    testsToRun = false
                                }
                            }
                            if (testsToRun) {
                                def rc
                                dir('_project') {
                                    testReportFile = "${currentBuild.displayName.replace(' ', '-')}_testreport.txt"
                                    withEnv(
                                        [
                                            "TEST_SCRIPT=$testScript",
                                            "TEST_REPORT_FILE=../$testReportFile"
                                        ]
                                    ) {
                                        rc = sh(
                                            script: '''
                                                #!/bin/bash
                                                $TEST_SCRIPT | tee $TEST_REPORT_FILE ; exit ${PIPESTATUS[0]}
                                            '''.stripIndent().trim(),
                                            returnStatus: true,
                                            label: 'Run tests'
                                        )
                                    }
                                }
                                archiveArtifacts(
                                    artifacts: testReportFile,
                                    allowEmptyArchive: false,
                                    fingerprint: true,
                                )
                                if (rc != 0) {
                                    def errorString = "Tests exited with exit code $rc"
                                    if (params.TEST != 'run but ignore result') {
                                        error(errorString)
                                    }
                                    else {
                                        unstable(errorString)
                                    }
                                }
                            }
                            else {
                                catchError(buildResult: 'SUCCESS', stageResult: 'NOT_BUILT') {
                                    error('No tests to run')
                                }
                            }
                        }
                    }
                }
                stage('Build') {
                    when {
                        expression {
                            params.BUILD
                        }
                    }
                    steps {
                        script {
                            if ('build' in AVAILABLE_POE_TASKS) {
                                buildScript = 'poe build'
                            }
                            else {
                                buildScript = 'poetry build'
                            }
                            dir('_project') {
                                sh(
                                    script: 'poetry build',
                                    label: 'Run build'
                                )
                                archiveArtifacts(
                                    artifacts: 'dist/*',
                                    allowEmptyArchive: false,
                                    fingerprint: true,
                                    onlyIfSuccessful: true
                                )
                            }
                        }
                    }
                }
                stage('Get version info') {
                    when {
                        expression {
                            params.BUILD
                        }
                    }
                    steps {
                        script {
                            dir('_project') {
                                def out = readJSON(
                                    text: sh(
                                        script: 'python ../get_version_info.py',
                                        returnStdout: true
                                    )
                                )
                                env.VERSION = out['version']
                                IS_LOCAL_VERSION = out['local']
                                IS_PRERELEASE = out['prerelease']
                                if (IS_LOCAL_VERSION) {
                                    echo 'This package has a local component to its version'
                                }
                                if (IS_PRERELEASE) {
                                    echo 'This package is a prerelease'
                                }
                            }
                            currentBuild.displayName = "$env.PROJECT_NAME $env.VERSION"
                        }
                    }
                }
                stage('PyPI release') {
                    when {
                        expression {
                            params.BUILD && params.PYPI_RELEASE && !IS_LOCAL_VERSION
                        }
                    }
                    environment {
                        REPO_URL = "${params.PYPI_SERVER}"
                    }
                    steps {
                        script {
                            dir('_project') {
                                withCredentials(
                                    [
                                        usernamePassword(
                                            credentialsId: params.PYPI_CREDS_ID,
                                            usernameVariable: 'REPO_USERNAME',
                                            passwordVariable: 'REPO_PASSWORD'
                                        )
                                    ]
                                ) {
                                    if (params.PYPI_SERVER) {
                                        sh '''
                                            poetry config repositories.repo $REPO_URL
                                            poetry config http-basic.repo $REPO_USERNAME $REPO_PASSWORD
                                            poetry publish -r repo
                                        '''
                                        label: 'Upload to PyPI server'
                                    }
                                    else {
                                        sh '''
                                            poetry config http-basic.pypi $REPO_USERNAME $REPO_PASSWORD
                                            poetry publish
                                        '''
                                        label: 'Upload to PyPI server'
                                    }
                                }
                            }
                        }
                    }
                }
                stage('GitHub release') {
                    when {
                        expression {
                            params.GITHUB_RELEASE
                        }
                    }
                    environment {
                        RELEASE_NOTES = "${params.RELEASE_NOTES}"
                        BRANCH = "${params.GIT_BRANCH}"
                    }
                    steps {
                        script {
                            if ('release-gh' in AVAILABLE_POE_TASKS) {
                                releaseScript = 'poe release-gh'
                            }
                            else {
                                releaseScript = 'gh release create "v$VERSION" --target "$BRANCH"'
                                if (env.RELEASE_NOTES) {
                                    releaseScript += ' --notes "$RELEASE_NOTES"'
                                }
                                else {
                                    releaseScript += ' --generate-notes'
                                }
                                if (IS_PRERELEASE) {
                                    releaseScript += ' -p'
                                }
                            }
                            if (params.BUILD) {
                                releaseScript = "$releaseScript dist/*$VERSION*"
                            }
                            dir('_project') {
                                withCredentials(
                                    [
                                        usernamePassword(
                                            credentialsId: params.GIT_CREDS_ID,
                                            usernameVariable: 'GITHUB_USERNAME',
                                            passwordVariable: 'GH_TOKEN'
                                        )
                                    ]
                                ) {
                                    sh(
                                        script: releaseScript,
                                        label: 'Create new release on GitHub'
                                    )
                                }
                            }
                        }
                    }
                }
            }
            post {
                cleanup {
                    cleanWs()
                }
            }
        }
    }
}
