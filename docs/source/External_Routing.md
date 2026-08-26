# Setting up external routing (port forwarding)

By default, GAME modules communicate over a local network &mdash; both the Predictor (server) and the Evaluator (client) run on the same HPC cluster or local network, and connect directly via IP and port. However, there are cases where you may want to host a Predictor on a separate machine (e.g. your local workstation, a cloud VM, or a different institution's HPC) and allow remote Evaluators to connect to it.

This page points to general resources on port forwarding for these scenarios. Network configurations vary widely across institutions, so treat these as starting points only.

## When is port forwarding needed?

- You want to host a Predictor with **proprietary model weights** on your own machine, without sharing the weights or the container.
- Your Predictor runs on a **local workstation with a GPU**, but the Evaluator runs on a remote HPC cluster.
- You are connecting modules across **different networks** (e.g. between institutions or between a cloud VM and an HPC).

If both the Predictor and Evaluator are on the same HPC cluster or local network, port forwarding is not needed &mdash; use the IP and port directly as described in [Submitting Jobs](Submitting_jobs.md).

## Useful resources

Router and network configurations differ by device, ISP, and institution &mdash; always check your device manufacturer's documentation and your institution's network/IT policies first, as these take precedence over any general guide below. Some institutional networks (e.g. many HPC clusters) restrict or prohibit inbound port forwarding entirely, so confirm with your network administrator before proceeding.

**General guides:**

- [Wikipedia: Port forwarding](https://en.wikipedia.org/wiki/Port_forwarding)
- [No-IP: General Port Forwarding Guide](https://www.noip.com/support/knowledgebase/general-port-forwarding-guide)
- [r/HomeNetworking: A Guide to Port Forwarding](https://www.reddit.com/r/HomeNetworking/comments/i7ijiz/a_guide_to_port_forwarding/)
