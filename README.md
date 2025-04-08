# 🕷️ Welcome to the wiki of Broken Links Crawler (BLC)

---

## 🔍 Project Overview

BLC (Broken Links Crawler) is a Python-based command-line tool developed as part of academic work.

The tool is built to scan websites and detect broken or problematic hyperlinks, addressing practical needs while showcasing key concepts in modern software development — including multithreading, modular design, automation, and robust error handling.

---

## ⚡ What BLC Offers

Although developed in an academic setting, BLC is a fully functional and production-aware tool. It’s designed to be performant, configurable, and extensible — suitable for use by developers, sysadmins, QA engineers, and anyone responsible for maintaining link integrity across digital content.

---

## ✅ Key Features

- 🚀 **High-performance, multi-threaded crawling**  
  Utilizes a producer-consumer pattern to efficiently scan sites in parallel.

- 🛑 **Detection of common link issues**:
  - `404 Not Found`
  - DNS resolution errors
  - HTTP to HTTPS mismatches
  - "False 200 OK" responses (e.g., custom error pages)

- 🌐 **External link validation**  
  Ensures referenced external links are reachable, without full recursion.

- 🎛️ **Flexible configuration**:
  - Crawl depth control
  - Adjustable thread count
  - Output in `JSON`, `HTML`, or human-readable formats

- 📬 **Email-based reporting**  
  Automatically sends results based on customizable triggers:
  - Always
  - Only on error
  - Never

- 🖥️ **Cross-platform support**
  - Built for Linux (Ubuntu) and Windows
  - Can be packaged into a standalone executable (`blc`, `blc.exe`)

- 🔓 **Open-source & automation-ready**
  - Easily integrated into CI/CD pipelines, scheduled audits, or link monitoring tools

---

## 🎓 Key Concepts and Engineering Guidelines

This project demonstrates:

- Clean and modular code structure
- Effective use of concurrency and thread-safe data structures
- Real-world exception handling and resilience
- Compliance with web standards (`robots.txt`, SSL, email protocols)
- Practical usage of third-party libraries (e.g., `requests`, `certifi`, `PyInstaller`)

BLC serves as a platform to reinforce core software engineering principles while delivering a system with practical, real-world utility.

---

## 📁 Get Started

Visit the [🚀 Command-Line Usage](./🚀-Command‐Line-Usage) page to learn how to configure, run, and customize BLC.

Explore the sections - [📊 Initial Software Requirements](./Software-Requirements), [📐 High-Level Design](./High‐Level-Design) to explore the project's origin and architecture.

Check out [🛠️ Implementation Notes](./🛠%EF%B8%8F-Implementation-Notes) for insights into the tools, technologies, and key implementation decisions.

Crawling the web isn’t easy — check out [🐞 Progress and Improvements](./🐞-Crawler-URL-Fetching-Issues-–-Progress-and-Improvements) and [🛠️ The Challenges](./🛠️-Crawler-URL-Fetching-Issues-‐-The-Challenges) to see what was done and achieved.

A discussion on thread number optimization can be found on [🚀 Performance Tuning: Thread Count](./🚀-Performance-Tuning:-Thread-Count).

---

## 🧑‍💻 Contribute & Explore

Feel free to explore or extend the project further. You can find the full source code, issue tracker, and documentation in the [GitHub repository](https://github.com/yohayonyon/blc).

---

Thank you for visiting — and here’s to chasing broken links, and finishing what we started. 🎓✨
