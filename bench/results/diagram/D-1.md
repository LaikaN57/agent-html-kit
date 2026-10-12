# Checkout Platform: Architecture Overview

stats: 12 components | 11 connections | 2 client apps | 1 external provider

This page covers the components of the checkout platform, how they connect, and what happens during a single checkout.

## Components

| Component | Kind | Role |
|---|---|---|
| Web app | Client | Browser client |
| Mobile app | Client | Mobile client |
| API gateway | Service | Entry point for both client apps |
| Checkout service | Service | Runs the checkout flow |
| Cart service | Service | Loads carts and stores them in Redis |
| Fraud service | Service | Returns a fraud score |
| Payment service | Service | Charges the card through Stripe |
| Email service | Service | Sends the receipt |
| Postgres | Database | Orders database |
| Redis | Cache | Cart cache |
| Kafka | Queue | Event bus |
| Stripe | External | Payment provider |

## System diagram

```diagram
title: Checkout platform
Web app [user] -> API gateway [svc]: HTTPS
Mobile app [user] -> API gateway: HTTPS
API gateway -> Checkout service [svc]: gRPC
Checkout service -> Cart service [svc]: gRPC, loads the cart
Cart service -> Redis [cache]: reads and writes carts
Checkout service -> Fraud service [svc]: asks for a fraud score
Checkout service -> Payment service [svc]: charges the card
Payment service -> Stripe [ext]: payment API call
Checkout service -> Postgres [db]: writes the order
Checkout service -> Kafka [queue]: publishes order.created
Kafka -> Email service [svc]: consumes order.created, sends receipt
```

## Walkthrough: one checkout

```steps
Client request | The Web app or Mobile app sends the checkout request to the API gateway over HTTPS.
Route to checkout | The API gateway forwards the request to the Checkout service over gRPC.
Load the cart | The Checkout service calls the Cart service over gRPC. The Cart service reads the cart from Redis.
Fraud check | The Checkout service asks the Fraud service for a fraud score.
Charge the card | The Checkout service asks the Payment service to charge the card. The Payment service calls the Stripe payment API.
Write the order | The Checkout service writes the order to Postgres, but only if the fraud score passed and the charge succeeded.
Publish the event | The Checkout service publishes order.created to Kafka.
Send the receipt | The Email service consumes order.created from Kafka and sends the receipt.
```

> Warning: An order is only written after the fraud score passes and the charge succeeds. If either one fails, nothing is written to Postgres.

> Note: The source data does not give the protocols for the Fraud, Payment, Postgres, and Kafka connections. It also does not say which of the fraud check and the charge runs first, or exactly when order.created is published relative to the order write. Check with the owning teams before relying on any of these details.