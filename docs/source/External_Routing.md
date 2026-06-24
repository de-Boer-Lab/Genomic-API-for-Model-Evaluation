# How to set up external routing (port forwarding)

By default, GAME modules communicate over a local network &mdash; both the Predictor (server) and the Evaluator (client) run on the same HPC cluster or local network, and connect directly via IP and port. However, there are cases where you may want to host a Predictor on a separate machine (e.g. your local workstation, a cloud VM, or a different institution's HPC) and allow remote Evaluators to connect to it.

This page provides a brief overview of how to set up port forwarding for these scenarios. Network configurations vary widely across institutions, so treat these as starting points rather than universal instructions.

## When is port forwarding needed?

- You want to host a Predictor with **proprietary model weights** on your own machine, without sharing the weights or the container.
- Your Predictor runs on a **local workstation with a GPU**, but the Evaluator runs on a remote HPC cluster.
- You are connecting modules across **different networks** (e.g. between institutions or between a cloud VM and an HPC).

If both the Predictor and Evaluator are on the same HPC cluster or local network, port forwarding is not needed &mdash; use the IP and port directly as described in [Submitting Jobs](Submitting_jobs.md).

## Coming soon...

TODO: Add more tested info