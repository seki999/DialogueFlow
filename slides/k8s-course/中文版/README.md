# 课程说明

## 课程主题

基于 Kubernetes 官方中文教程页面（https://kubernetes.io/zh-cn/docs/tutorials/）整理的完整课程：从集群基础、部署与配置，到无状态/有状态应用实战、Service 原理、安全加固，再到集群管理进阶话题。

## 总章节数

共 26 组文件（编号 01～26），对应"长"版本课程。

## 文件编号规则

* 每组文件包含同一编号的 `.md` 和 `.conversation` 两个文件
* 编号使用两位数字，连续不跳号
* 例如：`01.md` 对应 `01.conversation`

## 文件对应关系

* `.md` 文件：展示当前章节的知识结构、流程图（Mermaid）和核心要点，用于录制视频画面
* `.conversation` 文件：讲解对应 `.md` 文件内容的双人对话稿，用于自动朗读或录音
* 两个文件内容严格对应，`.conversation` 中不会出现 `.md` 中没有的内容

## 章节列表

1. 为什么要学习 Kubernetes（背景与整体地图）
2. Kubernetes 基础：集群与核心概念
3. 你好 Minikube：创建你的第一个集群
4. 部署应用：使用 kubectl 创建 Deployment
5. 了解你的应用：查看 Pod 和节点
6. 暴露应用：使用 Service
7. 扩缩应用：运行多个实例
8. 更新你的应用：执行滚动更新
9. 配置：使用 ConfigMap 管理配置
10. 实战：使用 ConfigMap 配置 Redis
11. 构造 Pod：使用 Sidecar 容器
12. 无状态应用：公开外部 IP 地址
13. 实战：使用 Redis 部署留言板应用
14. 有状态应用基础：StatefulSet
15. 实战：使用持久卷部署 WordPress 和 MySQL
16. 实战：使用 StatefulSet 部署 Cassandra
17. 实战：运行 ZooKeeper 分布式协调系统
18. Service 深入：使用 Service 连接到应用
19. Service 深入：使用源 IP 与流量保留
20. 安全：在集群级别应用 Pod 安全标准
21. 安全：在名字空间级别应用 Pod 安全标准
22. 安全：使用 AppArmor 限制容器对资源的访问
23. 安全：使用 Seccomp 限制容器的系统调用
24. 集群管理：交换内存与独立模式 kubelet
25. 集群管理：使用 DRA 分配设备
26. 总结与学习路径建议

## 推荐播放顺序

按编号从 01 到 26 依次播放。

## 使用方式

* 播放/录制视频时，按顺序展示每个 `.md` 文件的图形和要点
* 同步朗读对应编号 `.conversation` 文件中的对话内容（speaker 1 为学习者视角，speaker 2 为专家视角）
* 建议每组文件对应一段独立的视频片段或录音片段
