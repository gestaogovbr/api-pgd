pipeline {

    environment {
       CATTLE_ACCESS_KEY = credentials('cattle-access-key')
       CATTLE_SECRET_KEY = credentials('cattle-secret-key')
       RANCHER_SERVICE = '1s5507'
    }

    agent any

    stages {
        stage('Checkout'){
            steps{
               checkout([$class: 'GitSCM',
                    branches: [[name: '*/main']],
                    doGenerateSubmoduleConfigurations: false,
                    extensions: [], submoduleCfg: [],
                    userRemoteConfigs: [[url: 'https://github.com/economiagovbr/api-pgd.git']]])
                sh 'ls'
                sh 'pwd'
            }
        }
        stage('Build') {
            steps {
                    echo 'Building..'
                    sh 'pwd'
                    sh 'docker build --rm -f "Dockerfile" -t registry.docker.planejamento.gov.br/seges-cginf/api-pgd:latest .'
            }
        }
        stage('Push image') {
            steps {
                echo 'Pushing....'
                    withDockerRegistry(credentialsId: '15', url: 'http://registry.docker.planejamento.gov.br') {
                        sh 'docker push registry.docker.planejamento.gov.br/seges-cginf/api-pgd:latest'
                }
            }
        }
        stage('Upgrade image') {
            steps {
                echo 'upgrading image on rancher...'
                sh '''#!/bin/bash
                    url="https://rancher.dev.economia.gov.br/v2-beta/projects/1a656207/services/${RANCHER_SERVICE}/?action=upgrade"

                    echo "Atualizando as imagens no Rancher..."

                    echo "URL: $url\n"

                    curl -o response.json \
                    -s \
                    -w "%{http_code}\n" \
                    -u "${CATTLE_ACCESS_KEY}:${CATTLE_SECRET_KEY}" \
                    -X POST \
                    -H 'Accept: application/json' \
                    -H 'Content-Type: application/json' \
                    -d '{"inServiceStrategy":{"batchSize":1, "intervalMillis":2000, "startFirst":false, "launchConfig":{"instanceTriggeredStop":"stop", "kind":"container", "networkMode":"managed", "privileged":false, "publishAllPorts":false, "readOnly":false, "runInit":false, "startOnCreate":true, "stdinOpen":true, "tty":true, "vcpu":1, "drainTimeoutMs":0, "type":"launchConfig", "blkioWeight":null, "capAdd":[], "capDrop":[], "cgroupParent":null, "command":["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "5057"], "count":null, "cpuCount":null, "cpuPercent":null, "cpuPeriod":null, "cpuQuota":null, "cpuRealtimePeriod":null, "cpuRealtimeRuntime":null, "cpuSet":null, "cpuSetMems":null, "cpuShares":null, "dataVolumes":[], "dataVolumesFrom":[], "description":null, "devices":[], "diskQuota":null, "dns":[], "dnsSearch":[], "domainName":null, "healthInterval":null, "healthRetries":null, "healthTimeout":null, "hostname":null, "imageUuid":"docker:registry.docker.planejamento.gov.br/seges-cginf/api-pgd:latest", "ioMaximumBandwidth":null, "ioMaximumIOps":null, "ip":null, "ip6":null, "ipcMode":null, "isolation":null, "kernelMemory":null, "labels":{"io.rancher.container.pull_image":"always", "io.rancher.container.hostname_override":"container_name"}, "logConfig":{"type":"logConfig", "config":{}, "driver":null}, "memory":null, "memoryMb":null, "memoryReservation":null, "memorySwap":null, "memorySwappiness":null, "milliCpuReservation":null, "oomScoreAdj":null, "pidMode":null, "pidsLimit":null, "ports":["5057:5057/tcp"], "requestedHostId":"1h182", "requestedIpAddress":null, "secrets":[], "shmSize":null, "stopSignal":null, "stopTimeout":null, "system":false, "user":null, "userdata":null, "usernsMode":null, "uts":null, "version":"f297dbd7-a635-43ba-a726-2176b3210055", "volumeDriver":null, "workingDir":null, "dataVolumesFromLaunchConfigs":[], "networkLaunchConfig":null, "createIndex":null, "created":null, "deploymentUnitUuid":null, "externalId":null, "firstRunning":null, "healthState":null, "removed":null, "startCount":null, "uuid":null}, "secondaryLaunchConfigs":[]}, "toServiceStrategy":null}' \
                    $url \
                    | tee /dev/stderr | xargs -I{} test '202' = '{}'

                    error_level=$?

                    if [ $error_level != 0 ];
                    then
                        echo "Requisição ao rancher falhou.\n\n";
                    fi

                    echo "Resposta do Rancher:\n\n"
                    cat response.json
                    rm response.json

                    exit $error_level
                   '''
            }
        }
         stage('Finish upgrade') {
            steps {
                  echo 'Finish upgrade image on rancher...'
                  sh 'sleep 50'
                  sh '''#!/bin/bash
                        url="https://rancher.dev.economia.gov.br/v2-beta/projects/1a656207/services/${RANCHER_SERVICE}/?action=finishupgrade"

                        echo "Disparando finish upgrade no Rancher..."

                        echo "URL: $url\n"

                        curl
                        -o response.json \
                        -s \
                        -w "%{http_code}\n" \
                        -u "${CATTLE_ACCESS_KEY}:${CATTLE_SECRET_KEY}" \
                        -X POST \
                        -H 'Accept: application/json' \
                        -H 'Content-Type: application/json' \
                        -d '{}' \
                        $url \
                        | tee /dev/stderr | xargs -I{} test '202' = '{}'

                        error_level=$?

                        if [ $error_level != 0 ];
                        then
                            echo "Requisição ao rancher falhou.\n\n";
                        fi

                        echo "Resposta do Rancher:\n\n"
                        cat response.json
                        rm response.json

                        exit $error_level
                    '''


            }
         }
    }
}

