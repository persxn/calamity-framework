---
id: sec-wireless-embedded
title: "Wireless & embedded security"
track: sec
group: cross-cutting
prereqs: [sec-networking]
optional: true
tags: [sec]
weaves_into: [sec]
aliases: [wireless security, wifi, 802.11, embedded, firmware, raspberry pi]
est_hours: 30
order: 30
summary: "Wi-Fi and embedded devices studied by building the target first on your own hardware: 802.11 behaviour, an access point you configure, firmware, and the hardware interfaces underneath."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill. Every experiment is on
a network and devices the learner owns or is explicitly authorised to test.

- Wi-Fi and 802.11 fundamentals
- authentication and association
- beacon, probe and management frames
- WPA2 and WPA3 concepts
- capturing and inspecting wireless traffic you own
- access-point configuration and how it affects security
- rogue access points inside an isolated test network of your own
- client behaviour and the trust assumptions clients make
- firmware analysis and embedded Linux
- UART, SPI, I2C and other hardware interfaces where relevant
- secure boot and firmware integrity

# Boss

On your own hardware (for example a Raspberry Pi), build a test access point, observe and capture its protocol behaviour, and show how two configuration choices change its security. Keep every experiment inside your own isolated test network.

Passes when:

- the access point is built and its management and association frames are captured and read
- two configuration changes are shown to change the security posture, with captured evidence
- the learner explains the trust assumptions a connecting client makes
- all activity stays within the owned, isolated network
