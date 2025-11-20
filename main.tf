
terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.170"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}


# Provider configuration
provider "yandex" {
  token     = var.yc_token  # From 'yc config get token'
  cloud_id  = var.cloud_id
  folder_id = var.folder_id
  # No 'zone' here — specify per-resource if needed (e.g., for VMs)
}

# Service Account
resource "yandex_iam_service_account" "bot_sa" {
  name        = "telegram-bot-sa-vvot23"
  description = "Service account for Telegram bot vvot23"
  folder_id   = var.folder_id  # Add this for safety
}

# Roles for Service Account
resource "yandex_resourcemanager_folder_iam_member" "editor" {
  folder_id = var.folder_id
  role      = "editor"
  member    = "serviceAccount:${yandex_iam_service_account.bot_sa.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "storage_editor" {
  folder_id = var.folder_id
  role      = "storage.editor"
  member    = "serviceAccount:${yandex_iam_service_account.bot_sa.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "serverless_functions_invoker" {
  folder_id = var.folder_id
  role      = "serverless.functions.invoker"
  member    = "serviceAccount:${yandex_iam_service_account.bot_sa.id}"
}

# Static Access Key
resource "yandex_iam_service_account_static_access_key" "sa_static_key" {
  service_account_id = yandex_iam_service_account.bot_sa.id
  description        = "Static access key for object storage vvot23"
}

# Object Storage Bucket
resource "yandex_storage_bucket" "instruction_bucket" {
  bucket     = "cheatsheet-instruction-bucket-vvot23"
  access_key = yandex_iam_service_account_static_access_key.sa_static_key.access_key
  secret_key = yandex_iam_service_account_static_access_key.sa_static_key.secret_key
}

# Instruction File in Storage
resource "yandex_storage_object" "instruction" {
  bucket     = yandex_storage_bucket.instruction_bucket.bucket
  key        = "instruction.txt"
  source     = "${path.module}/function/instruction.txt"  # Fixed path to your function folder
  access_key = yandex_iam_service_account_static_access_key.sa_static_key.access_key
  secret_key = yandex_iam_service_account_static_access_key.sa_static_key.secret_key
}

# Zip the function code (REQUIRED — your old code referenced "function.zip" without creating it)
data "archive_file" "function_zip" {
  type        = "zip"
  source_dir  = "${path.module}/function"  # Assumes your Python code is in 'function/' folder
  output_path = "${path.module}/function.zip"
}

resource "yandex_function" "telegram_bot" {
  name               = "telegram-os-bot-vvot23"
  description        = "Telegram bot for OS exam questions vvot23"
  runtime            = "python311"
  entrypoint         = "main.handler"
  memory             = 128
  execution_timeout  = 10
  service_account_id = yandex_iam_service_account.bot_sa.id
  folder_id          = var.folder_id

  # REQUIRED IN PROVIDER v0.171+
  user_hash = filesha256(data.archive_file.function_zip.output_path)

  environment = {
    TG_BOT_TOKEN          = var.tg_bot_key
    YANDEX_CLOUD_CATALOG  = "vvot23"
    BUCKET_NAME           = yandex_storage_bucket.instruction_bucket.bucket
    OBJECT_KEY            = yandex_storage_object.instruction.key
    AWS_ACCESS_KEY_ID     = yandex_iam_service_account_static_access_key.sa_static_key.access_key
    AWS_SECRET_ACCESS_KEY = yandex_iam_service_account_static_access_key.sa_static_key.secret_key
  }

  content {
    zip_filename = data.archive_file.function_zip.output_path
  }
}



# API Gateway
resource "yandex_api_gateway" "telegram_gateway" {
  name     = "telegram-bot-gateway-vvot23"
  folder_id = var.folder_id  # Add for safety

  spec = <<-EOT
    openapi: "3.0.0"
    info:
      version: 1.0.0
      title: Telegram Bot API vvot23
    paths:
      /:
        post:
          x-yc-apigateway-integration:
            type: cloud_functions
            function_id: ${yandex_function.telegram_bot.id}
            service_account_id: ${yandex_iam_service_account.bot_sa.id}
  EOT
}

# Outputs
output "webhook_url" {
  value = "https://${yandex_api_gateway.telegram_gateway.domain}/"
}

output "setup_instructions" {
  value = <<EOT
  ✅ DEPLOYMENT COMPLETE!
  To set up Telegram webhook manually, run:
  curl -X POST "https://api.telegram.org/bot${var.tg_bot_key}/setWebhook?url=https://${yandex_api_gateway.telegram_gateway.domain}/"
  Then test your bot: @cheatsheet_itis_2024_vvot23_bot
  EOT

  sensitive = true
}
