# Course Notes

## Course Topic

A complete course organized from the official Kubernetes Chinese tutorials page (https://kubernetes.io/zh-cn/docs/tutorials/): from cluster basics, deployment, and configuration, through hands-on stateless/stateful application cases, Service internals, and security hardening, to advanced cluster management topics.

## Total Chapters

26 file groups in total (numbered 01–26), corresponding to the "long" version of the course.

## File Numbering Rules

* Each group contains a matching pair: `.md` and `.conversation`, with the same number
* Numbers use two digits and run consecutively with no gaps
* Example: `01.md` pairs with `01.conversation`

## File Relationship

* `.md` file: shows the chapter's knowledge structure, a flow diagram (Mermaid), and key points — for the video's visuals
* `.conversation` file: a two-speaker dialogue script explaining the corresponding `.md` file's content — for narration or recording
* The two files correspond strictly; the `.conversation` file never contains content absent from the `.md` file

## Chapter List

1. Why Learn Kubernetes (Background and the Big Picture)
2. Kubernetes Basics: Clusters and Core Concepts
3. Hello Minikube: Creating Your First Cluster
4. Deploying an App: Creating a Deployment with kubectl
5. Exploring Your App: Viewing Pods and Nodes
6. Exposing an App: Using a Service
7. Scaling Your App: Running Multiple Instances
8. Updating Your App: Performing a Rolling Update
9. Configuration: Managing Config with ConfigMaps
10. Hands-On: Configuring Redis Using a ConfigMap
11. Authoring Pods: Using Sidecar Containers
12. Stateless Applications: Exposing an External IP Address
13. Hands-On: Deploying a Guestbook App with Redis
14. Stateful Application Basics: StatefulSet
15. Hands-On: Deploying WordPress and MySQL with Persistent Volumes
16. Hands-On: Deploying Cassandra with a StatefulSet
17. Hands-On: Running ZooKeeper, a Distributed Coordination System
18. Services in Depth: Connecting Applications with Services
19. Services in Depth: Using Source IP and Traffic Preservation
20. Security: Applying Pod Security Standards at the Cluster Level
21. Security: Applying Pod Security Standards at the Namespace Level
22. Security: Restricting a Container's Access to Resources with AppArmor
23. Security: Restricting a Container's System Calls with Seccomp
24. Cluster Management: Swap Memory and Standalone kubelet
25. Cluster Management: Allocating Devices with DRA
26. Summary and Suggested Learning Path

## Recommended Playback Order

Play in numerical order from 01 through 26.

## How to Use

* When recording or playing a video, display the diagram and key points from each `.md` file in order
* Narrate the matching `.conversation` file's dialogue at the same time (speaker 1 represents the learner's perspective, speaker 2 represents the expert's perspective)
* It's recommended to treat each file pair as an independent video or audio segment
