apiVersion: v1
kind: Pod
metadata:
  labels:
    app: ms-qe-cluster-sanity-amq-streams-test
  name: ms-qe-cluster-sanity-amq-streams-test
  namespace: managed-services-integration
spec:
  containers:
  - command:
    - pipenv
    - run
    - pytest
    - --junitxml=/data/results/xunit_results.xml
    - --pytest-log-file=/data/results/pytest-tests.log
    - -s
    - -o
    - log_cli=true
    - -p
    - no:logging
    env:
    - name: KUBECONFIG
      value: /data/auth/kubeconfig
    - name: TEST_COLLECT_BASE_DIR
      value: /data/results
    - name: CNV_TEST_COLLECT_LOGS
      value: '1'
    image: quay.io/interop_qe_ms/ms-interop-tests:latest
    imagePullPolicy: Always
    name: cluster-sanity
    volumeMounts:
    - mountPath: /data/auth
      name: ms-interop-cluster-auth
    - mountPath: /data/results
      name: ms-interop-results-dir
  - command:
    - sh
    - -c
    - while true ; do echo ready ; sleep 30 ; done
    image: quay.io/prometheus/busybox
    name: rsync-container
    volumeMounts:
    - mountPath: /data/results/
      name: ms-interop-results-dir
  imagePullPolicy: Always
  imagePullSecrets:
  - name: ms-interop-quay-credentials
  restartPolicy: Never
  securityContext:
    privileged: true
  volumes:
  - configMap:
      name: ms-interop-cluster-auth
    name: ms-interop-cluster-auth
  - emptyDir: {}
    name: ms-interop-results-dir
  - emptyDir: {}
    name: setup-dir

