# Rent Payment System – System Design Demo

> **Educational simulation only.**  
> This is **not** production payment code.  
> It does **not** connect to M-Pesa or any real payment provider.

A minimal, in-memory Python demonstration of common system-design patterns used in billing and payment platforms.

**Requirements:** Python 3.10+ (standard library only)

---

## What This Demo Teaches

| Concept              | How it appears in the code                                      |
|----------------------|-----------------------------------------------------------------|
| **Idempotency**      | Duplicate provider callbacks are ignored via unique `provider_transaction_id` |
| **Cache-aside**      | `balance_cache` is checked first; on miss the balance is calculated and stored |
| **Cache invalidation** | Balance cache is cleared when a new payment is recorded       |
| **Message queue**    | Notifications are enqueued and processed asynchronously by a simple worker |
| **Retry handling**   | Simulated transient failure + re-queue of the notification job |
| **Capacity estimation** | Little’s Law used to estimate peak in-flight requests        |

---

## Quick Start

```bash
python rent_payment_demo.py
```
    
## Related Resources          ← put it here

- [Little’s Law](https://en.wikipedia.org/wiki/Little%27s_law)
- [Cache-Aside Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/cache-aside)
- [Idempotency in APIs](https://stripe.com/docs/api/idempotent_requests)
- [Outbox Pattern](https://microservices.io/patterns/data/transactional-outbox.html)
- [Message Queues & At-Least-Once Delivery](https://www.cloudamqp.com/blog/part1-rabbitmq-for-beginners-what-is-rabbitmq.html)

## License
MIT – free to use for learning and teaching.