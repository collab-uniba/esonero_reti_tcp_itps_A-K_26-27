/*
 * protocol.h
 *
 * Application protocol shared by client and server.
 * DO NOT modify the protocol definitions below: the reference client and
 * server used for grading rely on them. You may add constants and prototypes.
 */

#ifndef PROTOCOL_H_
#define PROTOCOL_H_

#include <stdint.h>

// Shared application parameters
#define DEFAULT_SERVER_IP "127.0.0.1"
#define SERVER_PORT 56700          // Default server port
#define QUEUE_SIZE 5               // Size of pending connections queue (server)

#define CODE_LEN 4                 // ISO 4217 currency code: 3 letters + '\0'
#define MAX_AMOUNT 10000000u       // 100000.00 in cents

// Response status codes
#define STATUS_OK 0
#define STATUS_INVALID_CURRENCY 1
#define STATUS_INVALID_AMOUNT 2

// Request message (client -> server), 12 bytes
typedef struct {
    char from[CODE_LEN];   // Source currency code, null-terminated (e.g. "EUR")
    char to[CODE_LEN];     // Target currency code, null-terminated (e.g. "USD")
    uint32_t amount;       // Amount in cents, network byte order
} conversion_request_t;

// Response message (server -> client), 8 bytes
typedef struct {
    uint32_t status;       // STATUS_* code, network byte order
    uint32_t amount;       // Converted amount in cents, network byte order
} conversion_response_t;

// Function prototypes
// Add here the signatures of the functions you implement

#endif /* PROTOCOL_H_ */
