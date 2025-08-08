# 🚀 Flask App with MariaDB and phpMyAdmin on Kubernetes

This project deploys a Flask web application connected to a MariaDB database, with phpMyAdmin for database management — all containerized with Docker and orchestrated using Kubernetes via Minikube.

phpMyAdmin: http://<minikube-ip>:30081
MariaDB: Used internally, exposed only in-cluster

🔍 Debug & Testing
-Check all resources:
kubectl get all

-Logs for Flask app:
kubectl logs deployment/webserver

-Curl test:
curl http://webserver.local

📌 Future Improvements:
- Use Gunicorn for Flask in production
- Add PersistentVolume for database data
- Set up TLS with self-signed certs for HTTPS access
