const express = require("express");
const path = require("path");

const port = process.env.PORT || 5006;

const app = express();

app.use(express.json());

app.get("/cpu-intensive", (req, res) => {
  const n = 100_000;
  const primes = primeNumbers(n);
  res.json({ n, primes: primes.length });
});

app.post("/cpu-intensive", (req, res) => {
  // Compute-intensive operation - calculate prime numbers
  // pull a value n from the request body.
  const requestN = parseInt(req.body?.n) || 100_000;
  const n = Math.min(100_000_000, requestN);

  const primes = primeNumbers(n);
  res.json({ n, primes: primes.length });
});

const server = app.listen(port, () => {
  console.log(`Listening on ${port}`);
});

process.on("SIGTERM", async () => {
  console.log("SIGTERM signal received: gracefully shutting down");
  if (server) {
    server.close(() => {
      console.log("HTTP server closed");
    });
  }
});

// Prime number generator
function primeNumbers(n) {
  const primes = [];
  for (let i = 2; i <= n; i++) {
    let isPrime = true;
    for (let j = 2; j < i; j++) {
      if (i % j === 0) {
        isPrime = false;
        break;
      }
    }
    if (isPrime) primes.push(i);
  }

  return primes;
}
