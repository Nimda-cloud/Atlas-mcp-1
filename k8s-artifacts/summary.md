# Atlas MCP Kubernetes Deployment Summary

**Cluster:** atlas-mcp-ci-test
**Namespace:** atlas-mcp-dev
**Timestamp:** Mon Aug 25 02:01:33 EEST 2025

## Deployment Status

```
NAME             READY   UP-TO-DATE   AVAILABLE   AGE
atlas-core       0/2     2            0           5m28s
atlas-frontend   0/3     3            0           5m28s
grafana          0/1     1            0           5m28s
mcp-automation   0/2     2            0           5m28s
mcp-automator    0/2     2            0           5m28s
mcp-playwright   0/2     2            0           5m28s
mcp-tts          0/2     2            0           5m28s
ollama           0/1     1            0           5m28s
prometheus       0/1     1            0           5m28s
qdrant           1/1     1            1           5m28s
redis            1/1     1            1           5m28s
redis-exporter   1/1     1            1           5m28s
```

## Service Status

```
NAME                     TYPE           CLUSTER-IP       EXTERNAL-IP            PORT(S)             AGE
atlas-core-service       ClusterIP      10.108.30.34     <none>                 8000/TCP            5m29s
atlas-frontend-service   ClusterIP      10.99.69.233     <none>                 8080/TCP            5m29s
grafana-service          ClusterIP      10.109.78.3      <none>                 3000/TCP            5m29s
mcp-automation-service   ClusterIP      10.101.201.162   <none>                 4002/TCP            5m29s
mcp-automator-service    ClusterIP      10.107.169.169   <none>                 4003/TCP            5m29s
mcp-playwright-service   ClusterIP      10.99.26.36      <none>                 4005/TCP            5m29s
mcp-tts-service          ClusterIP      10.110.34.55     <none>                 4004/TCP            5m28s
ollama-host              ExternalName   <none>           host.docker.internal   11434/TCP           5m28s
ollama-host-service      ClusterIP      None             <none>                 11434/TCP           5m28s
ollama-service           ClusterIP      10.111.223.62    <none>                 11434/TCP           5m28s
prometheus-service       ClusterIP      10.105.202.214   <none>                 9090/TCP            5m28s
qdrant-service           ClusterIP      10.109.86.184    <none>                 6333/TCP,6334/TCP   5m28s
redis-exporter-service   ClusterIP      10.102.237.227   <none>                 9121/TCP            5m28s
redis-service            ClusterIP      10.106.196.189   <none>                 6379/TCP            5m28s
```

## Pod Status

```
NAME                              READY   STATUS              RESTARTS      AGE
atlas-core-6dbf5bf65c-nbc47       0/1     ErrImageNeverPull   0             5m13s
atlas-core-6dbf5bf65c-rct6d       0/1     ErrImageNeverPull   0             5m28s
atlas-frontend-58ccd575fd-9t7k6   0/1     ErrImageNeverPull   0             5m28s
atlas-frontend-58ccd575fd-bgcbl   0/1     ErrImageNeverPull   0             5m13s
atlas-frontend-58ccd575fd-p4qz8   0/1     ErrImageNeverPull   0             5m13s
grafana-65c58c94b-4bzng           0/1     CrashLoopBackOff    3 (10s ago)   5m28s
mcp-automation-55d98f8b4-66blx    0/1     ErrImageNeverPull   0             5m28s
mcp-automation-55d98f8b4-cvmmj    0/1     ErrImageNeverPull   0             5m13s
mcp-automator-64d697d65c-4tp8m    0/1     ErrImageNeverPull   0             5m13s
mcp-automator-64d697d65c-q6hrg    0/1     ErrImageNeverPull   0             5m28s
mcp-playwright-54449ffd46-24sx2   0/1     ErrImageNeverPull   0             5m28s
mcp-playwright-54449ffd46-kxkx7   0/1     ErrImageNeverPull   0             5m13s
mcp-tts-564bb8978-pbp2r           0/1     ErrImageNeverPull   0             5m13s
mcp-tts-564bb8978-qgpmm           0/1     ErrImageNeverPull   0             5m28s
ollama-755fd45d7b-mtsbm           0/1     ImagePullBackOff    0             5m28s
prometheus-7f499f44c4-r5jx6       0/1     CrashLoopBackOff    3 (9s ago)    5m28s
qdrant-5748f45fd4-zs25t           1/1     Running             0             5m28s
redis-85d6ff84c4-mrtrz            1/1     Running             0             5m27s
redis-exporter-748b84f6df-g65rc   1/1     Running             0             5m27s
```

## Service Tests

- **atlas-core-service:** SUCCESS
- **atlas-frontend-service:** SUCCESS
- **mcp-automation-service:** SUCCESS
- **mcp-automator-service:** SUCCESS
- **mcp-tts-service:** SUCCESS

## Files Generated

- . (1344 bytes)
- .. (2592 bytes)
- atlas-core-6dbf5bf65c-nbc47-describe.txt (3864 bytes)
- atlas-core-6dbf5bf65c-rct6d-describe.txt (3864 bytes)
- atlas-core-logs.txt (131 bytes)
- atlas-core-service-portforward.log (81 bytes)
- atlas-core-service-status.json (491 bytes)
- atlas-core-service-test-result.txt (8 bytes)
- atlas-frontend-58ccd575fd-9t7k6-describe.txt (3146 bytes)
- atlas-frontend-58ccd575fd-bgcbl-describe.txt (3153 bytes)
- atlas-frontend-58ccd575fd-p4qz8-describe.txt (3153 bytes)
- atlas-frontend-logs.txt (139 bytes)
- atlas-frontend-service-portforward.log (81 bytes)
- atlas-frontend-service-status.json (51 bytes)
- atlas-frontend-service-test-result.txt (8 bytes)
- cluster-info.txt (249 bytes)
- deployments.txt (3631 bytes)
- mcp-automation-55d98f8b4-66blx-describe.txt (2934 bytes)
- mcp-automation-55d98f8b4-cvmmj-describe.txt (2941 bytes)
- mcp-automation-logs.txt (138 bytes)
- mcp-automation-service-portforward.log (81 bytes)
- mcp-automation-service-status.json (161 bytes)
- mcp-automation-service-test-result.txt (8 bytes)
- mcp-automator-64d697d65c-4tp8m-describe.txt (2936 bytes)
- mcp-automator-64d697d65c-q6hrg-describe.txt (2929 bytes)
- mcp-automator-logs.txt (137 bytes)
- mcp-automator-service-portforward.log (81 bytes)
- mcp-automator-service-status.json (198 bytes)
- mcp-automator-service-test-result.txt (8 bytes)
- mcp-playwright-54449ffd46-24sx2-describe.txt (2942 bytes)
- mcp-playwright-54449ffd46-kxkx7-describe.txt (2949 bytes)
- mcp-tts-564bb8978-pbp2r-describe.txt (3129 bytes)
- mcp-tts-564bb8978-qgpmm-describe.txt (3129 bytes)
- mcp-tts-service-portforward.log (81 bytes)
- mcp-tts-service-status.json (15 bytes)
- mcp-tts-service-test-result.txt (8 bytes)
- namespace-all.txt (16484 bytes)
- nodes.txt (527 bytes)
- ollama-755fd45d7b-mtsbm-describe.txt (3957 bytes)
- pods.yaml (99426 bytes)
- services.txt (4048 bytes)
- summary.md (4401 bytes)
