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