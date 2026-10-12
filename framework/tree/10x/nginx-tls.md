---
id: nginx-tls
title: "Nginx, reverse proxies & TLS"
track: 10x
group: devops
prereqs: [networking, linux-shell]
aliases: [nginx, reverse proxy, https, lets encrypt, load balancer]
est_hours: 12
order: 60
summary: "Put a server on the internet correctly: reverse proxying, static files, TLS certificates, limits, logs."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- server blocks; serving static files
- reverse proxying and load balancing
- TLS with Let's Encrypt; HTTP/2
- compression and caching headers
- rate limiting; access and error logs

# Boss

Put a service behind Nginx with a real certificate.

Passes when:

- an SSL Labs style check grades it A
- HTTP redirects to HTTPS
- a burst of requests is rate limited
