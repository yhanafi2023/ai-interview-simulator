PROJECT ?= ai-interview
ENV     ?= dev
PREFIX  := $(PROJECT)-$(ENV)

.PHONY: infra-plan infra-up infra-down infra-cost

infra-plan:
	cd infra && terraform fmt && terraform validate && terraform plan -var image_tag=sha-$(GIT_SHA)

infra-up:
	cd infra && terraform apply -var image_tag=sha-$(GIT_SHA)

infra-down:
	cd infra && terraform destroy -var image_tag=sha-$(GIT_SHA)

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

.PHONY: db-migrate db-seed

# Shared network config for one-off tasks. awsvpc means every task needs
# to be told which subnets and security groups to use.
define RUN_TASK_NET
awsvpcConfiguration={subnets=[$$(cd infra && terraform output -json public_subnet_ids | jq -r 'join(",")')],securityGroups=[$$(cd infra && terraform output -json security_group_ids | jq -r .tasks)],assignPublicIp=ENABLED}
endef

db-migrate:
	@TASK=$$(aws ecs run-task \
	  --cluster $(PREFIX)-cluster \
	  --task-definition $(PREFIX)-migrate \
	  --launch-type FARGATE \
	  --network-configuration "$(RUN_TASK_NET)" \
	  --query 'tasks[0].taskArn' --output text); \
	echo "migration task: $$TASK"; \
	aws ecs wait tasks-stopped --cluster $(PREFIX)-cluster --tasks $$TASK; \
	aws logs tail /ecs/$(PREFIX)-migrate --since 10m; \
	CODE=$$(aws ecs describe-tasks --cluster $(PREFIX)-cluster --tasks $$TASK \
	  --query 'tasks[0].containers[0].exitCode' --output text); \
	echo "exit code: $$CODE"; \
	test "$$CODE" = "0"

db-seed:
	@TASK=$$(aws ecs run-task \
	  --cluster $(PREFIX)-cluster \
	  --task-definition $(PREFIX)-migrate \
	  --launch-type FARGATE \
	  --network-configuration "$(RUN_TASK_NET)" \
	  --overrides '{"containerOverrides":[{"name":"migrate","command":["python","-m","app.seed"]}]}' \
	  --query 'tasks[0].taskArn' --output text); \
	echo "seed task: $$TASK"; \
	aws ecs wait tasks-stopped --cluster $(PREFIX)-cluster --tasks $$TASK; \
	aws logs tail /ecs/$(PREFIX)-migrate --since 10m; \
	CODE=$$(aws ecs describe-tasks --cluster $(PREFIX)-cluster --tasks $$TASK \
	  --query 'tasks[0].containers[0].exitCode' --output text); \
	echo "exit code: $$CODE"; \
	test "$$CODE" = "0"