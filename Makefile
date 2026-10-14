.PHONY: infra-plan infra-up infra-down infra-cost

infra-plan:
	cd infra && terraform fmt && terraform validate && terraform plan

infra-up:
	cd infra && terraform apply

infra-down:
	cd infra && terraform destroy

infra-cost:
	@aws ce get-cost-and-usage \
		--time-period Start=$$(date -u -d '7 days ago' +%Y-%m-%d),End=$$(date -u -d tomorrow +%Y-%m-%d) \
		--granularity DAILY --metrics UnblendedCost \
		--query 'ResultsByTime[].{Date:TimePeriod.Start,Cost:Total.UnblendedCost.Amount}' \
		--output table

AWS_REGION ?= us-east-1
GIT_SHA    := $(shell git rev-parse --short HEAD)

.PHONY: ecr-login image-push

ecr-login:
	@aws ecr get-login-password --region $(AWS_REGION) \
	 | docker login --username AWS --password-stdin \
	   $$(cd infra && terraform output -raw ecr_repository_url | cut -d/ -f1)

image-push: ecr-login
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "ERROR: working tree is dirty. Commit before building."; exit 1; \
	fi
	@REPO=$$(cd infra && terraform output -raw ecr_repository_url); \
	docker build --platform linux/amd64 -t $$REPO:sha-$(GIT_SHA) ./backend && \
	docker image inspect $$REPO:sha-$(GIT_SHA) --format 'arch: {{.Architecture}}' && \
	docker push $$REPO:sha-$(GIT_SHA) && \
	echo "pushed sha-$(GIT_SHA)"