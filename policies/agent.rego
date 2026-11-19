package agent.authz

default allow = false

allow {
  input.identity_valid == true
  input.registered == true
  input.lifecycle == "active"
  input.action == "records:read"
  input.resource == "synthetic-customer-records"
}
