data "aws_cloudfront_cache_policy" "caching_disabled" {
  name = "Managed-CachingDisabled"
}

data "aws_cloudfront_origin_request_policy" "all_viewer_except_host" {
  name = "Managed-AllViewerExceptHostHeader"
}


resource "aws_cloudfront_distribution" "backend" {

  enabled = true

  origin {
    domain_name = aws_instance.backend.public_dns
    origin_id   = "stayops-backend"

    custom_origin_config {
      http_port              = 8000
      https_port             = 443
      origin_protocol_policy = "http-only"

      origin_keepalive_timeout = 5
      origin_read_timeout      = 60

      origin_ssl_protocols = [
        "TLSv1.2"
      ]
    }
  }


  default_cache_behavior {

    target_origin_id = "stayops-backend"

    viewer_protocol_policy = "redirect-to-https"

    allowed_methods = [
      "DELETE",
      "GET",
      "HEAD",
      "OPTIONS",
      "PATCH",
      "POST",
      "PUT"
    ]

    cached_methods = [
      "GET",
      "HEAD",
      "OPTIONS"
    ]

    cache_policy_id = data.aws_cloudfront_cache_policy.caching_disabled.id

    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_viewer_except_host.id

    compress = true
  }


  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }


  viewer_certificate {
    cloudfront_default_certificate = true
  }


  tags = {
    Name = "${var.project_name}-${var.environment}-backend"
  }
}