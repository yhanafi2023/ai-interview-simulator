locals {
  # Every resource gets this prefix, so a console list is instantly readable
  # and so two environments can coexist in one account without colliding.
  name_prefix = "${var.project}-${var.environment}"
}