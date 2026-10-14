# PR review: Retry queue for payment webhooks

Webhook calls that fail now go to a retry queue instead of being dropped. The retry limit moves into config (CHK-103).

```diff
title: Changes in this PR
diff --git a/config/payments.yaml b/config/payments.yaml
index 3b18e51..a9c4f02 100644
--- a/config/payments.yaml
+++ b/config/payments.yaml
@@ -4,6 +4,8 @@ webhooks:
   endpoint: https://pay.example.com/hooks
   timeout_ms: 3000
-  retries: 0
+  retries: 5
+  retry_queue: payments-webhook-retry
+  backoff: exponential

 fraud:
   threshold: 0.82
diff --git a/src/webhooks/send.ts b/src/webhooks/send.ts
index 5d2c7e0..c1f9b33 100644
--- a/src/webhooks/send.ts
+++ b/src/webhooks/send.ts
@@ -12,9 +12,12 @@ export async function send(event: Event): Promise<void> {
   const body = JSON.stringify(event);
   try {
     await http.post(cfg.endpoint, body, { timeout: cfg.timeout_ms });
   } catch (err) {
-    log.warn("webhook failed, dropping", err);
-    return;
+    if (event.attempt < cfg.retries) {
+      await queue.push(cfg.retry_queue, { ...event, attempt: event.attempt + 1 });
+      return;
+    }
+    log.error("webhook failed after retries", err);
   }
 }
```

> OK: Duplicate charges in staging dropped to zero over 3 days.
