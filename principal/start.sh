#!/bin/bash
docker build -t htb-principal . && docker run -d --name principal -p 8080:8080 -p 2222:22 htb-principal
