output "api_gateway_domain" {
  value = yandex_api_gateway.telegram_gateway.domain
}

output "function_id" {
  value = yandex_function.telegram_bot.id
}

output "deployment_status" {
  value = "✅ Bot deployed! Set webhook manually and test: @cheatsheet_itis_2024_vvot23_bot"
}